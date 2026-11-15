"""Almacenamiento SQLite de la zona publica.

Aislado a proposito de la base de autenticacion (SQLAlchemy/MySQL): la fase
experimental publica usa su propio archivo SQLite con sqlite3 directo, para no
tocar el esquema ni la URI de la app autenticada.

Tablas:
- weather_cache     cache de respuestas Open-Meteo con TTL
- radar_scans       inventario de frames compuestos IDEAM descubiertos
- public_requests_log trazabilidad con IP hasheada (sin PII)
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

_SCHEMA = """
CREATE TABLE IF NOT EXISTS weather_cache (
    cache_key  TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS radar_scans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL,            -- 'composite' | 'overlay:<radar>'
    stamp         TEXT NOT NULL,            -- 'YYMMDDHHMM' UTC
    url           TEXT NOT NULL,
    status        TEXT NOT NULL,            -- 'available' | 'missing'
    discovered_at TEXT NOT NULL,
    UNIQUE (kind, stamp)
);

CREATE TABLE IF NOT EXISTS public_requests_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    endpoint    TEXT NOT NULL,
    ip_hash     TEXT,
    status_code INTEGER
);

CREATE INDEX IF NOT EXISTS idx_weather_cache_exp ON weather_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_radar_scans_recent ON radar_scans(kind, stamp DESC);
CREATE INDEX IF NOT EXISTS idx_reqlog_window ON public_requests_log(endpoint, ts);
"""


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_ip(ip: str, salt: str) -> str:
    """Hash de IP con salt del servidor: minimizacion de datos, nunca IP cruda."""
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()[:16]


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def cache_get(db_path: str, key: str):
    """Devuelve el payload JSON si la entrada no expiro; None en otro caso."""
    now = utcnow_iso()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT payload, expires_at FROM weather_cache WHERE cache_key = ? AND expires_at > ?",
            (key, now),
        ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["payload"])
    except (ValueError, TypeError):
        return None


def cache_put(db_path: str, key: str, payload: dict, ttl_seconds: int) -> None:
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(seconds=ttl_seconds)).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO weather_cache (cache_key, payload, fetched_at, expires_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, "
            "fetched_at = excluded.fetched_at, expires_at = excluded.expires_at",
            (key, json.dumps(payload), now.isoformat(), expires),
        )


def scan_upsert(db_path: str, kind: str, stamp: str, url: str, status: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO radar_scans (kind, stamp, url, status, discovered_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(kind, stamp) DO UPDATE SET url = excluded.url, "
            "status = excluded.status, discovered_at = excluded.discovered_at",
            (kind, stamp, url, status, utcnow_iso()),
        )


def recent_scans(db_path: str, kind: str, limit: int = 40):
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT stamp, url, status, discovered_at FROM radar_scans "
            "WHERE kind = ? AND status = 'available' ORDER BY stamp DESC LIMIT ?",
            (kind, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def requests_in_window(db_path: str, endpoint: str, ip_hash: str, window_seconds: int) -> int:
    since = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM public_requests_log "
            "WHERE endpoint = ? AND ip_hash = ? AND ts > ?",
            (endpoint, ip_hash, since),
        ).fetchone()
    return int(row["n"])


def log_request(db_path: str, endpoint: str, ip_hash: str, status_code: int) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO public_requests_log (ts, endpoint, ip_hash, status_code) "
            "VALUES (?, ?, ?, ?)",
            (utcnow_iso(), endpoint, ip_hash, status_code),
        )
