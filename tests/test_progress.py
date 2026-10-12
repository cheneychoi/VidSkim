import threading

import pytest

from watch2note import progress


def test_blocking_stage_reports_heartbeat_and_stops_on_exit():
    noticed = threading.Event()
    messages = []

    def collect(message):
        messages.append(message)
        if len(messages) > 1:
            noticed.set()

    with progress.ProgressStage(collect, "下载视频", interval=0.01) as stage:
        assert noticed.wait(timeout=1)
    assert "下载视频" in messages[-1]
    assert "已耗时" in messages[-1]
    assert not stage._thread.is_alive()


def test_stage_stops_heartbeat_after_failure():
    with pytest.raises(RuntimeError, match="download failed"):
        with progress.ProgressStage(lambda _: None, "下载视频") as stage:
            raise RuntimeError("download failed")
    assert not stage._thread.is_alive()


def test_updates_are_throttled_by_wall_clock(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(progress.time, "monotonic", lambda: clock[0])
    messages = []
    with progress.ProgressStage(messages.append, "开始转写") as stage:
        stage.update("音频 00:05 / 10:00", force=True)
        stage.update("音频 01:30 / 10:00")
        assert len(messages) == 2
        clock[0] = 11.0
        stage.update("音频 01:35 / 10:00")
    assert len(messages) == 3
    assert "音频 01:35 / 10:00" in messages[-1]
    assert "已耗时 11 秒" in messages[-1]
