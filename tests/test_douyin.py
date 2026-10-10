import json
from pathlib import Path

import av
import httpx
import pytest

from vidskim import douyin
from vidskim.errors import VidSkimError

VIDEO_ID = "7611489793444171048"
CANONICAL = f"https://www.douyin.com/video/{VIDEO_ID}"
PAGE_URL = f"https://www.iesdouyin.com/share/video/{VIDEO_ID}"
MEDIA_URL = "https://v3-dy.zjcdn.com/video.mp4"


def page(*, urls=None, title="真实作品描述 } ; 这不是逐字稿", status_code=0, item_status=None):
    item = {
        "aweme_id": VIDEO_ID,
        "desc": title,
        "status": item_status or {},
        "video": {"play_addr": {"url_list": urls if urls is not None else [MEDIA_URL]}},
    }
    data = {
        "loaderData": {
            "video_(id)/page": {"videoInfoRes": {"status_code": status_code, "item_list": [item]}}
        }
    }
    return "<script>\nwindow._ROUTER_DATA =\n" + json.dumps(data, indent=2) + ";\nother();</script>"


def mock_client(monkeypatch, handler):
    def with_unavailable_feed(request):
        if request.url.path == "/aweme/v1/feed/":
            return httpx.Response(200, json={"status_code": 0, "aweme_list": []})
        return handler(request)

    monkeypatch.setattr(
        douyin,
        "_client",
        lambda: httpx.Client(
            transport=httpx.MockTransport(with_unavailable_feed), follow_redirects=False
        ),
    )


@pytest.fixture(scope="module")
def video_bytes(tmp_path_factory):
    target = tmp_path_factory.mktemp("media") / "sample.mp4"
    with av.open(str(target), "w") as container:
        video = container.add_stream("mpeg4", rate=1)
        video.width = video.height = 16
        video.pix_fmt = "yuv420p"
        audio = container.add_stream("aac", rate=16000)
        audio.layout = "mono"
        frame = av.VideoFrame(16, 16, "yuv420p")
        for plane in frame.planes:
            plane.update(b"\x00" * plane.buffer_size)
        for packet in video.encode(frame):
            container.mux(packet)
        for packet in video.encode(None):
            container.mux(packet)
        sound = av.AudioFrame(format="fltp", layout="mono", samples=1024)
        sound.sample_rate = 16000
        for plane in sound.planes:
            plane.update(b"\x00" * plane.buffer_size)
        for packet in audio.encode(sound):
            container.mux(packet)
        for packet in audio.encode(None):
            container.mux(packet)
    return target.read_bytes()


@pytest.mark.parametrize(
    "value",
    [
        CANONICAL,
        f"https://douyin.com/video/{VIDEO_ID}/?foo=1",
        f"https://www.iesdouyin.com/share/video/{VIDEO_ID}/",
        f"https://www.douyin.com/share/video/{VIDEO_ID}",
        f"https://www.douyin.com/jingxuan?modal_id={VIDEO_ID}",
        f"7.32 复制打开抖音，看看这个 {CANONICAL}。复制链接",
    ],
)
def test_resolves_supported_inputs_without_network(value, monkeypatch):
    monkeypatch.setattr(douyin, "_client", lambda: pytest.fail("直接视频地址无需网络"))
    assert douyin.resolve_input(value) == CANONICAL


@pytest.mark.parametrize(
    "value",
    [
        f"https://www.douyin.com.evil.test/video/{VIDEO_ID}",
        f"https://evil.douyin.com/video/{VIDEO_ID}",
        f"https://www.douyin.com@evil.test/video/{VIDEO_ID}",
        f"https://user:secret@www.douyin.com/video/{VIDEO_ID}",
        f"https://www.douyin.com:8443/video/{VIDEO_ID}",
        f"https://127.0.0.1/video/{VIDEO_ID}",
        f"https://www.douyin.com/video/{VIDEO_ID}?modal_id=123",
        "https://www.douyin.com/jingxuan?modal_id=123&modal_id=456",
        "https://www.douyin.com/jingxuan?modal_id=abc",
        f"https://www.douyin.com/note/{VIDEO_ID}",
        "没有链接",
    ],
)
def test_rejects_invalid_or_untrusted_inputs_before_network(value, monkeypatch):
    monkeypatch.setattr(douyin, "_client", lambda: pytest.fail("无效输入不能发请求"))
    with pytest.raises(VidSkimError):
        douyin.resolve_input(value)


def test_short_link_validates_relative_redirects(monkeypatch):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/first/":
            return httpx.Response(302, headers={"location": "/second/"})
        if request.url.path == "/second/":
            return httpx.Response(302, headers={"location": CANONICAL})
        return httpx.Response(200, text="视频页面")

    mock_client(monkeypatch, handler)
    assert douyin.resolve_input("复制这个 https://v.douyin.com/first/") == CANONICAL
    assert seen == ["https://v.douyin.com/first/", "https://v.douyin.com/second/", CANONICAL]


@pytest.mark.parametrize(
    "location", ["https://evil.test/video/123", "http://127.0.0.1/", "//douyin.com.evil.test/"]
)
def test_short_link_stops_before_untrusted_redirect(monkeypatch, location):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(302, headers={"location": location})

    mock_client(monkeypatch, handler)
    with pytest.raises(VidSkimError, match="域名"):
        douyin.resolve_input("https://v.douyin.com/abc/")
    assert len(seen) == 1


def test_redirect_loop_is_bounded(monkeypatch):
    seen = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(302, headers={"location": "/loop/"})

    mock_client(monkeypatch, handler)
    with pytest.raises(VidSkimError, match="跳转次数"):
        douyin.resolve_input("https://v.douyin.com/loop/")
    assert len(seen) == douyin._MAX_REDIRECTS + 1


def test_multiline_router_json_and_semicolon_are_parsed():
    urls, title = douyin._parse_page(page(), VIDEO_ID)
    assert urls == [MEDIA_URL]
    assert title == "真实作品描述 } ; 这不是逐字稿"


@pytest.mark.parametrize(
    ("html", "message"),
    [
        ("<html>验证你的身份</html>", "没有视频数据"),
        (page(status_code=1), "失败状态"),
        (page(item_status={"is_delete": True}), "权限受限"),
        (page(item_status={"private_status": 1}), "权限受限"),
        (page(item_status={"allow_share": False}), "权限受限"),
        (page(urls=[]), "没有可下载"),
        (
            '<script>window._ROUTER_DATA={"unrelated":{"item_list":[{}]}};</script>',
            "数据结构",
        ),
        (
            '<script>window._ROUTER_DATA={"loaderData":{"video_(id)/page":'
            '{"videoInfoRes":{"status_code":0,"item_list":[]}}}};</script>',
            "未取得真实视频",
        ),
    ],
)
def test_page_failures_are_explicit(html, message):
    with pytest.raises(VidSkimError, match=message):
        douyin._parse_page(html, VIDEO_ID)


def test_download_decodes_and_caches_real_video(tmp_path, monkeypatch, video_bytes):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page())
        assert str(request.url) == MEDIA_URL
        return httpx.Response(200, content=video_bytes, headers={"content-type": "video/mp4"})

    mock_client(monkeypatch, handler)
    result, title = douyin.download_video(CANONICAL, tmp_path)
    assert result == tmp_path / f"{VIDEO_ID}.mp4"
    assert result.read_bytes() == video_bytes
    assert title == "真实作品描述 } ; 这不是逐字稿"
    metadata = json.loads((tmp_path / f"{VIDEO_ID}.json").read_text(encoding="utf-8"))
    assert metadata == {"source": CANONICAL, "title": title}
    assert seen == [PAGE_URL, MEDIA_URL]
    monkeypatch.setattr(douyin, "_client", lambda: pytest.fail("有效缓存不应重复请求"))
    assert douyin.download_video(CANONICAL, tmp_path) == (result, title)
    assert not list(tmp_path.glob("*.part"))


def test_media_network_failure_retries_only_twice(tmp_path, monkeypatch, video_bytes):
    attempts = 0

    def handler(request):
        nonlocal attempts
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page())
        attempts += 1
        if attempts == 1:
            return httpx.Response(502)
        return httpx.Response(200, content=video_bytes)

    mock_client(monkeypatch, handler)
    assert douyin.download_video(CANONICAL, tmp_path)[0].is_file()
    assert attempts == 2


def test_html_200_moves_to_next_candidate(tmp_path, monkeypatch, video_bytes):
    good = "https://v3-dy.zjcdn.com/good.mp4"
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page(urls=[MEDIA_URL, good]))
        if str(request.url) == MEDIA_URL:
            return httpx.Response(200, text="<html>风控页面</html>")
        return httpx.Response(200, content=video_bytes)

    mock_client(monkeypatch, handler)
    assert douyin.download_video(CANONICAL, tmp_path)[0].is_file()
    assert seen == [PAGE_URL, MEDIA_URL, MEDIA_URL, good]


@pytest.mark.parametrize("body", [b"<html>HTTP 200 is not a video</html>", b"broken media", b""])
def test_invalid_media_is_not_promoted_to_cache(tmp_path, monkeypatch, body):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page())
        return httpx.Response(200, content=body, headers={"content-type": "video/mp4"})

    mock_client(monkeypatch, handler)
    with pytest.raises(VidSkimError, match="下载失败"):
        douyin.download_video(CANONICAL, tmp_path)
    assert seen == [PAGE_URL, MEDIA_URL, MEDIA_URL]
    assert not list(tmp_path.iterdir())


def test_missing_audio_is_rejected(tmp_path):
    target = tmp_path / "silent.mp4"
    with av.open(str(target), "w") as container:
        video = container.add_stream("mpeg4", rate=1)
        video.width = video.height = 16
        video.pix_fmt = "yuv420p"
        frame = av.VideoFrame(16, 16, "yuv420p")
        for plane in frame.planes:
            plane.update(b"\x00" * plane.buffer_size)
        for packet in video.encode(frame):
            container.mux(packet)
        for packet in video.encode(None):
            container.mux(packet)
    with pytest.raises(VidSkimError, match="缺少视频或音轨"):
        douyin._validate_media(target)


def test_size_limit_applies_without_content_length(tmp_path, monkeypatch):
    monkeypatch.setattr(douyin, "_MAX_MEDIA_BYTES", 10)

    def handler(request):
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page())
        return httpx.Response(200, stream=httpx.ByteStream(b"x" * 11))

    mock_client(monkeypatch, handler)
    with pytest.raises(VidSkimError, match="下载上限"):
        douyin.download_video(CANONICAL, tmp_path)
    assert not list(tmp_path.iterdir())


def test_media_redirect_also_checks_domain(tmp_path, monkeypatch):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page())
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})

    mock_client(monkeypatch, handler)
    with pytest.raises(VidSkimError, match="域名"):
        douyin.download_video(CANONICAL, tmp_path)
    assert seen == [PAGE_URL, MEDIA_URL, MEDIA_URL]
    assert not list(tmp_path.iterdir())


def test_cached_invalid_media_is_downloaded_again(tmp_path, monkeypatch, video_bytes):
    (tmp_path / f"{VIDEO_ID}.mp4").write_bytes(b"not a media file")
    (tmp_path / f"{VIDEO_ID}.json").write_text(
        json.dumps({"source": CANONICAL, "title": "旧描述"}), encoding="utf-8"
    )

    def handler(request):
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page(title="新描述"))
        return httpx.Response(200, content=video_bytes)

    mock_client(monkeypatch, handler)
    target, title = douyin.download_video(CANONICAL, tmp_path)
    assert target.read_bytes() == video_bytes
    assert title == "新描述"


def test_download_requires_canonical_input(tmp_path):
    with pytest.raises(VidSkimError, match="规范"):
        douyin.download_video(f"https://www.douyin.com/video/{VIDEO_ID}/", Path(tmp_path))
