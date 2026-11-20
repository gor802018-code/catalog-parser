"""Загрузка страниц: таймауты, повторы и пауза между запросами."""

from __future__ import annotations

import time
import urllib.error
import urllib.request


class FetchError(RuntimeError):
    """Страницу не удалось получить."""


class Fetcher:
    def __init__(self, user_agent: str, timeout_seconds: int, retries: int, delay_seconds: float) -> None:
        self._user_agent = user_agent
        self._timeout = timeout_seconds
        self._retries = retries
        self._delay = delay_seconds

    def get(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            if attempt:
                time.sleep(self._delay * attempt)
            request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    return response.read().decode(charset, errors="replace")
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_error = error
        msg = f"Не удалось получить {url}: {last_error}"
        raise FetchError(msg)

    def wait(self) -> None:
        if self._delay:
            time.sleep(self._delay)
