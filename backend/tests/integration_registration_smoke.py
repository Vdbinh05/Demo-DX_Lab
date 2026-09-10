# SPDX-License-Identifier: MIT
"""Non-destructive smoke test for public employee registration."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from db import get_connection  # noqa: E402


API_URL = os.getenv("DXLAB_TEST_API_URL", "http://127.0.0.1:8000").rstrip("/")


def request_json(path: str, *, method: str = "GET", body=None, token=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{API_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read().decode("utf-8"))
        raise AssertionError(f"{method} {path} -> {error.code}: {payload}") from error


def cleanup_user(username: str) -> None:
    connection = get_connection()
    try:
        connection.cursor().execute(
            "DELETE FROM dbo.Users WHERE Username = ? AND RoleID = 'Sales'", username
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> int:
    username = f"smoke.{uuid.uuid4().hex[:12]}"
    password = "SmokeTest@123"
    try:
        status, registered = request_json(
            "/register",
            method="POST",
            body={
                "full_name": "Tài khoản kiểm thử tạm",
                "username": username,
                "password": password,
            },
        )
        assert status == 201
        assert registered["user"]["RoleID"] == "Sales"

        status, signed_in = request_json(
            "/login",
            method="POST",
            body={"username": username, "password": password},
        )
        assert status == 200
        token = signed_in["access_token"]

        status, profile = request_json("/me", token=token)
        assert status == 200
        assert profile["Username"] == username
        assert profile["RoleID"] == "Sales"
        print("PASS: registration, login and session validation were verified.")
        return 0
    finally:
        cleanup_user(username)
        print(f"CLEANUP: removed temporary user {username}.")


if __name__ == "__main__":
    raise SystemExit(main())
