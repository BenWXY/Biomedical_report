from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Mapping, Optional


class HttpError(RuntimeError):
    pass


class HttpClient:
    def __init__(self, timeout_seconds: int = 20, retries: int = 2, backoff_seconds: float = 0.8):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.logger = logging.getLogger(__name__)

    def get_json(self, url: str, params: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v not in ("", None)}, doseq=True)
            url = f"{url}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": "research-intel-prototype/0.1"})
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    return json.loads(response.read().decode(charset))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                self.logger.warning("HTTP request failed: %s attempt=%s", url, attempt + 1)
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (attempt + 1))
        raise HttpError(f"Could not fetch {url}: {last_error}")

