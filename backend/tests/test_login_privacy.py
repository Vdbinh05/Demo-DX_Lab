# SPDX-License-Identifier: MIT
"""Ensure failed login responses cannot be used to enumerate accounts."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes.auth import (  # noqa: E402
    LOGIN_ATTEMPT_LIMIT,
    LOGIN_FAILED_MESSAGE,
    _login_attempts,
    login,
)
from app.core.security import hash_password  # noqa: E402
from app.schemas.auth import LoginRequest  # noqa: E402


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def execute(self, *_args, **_kwargs):
        return self

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row

    def cursor(self):
        return FakeCursor(self.row)

    def close(self):
        pass


class LoginPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_hash = hash_password("Correct@123")

    def assert_generic_failure(self, row, *, password="Wrong@123", portal="employee"):
        request = LoginRequest(username="candidate", password=password, portal=portal)
        with patch(
            "app.api.routes.auth.get_connection",
            return_value=FakeConnection(row),
        ):
            with self.assertRaises(HTTPException) as raised:
                login(request)
        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.detail, LOGIN_FAILED_MESSAGE)

    def test_unknown_username_and_wrong_password_have_same_response(self):
        self.assert_generic_failure(None)
        self.assert_generic_failure(
            (1, "candidate", self.valid_hash, "Candidate", "Sales", "Active")
        )

    def test_wrong_portal_and_locked_account_have_same_response(self):
        self.assert_generic_failure(
            (1, "admin.demo", self.valid_hash, "Admin", "Admin", "Active"),
            password="Correct@123",
            portal="employee",
        )
        self.assert_generic_failure(
            (2, "locked", self.valid_hash, "Locked", "Sales", "Locked"),
            password="Correct@123",
            portal="employee",
        )

    def test_repeated_failures_are_rate_limited_without_changing_message(self):
        _login_attempts.clear()
        request = LoginRequest(
            username="rate-limit-candidate",
            password="Wrong@123",
            portal="employee",
        )
        with patch(
            "app.api.routes.auth.get_connection",
            return_value=FakeConnection(None),
        ):
            for _ in range(LOGIN_ATTEMPT_LIMIT):
                with self.assertRaises(HTTPException) as raised:
                    login(request)
                self.assertEqual(raised.exception.status_code, 401)
                self.assertEqual(raised.exception.detail, LOGIN_FAILED_MESSAGE)
            with self.assertRaises(HTTPException) as blocked:
                login(request)
        self.assertEqual(blocked.exception.status_code, 429)
        self.assertEqual(blocked.exception.detail, LOGIN_FAILED_MESSAGE)
        _login_attempts.clear()


if __name__ == "__main__":
    unittest.main()
