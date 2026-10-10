"""解析抖音公开分享链接，下载并验证真实音视频。"""

import json
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import av
import httpx

from .errors import VidSkimError

_PAGE_HOSTS = {
    "douyin.com",
    "www.douyin.com",
    "m.douyin.com",
    "v.douyin.com",
    "jingxuan.douyin.com",
    "iesdouyin.com",
    "www.iesdouyin.com",
}
_FEED_ENDPOINTS = (
    "https://api5-normal-c-hl.amemv.com/aweme/v1/feed/",
    "https://aweme.snssdk.com/aweme/v1/feed/",
)
_MEDIA_DOMAINS = (
    "douyinvod.com",
    "bytecdn.cn",
    "byteimg.com",
    "snssdk.com",
    "amemv.com",
    "zjcdn.com",
    "ibytedtos.com",
    "volcvod.com",
    "bdxiguavod.com",
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    ),
    "Referer": "https://www.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
_MAX_REDIRECTS = 5
_MAX_PAGE_BYTES = 5 * 1024 * 1024
_MAX_MEDIA_BYTES = 512 * 1024 * 1024
_DOWNLOAD_SECONDS = 180
_ATTEMPTS = 2
_URL_PATTERN = re.compile(r"https?://[^\s<>\"'，。；！？、）]+", re.IGNORECASE)
_ID_PATTERN = re.compile(r"[0-9]{1,32}\Z")


def _client() -> httpx.Client:
    return httpx.Client(
        headers=_HEADERS,
        timeout=httpx.Timeout(15, connect=10),
        follow_redirects=False,
    )


def _validate_url(url: str, *, media: bool = False, api: bool = False) -> str:
    try:
        parts = urlsplit(url)
        port = parts.port
        host = parts.hostname or ""
    except ValueError as exc:
        raise VidSkimError("链接格式无效。") from exc
    if (
        parts.scheme not in {"http", "https"}
        or parts.username is not None
        or parts.password is not None
        or port not in {None, 80 if parts.scheme == "http" else 443}
    ):
        raise VidSkimError("只支持不含账号信息的 HTTP / HTTPS 抖音链接。")
    allowed = host in _PAGE_HOSTS
    if api:
        allowed = host in {urlsplit(endpoint).hostname for endpoint in _FEED_ENDPOINTS}
    if media:
        allowed = allowed or any(
            host == domain or host.endswith("." + domain) for domain in _MEDIA_DOMAINS
        )
    if not allowed:
        raise VidSkimError("链接域名不在抖音支持范围内。")
    return url


def _video_id(url: str) -> str | None:
    parts = urlsplit(url)
    path_match = re.fullmatch(r"/(?:share/)?video/([0-9]{1,32})/?", parts.path)
    ids = parse_qs(parts.query).get("modal_id", [])
    if ids and (len(ids) != 1 or not _ID_PATTERN.fullmatch(ids[0])):
        raise VidSkimError("modal_id 必须是一个数字视频 ID。")
    path_id = path_match.group(1) if path_match else None
    if path_id and ids and path_id != ids[0]:
        raise VidSkimError("链接中的视频 ID 不一致。")
    if parts.path.startswith(("/note/", "/slides/", "/share/note/", "/share/slides/")):
        raise VidSkimError("首版只支持普通视频，暂不支持图文作品。")
    return path_id or (ids[0] if ids else None)


@contextmanager
def _response(
    client: httpx.Client,
    url: str,
    *,
    media: bool = False,
    api: bool = False,
    headers: dict | None = None,
):
    current = _validate_url(url, media=media, api=api)
    for hop in range(_MAX_REDIRECTS + 1):
        with client.stream("GET", current, headers=headers) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise VidSkimError("抖音返回了缺少目标地址的跳转。")
                if hop == _MAX_REDIRECTS:
                    raise VidSkimError("抖音链接跳转次数过多。")
                current = _validate_url(urljoin(current, location), media=media, api=api)
                continue
            response.raise_for_status()
            yield response
            return


def resolve_input(value: str) -> str:
    """支持分享文本、短链和视频页；每次跳转均验证域名。"""
    match = _URL_PATTERN.search(value.strip())
    if not match:
        raise VidSkimError("请提供抖音视频链接或包含链接的分享文本。")
    url = _validate_url(match.group().rstrip(".,;!?)］]}"))
    video_id = _video_id(url)
    if video_id:
        return f"https://www.douyin.com/video/{video_id}"
    if urlsplit(url).hostname != "v.douyin.com":
        raise VidSkimError("链接中没有找到视频 ID。")
    try:
        with _client() as client, _response(client, url) as response:
            video_id = _video_id(str(response.url))
    except httpx.HTTPStatusError as exc:
        raise VidSkimError(f"抖音短链请求失败（HTTP {exc.response.status_code}）。") from exc
    except httpx.HTTPError as exc:
        raise VidSkimError("抖音短链网络请求失败，请稍后重试。") from exc
    if not video_id:
        raise VidSkimError("短链未返回普通视频地址，可能已失效或需要登录。")
    return f"https://www.douyin.com/video/{video_id}"


def _read_page(client: httpx.Client, video_id: str, deadline: float) -> str:
    with _response(client, f"https://www.iesdouyin.com/share/video/{video_id}") as response:
        body = bytearray()
        for chunk in response.iter_bytes(chunk_size=65536):
            if time.monotonic() > deadline:
                raise VidSkimError("抖音下载已超过时间上限，请稍后重试。")
            body.extend(chunk)
            if len(body) > _MAX_PAGE_BYTES:
                raise VidSkimError("抖音分享页异常，页面大小超过上限。")
        return body.decode("utf-8", errors="replace")


def _parse_page(page: str, video_id: str) -> tuple[list[str], str]:
    marker = re.search(r"window\s*\.\s*_ROUTER_DATA\s*=\s*", page)
    if not marker:
        raise VidSkimError("分享页没有视频数据，可能触发风控、需要登录或作品已失效。")
    try:
        data, _ = json.JSONDecoder().raw_decode(page[marker.end() :])
        result = data["loaderData"]["video_(id)/page"]["videoInfoRes"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise VidSkimError("抖音分享页数据结构无法解析，平台结构可能已变化。") from exc
    if not isinstance(result, dict):
        raise VidSkimError("抖音返回的视频详情格式异常。")
    if result.get("status_code", 0) not in (0, "0"):
        raise VidSkimError("抖音返回失败状态，作品可能受限、已删除或需要登录。")
    items = result.get("item_list")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise VidSkimError("作品不可访问、已删除或需要登录，未取得真实视频。")
    return _item_media(items[0], video_id)


def _item_media(item: dict, video_id: str) -> tuple[list[str], str]:
    if str(item.get("aweme_id", "")) != video_id:
        raise VidSkimError("抖音返回的作品 ID 与请求不一致。")
    status = item.get("status") or {}
    if not isinstance(status, dict):
        raise VidSkimError("作品权限信息格式异常。")
    if (
        status.get("is_delete")
        or status.get("is_prohibited")
        or status.get("private_status", 0) not in (0, "0")
        or item.get("is_private")
        or status.get("allow_share") is False
    ):
        raise VidSkimError("作品已删除或访问权限受限，无法取得真实视频。")
    if item.get("images") or item.get("aweme_type") in (2, 68):
        raise VidSkimError("首版只支持普通视频，暂不支持图文作品。")
    video = item.get("video") or {}
    title = item.get("desc", "")
    if not isinstance(video, dict) or not isinstance(title, str):
        raise VidSkimError("抖音返回的媒体或描述信息格式异常。")
    urls = []
    for key in ("play_addr", "download_addr"):
        address = video.get(key) or {}
        if isinstance(address, dict) and isinstance(address.get("url_list"), list):
            for url in address["url_list"]:
                if isinstance(url, str) and url and url not in urls:
                    urls.append(url)
    if not urls:
        raise VidSkimError("作品没有可下载的视频地址。")
    return urls[:3], title.strip() or f"抖音视频 {video_id}"


def _read_feed(
    client: httpx.Client, video_id: str, deadline: float
) -> tuple[list[str], str] | None:
    # Feed 也会返回推荐视频，只有精确匹配请求 ID 的作品才能用于转写。
    for endpoint in _FEED_ENDPOINTS:
        if time.monotonic() > deadline:
            raise VidSkimError("抖音下载已超过时间上限，请稍后重试。")
        url = f"{endpoint}?aweme_id={video_id}&aid=1128"
        try:
            with _response(
                client,
                url,
                api=True,
                headers={
                    "User-Agent": f"python-httpx/{httpx.__version__}",
                    "Accept": "application/json",
                },
            ) as response:
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > _MAX_PAGE_BYTES or time.monotonic() > deadline:
                        raise VidSkimError("抖音详情响应超过大小或时间上限。")
                data = json.loads(body)
        except (httpx.HTTPError, ValueError, VidSkimError):
            continue
        if not isinstance(data, dict) or data.get("status_code", 0) not in (0, "0"):
            continue
        items = data.get("aweme_list")
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and str(item.get("aweme_id", "")) == video_id:
                return _item_media(item, video_id)
    return None


def _validate_media(path: Path) -> None:
    try:
        with av.open(str(path)) as container:
            if not container.streams.video or not container.streams.audio:
                raise VidSkimError("下载内容缺少视频或音轨，不能用于真实语音转写。")
            if next(container.decode(video=0), None) is None:
                raise VidSkimError("下载内容的视频无法解码。")
        with av.open(str(path)) as container:
            if next(container.decode(audio=0), None) is None:
                raise VidSkimError("下载内容的音轨无法解码。")
    except (av.error.FFmpegError, OSError, ValueError) as exc:
        raise VidSkimError("下载内容不是可解码的视频，可能是风控页面或损坏媒体。") from exc


def _download(client: httpx.Client, url: str, path: Path, deadline: float) -> None:
    with _response(client, url, media=True) as response:
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        if content_type.startswith("text/") or content_type in {
            "application/json",
            "application/xhtml+xml",
        }:
            raise VidSkimError("媒体地址返回了网页或 JSON，未下载到真实视频。")
        length = response.headers.get("content-length")
        try:
            expected = int(length) if length is not None else None
        except ValueError as exc:
            raise VidSkimError("媒体响应的大小信息无效。") from exc
        if expected is not None and (expected <= 0 or expected > _MAX_MEDIA_BYTES):
            raise VidSkimError("视频为空或超过 512 MiB 下载上限。")
        size = 0
        with path.open("wb") as target:
            for chunk in response.iter_bytes(chunk_size=65536):
                if time.monotonic() > deadline:
                    raise VidSkimError("抖音下载已超过时间上限，请稍后重试。")
                size += len(chunk)
                if size > _MAX_MEDIA_BYTES:
                    raise VidSkimError("视频超过 512 MiB 下载上限。")
                target.write(chunk)
        if not size or (
            expected is not None
            and response.headers.get("content-encoding", "identity") == "identity"
            and size != expected
        ):
            raise VidSkimError("视频下载不完整。")
    _validate_media(path)


def download_video(canonical_url: str, cache_dir: Path) -> tuple[Path, str]:
    """返回经音视频解码验证的缓存文件和作品原始 desc；desc 只用于标题。"""
    _validate_url(canonical_url)
    video_id = _video_id(canonical_url)
    if not video_id or canonical_url != f"https://www.douyin.com/video/{video_id}":
        raise VidSkimError("下载需要 resolve_input 返回的规范抖音视频地址。")
    media_path = cache_dir / f"{video_id}.mp4"
    metadata_path = cache_dir / f"{video_id}.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            isinstance(metadata, dict)
            and metadata.get("source") == canonical_url
            and isinstance(metadata.get("title"), str)
            and media_path.is_file()
            and 0 < media_path.stat().st_size <= _MAX_MEDIA_BYTES
        ):
            _validate_media(media_path)
            return media_path, metadata["title"]
    except (OSError, json.JSONDecodeError, VidSkimError):
        pass
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + _DOWNLOAD_SECONDS
        with _client() as client:
            details = _read_feed(client, video_id, deadline)
            if details is None:
                page = _read_page(client, video_id, deadline)
                details = _parse_page(page, video_id)
            urls, title = details
            last_error = None
            for url in urls:
                for _ in range(_ATTEMPTS):
                    with tempfile.NamedTemporaryFile(
                        dir=cache_dir, suffix=".part", delete=False
                    ) as f:
                        temporary = Path(f.name)
                    try:
                        _download(client, url, temporary, deadline)
                        temporary.replace(media_path)
                        with tempfile.NamedTemporaryFile(
                            dir=cache_dir,
                            suffix=".json.part",
                            mode="w",
                            encoding="utf-8",
                            delete=False,
                        ) as f:
                            metadata_temporary = Path(f.name)
                            json.dump(
                                {"source": canonical_url, "title": title}, f, ensure_ascii=False
                            )
                        try:
                            metadata_temporary.replace(metadata_path)
                        finally:
                            metadata_temporary.unlink(missing_ok=True)
                        return media_path, title
                    except (httpx.HTTPError, VidSkimError) as exc:
                        last_error = exc
                        if time.monotonic() > deadline:
                            raise VidSkimError("抖音下载已超过时间上限，请稍后重试。") from exc
                    finally:
                        temporary.unlink(missing_ok=True)
            reason = (
                str(last_error) if isinstance(last_error, VidSkimError) else "媒体网络请求失败。"
            )
            raise VidSkimError(f"抖音视频下载失败：{reason}") from last_error
    except httpx.HTTPStatusError as exc:
        raise VidSkimError(f"抖音分享页请求失败（HTTP {exc.response.status_code}）。") from exc
    except httpx.HTTPError as exc:
        raise VidSkimError("抖音分享页网络请求失败，请稍后重试。") from exc
    except OSError as exc:
        raise VidSkimError("无法读写视频缓存，请检查目录权限和剩余空间。") from exc
