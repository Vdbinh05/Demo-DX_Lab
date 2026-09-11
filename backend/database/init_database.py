# SPDX-License-Identifier: MIT
"""Create and seed the local DX-Lab Core SQL Server database."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


DATABASE_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = DATABASE_DIR.parent
BACKEND_ENV = BACKEND_ROOT / ".env"


def split_batches(sql_text: str) -> list[str]:
    """Split an SSMS script on standalone GO batch separators."""
    return [
        batch.strip()
        for batch in re.split(
            r"^\s*GO\s*(?:--.*)?$", sql_text, flags=re.MULTILINE | re.IGNORECASE
        )
        if batch.strip()
    ]


def required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value == "replace-with-your-local-password":
        raise RuntimeError(f"Missing {name} in backend/.env")
    return value


def connect_to_master() -> pyodbc.Connection:
    driver = os.getenv("DXLAB_SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")
    server = os.getenv("DXLAB_SQL_SERVER", "localhost,1433")
    username = os.getenv("DXLAB_SQL_USER", "sa")
    password = required_setting("DXLAB_SQL_PASSWORD")

    connection_string = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        "DATABASE=master;"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string, timeout=10, autocommit=True)


def configured_database_name() -> str:
    database_name = (os.getenv("DXLAB_SQL_DATABASE") or "DXLabCore").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", database_name):
        raise RuntimeError(
            "DXLAB_SQL_DATABASE chỉ được chứa chữ, số, gạch dưới hoặc gạch ngang."
        )
    return database_name


def execute_script(
    connection: pyodbc.Connection,
    path: Path,
    database_name: str,
) -> None:
    print(f"Running {path.name}...")
    sql_text = path.read_text(encoding="utf-8-sig").replace("DXLabCore", database_name)
    cursor = connection.cursor()
    for batch in split_batches(sql_text):
        cursor.execute(batch)
        while cursor.nextset():
            pass
    cursor.close()


def main() -> int:
    if not BACKEND_ENV.exists():
        print("[ERROR] Missing backend/.env. Run CAI_DAT_LAN_DAU.bat first.")
        return 1

    load_dotenv(BACKEND_ENV, override=False)

    try:
        database_name = configured_database_name()
        connection = connect_to_master()
        try:
            execute_script(connection, DATABASE_DIR / "schema.sql", database_name)
            execute_script(connection, DATABASE_DIR / "seed.sql", database_name)
        finally:
            connection.close()
    except (OSError, RuntimeError, pyodbc.Error) as error:
        print(f"[ERROR] Could not initialize database: {error}")
        return 1

    print(f"{database_name} database initialization completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
