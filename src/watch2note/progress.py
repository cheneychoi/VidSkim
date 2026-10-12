import threading
import time
from typing import Callable


class ProgressStage:
    """Report wall-clock progress while a blocking operation is running."""

    def __init__(self, progress: Callable[[str], None], message: str, interval: float = 10):
        self.progress = progress
        self.message = message
        self.interval = interval
        self._stopped = threading.Event()
        self._lock = threading.Lock()

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._started

    def update(self, message: str | None = None, *, force: bool = False) -> None:
        with self._lock:
            if message is not None:
                self.message = message
            now = time.monotonic()
            if force or now - self._last_notice >= self.interval:
                self.progress(f"{self.message}（已耗时 {now - self._started:.0f} 秒）")
                self._last_notice = now

    def _heartbeat(self) -> None:
        while not self._stopped.is_set():
            with self._lock:
                delay = max(0, self.interval - (time.monotonic() - self._last_notice))
            if self._stopped.wait(delay):
                return
            self.update()

    def __enter__(self):
        self._started = self._last_notice = time.monotonic()
        self.update(force=True)
        self._thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stopped.set()
        self._thread.join()
