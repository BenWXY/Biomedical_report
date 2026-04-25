from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


class CacheStore:
    def __init__(self, path: Path):
        self.path = path
        self.json_path = path.with_suffix(path.suffix + ".json")
        self.logger = logging.getLogger(__name__)
        self.sqlite_available = True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._init_db()
        except sqlite3.Error as exc:
            self.sqlite_available = False
            self.logger.warning("SQLite cache unavailable at %s; using JSON fallback: %s", path, exc)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    format TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        if not self.sqlite_available:
            return self._json_get(key, ttl_seconds)
        with self._connect() as conn:
            row = conn.execute("SELECT payload, created_at FROM cache_entries WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        payload, created_at = row
        if time.time() - float(created_at) > ttl_seconds:
            return None
        return json.loads(payload)

    def set(self, key: str, payload: Any) -> None:
        if not self.sqlite_available:
            self._json_set(key, payload)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_entries(key, payload, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET payload=excluded.payload, created_at=excluded.created_at
                """,
                (key, json.dumps(payload, ensure_ascii=False), time.time()),
            )

    def record_report(self, target: str, format_name: str, path: Path) -> None:
        if not self.sqlite_available:
            data = self._read_json()
            data.setdefault("report_versions", []).append(
                {"target": target, "format": format_name, "path": str(path), "created_at": time.time()}
            )
            self._write_json(data)
            return
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO report_versions(target, format, path, created_at) VALUES (?, ?, ?, ?)",
                (target, format_name, str(path), time.time()),
            )

    def _json_get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        row = self._read_json().get("cache_entries", {}).get(key)
        if not row:
            return None
        if time.time() - float(row["created_at"]) > ttl_seconds:
            return None
        return row["payload"]

    def _json_set(self, key: str, payload: Any) -> None:
        data = self._read_json()
        data.setdefault("cache_entries", {})[key] = {"payload": payload, "created_at": time.time()}
        self._write_json(data)

    def _read_json(self) -> Any:
        if not self.json_path.exists():
            return {"cache_entries": {}, "report_versions": []}
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"cache_entries": {}, "report_versions": []}

    def _write_json(self, data: Any) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
