# SPDX-License-Identifier: MIT
"""Validated runtime configuration for DX-Lab Core."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parent
ENV_FILE = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)


class ConfigurationError(RuntimeError):
    """Raised when required local configuration is missing or malformed."""


def _required(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value or value.startswith("replace-with-"):
        raise ConfigurationError(
            f"Thiếu {name} trong backend/.env. Hãy chạy CAI_DAT_LAN_DAU.bat "
            "hoặc cập nhật cấu hình SQL Server của máy này."
        )
    return value


def _positive_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} phải là một số nguyên.") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} phải lớn hơn 0.")
    return value


def _origins() -> tuple[str, ...]:
    default = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    values = [item.strip().rstrip("/") for item in (os.getenv("DXLAB_CORS_ORIGINS") or default).split(",")]
    origins = tuple(item for item in values if item)
    if not origins:
        raise ConfigurationError("DXLAB_CORS_ORIGINS phải chứa ít nhất một địa chỉ frontend.")
    return origins


@dataclass(frozen=True)
class Settings:
    sql_server: str
    sql_database: str
    sql_user: str
    sql_password: str
    sql_driver: str
    auth_secret: str
    access_token_minutes: int
    cors_origins: tuple[str, ...]

    def sql_connection_string(self, *, database: str | None = None) -> str:
        return (
            f"DRIVER={self.sql_driver};"
            f"SERVER={self.sql_server};"
            f"DATABASE={database or self.sql_database};"
            f"UID={self.sql_user};"
            f"PWD={self.sql_password};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
        )


def load_settings() -> Settings:
    return Settings(
        sql_server=(os.getenv("DXLAB_SQL_SERVER") or "localhost,1433").strip(),
        sql_database=(os.getenv("DXLAB_SQL_DATABASE") or "DXLabCore").strip(),
        sql_user=(os.getenv("DXLAB_SQL_USER") or "sa").strip(),
        sql_password=_required("DXLAB_SQL_PASSWORD"),
        sql_driver=(os.getenv("DXLAB_SQL_DRIVER") or "{ODBC Driver 17 for SQL Server}").strip(),
        auth_secret=(os.getenv("DXLAB_AUTH_SECRET") or "").strip(),
        access_token_minutes=_positive_int("DXLAB_ACCESS_TOKEN_MINUTES", 480),
        cors_origins=_origins(),
    )


settings = load_settings()
