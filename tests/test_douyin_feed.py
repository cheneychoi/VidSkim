import json
import time

import httpx
import pytest
from test_douyin import CANONICAL, MEDIA_URL, PAGE_URL, VIDEO_ID, page
from test_douyin import video_bytes as video_bytes

from watch2note import douyin
from watch2note.errors import Watch2NoteError

PRIMARY_HOST = "api5-normal-c-hl.amemv.com"
BACKUP_HOST = "aweme.snssdk.com"


def item(video_id=VIDEO_ID, title="Feed 作品描述", status=None):
    return {
        "aweme_id": video_id,
        "desc": title,
        "status": status or {},
        "video": {"play_addr": {"url_list": [MEDIA_URL]}},
    }


def install_client(monkeypatch, handler):
    monkeypatch.setattr(
        douyin,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )


def test_feed_skips_unrelated_first_item_and_matches_target():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.url.params["aweme_id"] == VIDEO_ID
        assert request.url.params["aid"] == "1128"
        return httpx.Response(
            200,
            json={
                "status_code": 0,
                "aweme_list": [item("999", status={"private_status": 1}), item()],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = douyin._read_feed(client, VIDEO_ID, time.monotonic() + 60)
    assert result == ([MEDIA_URL], "Feed 作品描述")
    assert [request.url.host for request in seen] == [PRIMARY_HOST]


def test_both_feed_nodes_without_match_fall_back_to_ssr(tmp_path, monkeypatch, video_bytes):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        if request.url.path == "/aweme/v1/feed/":
            return httpx.Response(200, json={"status_code": 0, "aweme_list": [item("999")]})
        if str(request.url) == PAGE_URL:
            return httpx.Response(200, text=page(title="SSR 作品描述"))
        assert str(request.url) == MEDIA_URL
        return httpx.Response(200, content=video_bytes, headers={"content-type": "video/mp4"})

    install_client(monkeypatch, handler)
    path, title = douyin.download_video(CANONICAL, tmp_path)
    assert path.read_bytes() == video_bytes
    assert title == "SSR 作品描述"
    assert seen == [PRIMARY_HOST, BACKUP_HOST, "www.iesdouyin.com", "v3-dy.zjcdn.com"]


@pytest.mark.parametrize("failure", ["http", "json", "status", "redirect"])
def test_primary_failure_uses_matching_backup(failure):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        if request.url.host == PRIMARY_HOST:
            if failure == "http":
                return httpx.Response(403)
            if failure == "json":
                return httpx.Response(200, text="{broken JSON")
            if failure == "status":
                return httpx.Response(200, json={"status_code": 1, "aweme_list": [item()]})
            return httpx.Response(302, headers={"location": "https://evil.test/feed"})
        assert request.url.host == BACKUP_HOST
        return httpx.Response(200, json={"status_code": 0, "aweme_list": [item()]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = douyin._read_feed(client, VIDEO_ID, time.monotonic() + 60)
    assert result == ([MEDIA_URL], "Feed 作品描述")
    assert seen == [PRIMARY_HOST, BACKUP_HOST]


@pytest.mark.parametrize(
    "data",
    [
        [],
        {"status_code": 0},
        {"status_code": 0, "aweme_list": "invalid list"},
        {"status_code": 0, "aweme_list": [None, {"video": {}}]},
    ],
)
def test_invalid_or_missing_feed_items_do_not_become_requested_video(data):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        return httpx.Response(200, json=data)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert douyin._read_feed(client, VIDEO_ID, time.monotonic() + 60) is None
    assert seen == [PRIMARY_HOST, BACKUP_HOST]


@pytest.mark.parametrize(
    "status", [{"private_status": 1}, {"is_delete": True}, {"allow_share": False}]
)
def test_matching_restricted_item_is_rejected_without_ssr_fallback(tmp_path, monkeypatch, status):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        assert request.url.host == PRIMARY_HOST, "匹配私密作品后不能请求备用、SSR 或媒体"
        return httpx.Response(200, json={"status_code": 0, "aweme_list": [item(status=status)]})

    install_client(monkeypatch, handler)
    with pytest.raises(Watch2NoteError, match="权限受限"):
        douyin.download_video(CANONICAL, tmp_path)
    assert seen == [PRIMARY_HOST]
    assert not list(tmp_path.iterdir())


def test_feed_download_decodes_real_small_media_and_reuses_cache(
    tmp_path, monkeypatch, video_bytes
):
    seen = []

    def handler(request):
        seen.append(request.url.host)
        if request.url.host == PRIMARY_HOST:
            return httpx.Response(200, json={"status_code": 0, "aweme_list": [item()]})
        assert str(request.url) == MEDIA_URL, "Feed 成功时不能继续请求 SSR"
        return httpx.Response(200, content=video_bytes, headers={"content-type": "video/mp4"})

    install_client(monkeypatch, handler)
    path, title = douyin.download_video(CANONICAL, tmp_path)
    assert path == tmp_path / f"{VIDEO_ID}.mp4"
    assert path.read_bytes() == video_bytes
    assert title == "Feed 作品描述"
    metadata = json.loads((tmp_path / f"{VIDEO_ID}.json").read_text(encoding="utf-8"))
    assert metadata == {"source": CANONICAL, "title": title}
    assert seen == [PRIMARY_HOST, "v3-dy.zjcdn.com"]
    assert not list(tmp_path.glob("*.part"))

    monkeypatch.setattr(douyin, "_client", lambda: pytest.fail("有效缓存不应发网络请求"))
    assert douyin.download_video(CANONICAL, tmp_path) == (path, title)


@pytest.mark.parametrize(
    "location",
    [
        "https://evil.test/feed",
        "http://127.0.0.1/private",
        "https://api5-normal-c-hl.amemv.com.evil.test/feed",
        "https://api2.amemv.com/feed",
    ],
)
def test_api_redirect_stops_before_requesting_untrusted_domain(location):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(302, headers={"location": location})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(Watch2NoteError, match="域名"):
            with douyin._response(client, douyin._FEED_ENDPOINTS[0], api=True):
                pytest.fail("恶意 API 跳转不能产生响应")
    assert seen == [douyin._FEED_ENDPOINTS[0]]
