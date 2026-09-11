# SPDX-License-Identifier: MIT
"""Regression tests for administrator account invariants."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.schemas.admin import AccountPatch
from app.services.users import (
    UserChange,
    UserRuleError,
    prepare_user_change,
    update_user,
)


CONNECTION = SimpleNamespace(cursor=lambda: object())
ADMIN = {"UserID": 1, "FullName": "Admin Demo"}


class UserServiceTests(unittest.TestCase):
    def test_admin_cannot_demote_the_current_account(self):
        with self.assertRaises(UserRuleError) as context:
            prepare_user_change(
                1,
                AccountPatch(role_id="Sales"),
                ADMIN,
            )
        self.assertEqual(context.exception.status_code, 400)

    def test_admin_cannot_lock_the_current_account(self):
        with self.assertRaises(UserRuleError) as context:
            prepare_user_change(
                1,
                AccountPatch(account_status="Locked"),
                ADMIN,
            )
        self.assertEqual(context.exception.status_code, 400)

    @patch("app.services.users.UserRepository")
    def test_system_keeps_at_least_one_active_admin(self, repository_type):
        repository = repository_type.return_value
        repository.get_for_update.return_value = SimpleNamespace(
            RoleID="Admin",
            Status="Active",
        )
        repository.count_active_admins.return_value = 1

        with self.assertRaises(UserRuleError) as context:
            update_user(
                CONNECTION,
                2,
                UserChange(role_id="Sales", account_status=None),
                ADMIN,
            )

        self.assertEqual(context.exception.status_code, 400)
        repository.update_role.assert_not_called()

    @patch("app.services.users.UserRepository")
    def test_permission_change_revokes_existing_sessions(self, repository_type):
        repository = repository_type.return_value
        repository.get_for_update.return_value = SimpleNamespace(
            RoleID="Sales",
            Status="Active",
        )

        result = update_user(
            CONNECTION,
            2,
            UserChange(role_id="Warehouse", account_status=None),
            ADMIN,
        )

        self.assertEqual(result, {"success": True, "session_revoked": True})
        repository.update_role.assert_called_once_with(2, "Warehouse")
        repository.revoke_sessions.assert_called_once_with(2)
        repository.insert_update_activity.assert_called_once()


if __name__ == "__main__":
    unittest.main()
