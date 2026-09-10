# SPDX-License-Identifier: MIT
"""Fast unit checks for password and token helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import jwt


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from core import (  # noqa: E402
    ACCESS_TOKEN_MINUTES,
    AUTH_ALGORITHM,
    AUTH_SECRET,
    create_access_token,
    hash_password,
    verify_password,
)


class AuthenticationTests(unittest.TestCase):
    def test_password_round_trip_and_rejection(self):
        encoded = hash_password("Example@123")
        self.assertNotEqual(encoded, "Example@123")
        self.assertTrue(verify_password("Example@123", encoded))
        self.assertFalse(verify_password("wrong-password", encoded))

    def test_access_token_contains_identity_and_expiry(self):
        token = create_access_token(42, "sales.test", "Sales")
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["username"], "sales.test")
        self.assertEqual(payload["role"], "Sales")
        self.assertGreater(payload["exp"] - payload["iat"], 0)
        self.assertEqual(payload["exp"] - payload["iat"], ACCESS_TOKEN_MINUTES * 60)


if __name__ == "__main__":
    unittest.main()
