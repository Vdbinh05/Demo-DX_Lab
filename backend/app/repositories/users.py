# SPDX-License-Identifier: MIT
"""SQL Server persistence for administrator account management."""

from app.database.records import rows


class UserRepository:
    """Keep account SQL separate from validation and HTTP handling."""

    def __init__(self, cursor):
        self.cursor = cursor

    def list_with_roles(self) -> dict:
        self.cursor.execute(
            """
            SELECT users.UserID AS user_id, users.FullName AS full_name,
                   users.Username AS username, users.RoleID AS role_id,
                   users.Status AS account_status, users.CreatedAt AS created_at,
                   users.LastLoginAt AS last_login_at
            FROM dbo.Users users
            ORDER BY users.CreatedAt DESC, users.UserID DESC
            """
        )
        users = rows(self.cursor)
        self.cursor.execute(
            """
            SELECT RoleID AS role_id, RoleName AS role_name
            FROM dbo.Roles
            WHERE RoleID IN ('Admin', 'Sales', 'Warehouse')
            ORDER BY CASE RoleID
                WHEN 'Admin' THEN 1 WHEN 'Sales' THEN 2 ELSE 3 END
            """
        )
        return {"items": users, "roles": rows(self.cursor)}

    def role_exists(self, role_id: str) -> bool:
        row = self.cursor.execute(
            "SELECT 1 FROM dbo.Roles WHERE RoleID = ?",
            role_id,
        ).fetchone()
        return row is not None

    def insert_user(
        self,
        *,
        username: str,
        password_hash: str,
        full_name: str,
        role_id: str,
    ) -> int:
        self.cursor.execute(
            """
            INSERT INTO dbo.Users
                (Username, PasswordHash, FullName, RoleID, Status)
            OUTPUT INSERTED.UserID
            VALUES (?, ?, ?, ?, N'Active')
            """,
            username,
            password_hash,
            full_name,
            role_id,
        )
        return int(self.cursor.fetchone()[0])

    def insert_create_activity(
        self,
        *,
        created_user_id: int,
        username: str,
        actor: dict,
        new_values: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Account', ?,
                    'CREATE_USER', 'User', ?, ?)
            """,
            f"{actor['FullName']} đã tạo tài khoản {username}",
            int(actor["UserID"]),
            str(created_user_id),
            new_values,
        )

    def get_for_update(self, user_id: int):
        return self.cursor.execute(
            """
            SELECT RoleID, Status
            FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
            WHERE UserID = ?
            """,
            user_id,
        ).fetchone()

    def count_active_admins(self) -> int:
        row = self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
            WHERE LOWER(RoleID) = 'admin' AND LOWER(Status) = 'active'
            """
        ).fetchone()
        return int(row[0])

    def update_role(self, user_id: int, role_id: str) -> None:
        self.cursor.execute(
            "UPDATE dbo.Users SET RoleID = ? WHERE UserID = ?",
            role_id,
            user_id,
        )

    def update_status(self, user_id: int, account_status: str) -> None:
        self.cursor.execute(
            "UPDATE dbo.Users SET Status = ? WHERE UserID = ?",
            account_status,
            user_id,
        )

    def revoke_sessions(self, user_id: int) -> None:
        self.cursor.execute(
            """
            UPDATE dbo.UserSessions
            SET RevokedAt = SYSDATETIME()
            WHERE UserID = ? AND RevokedAt IS NULL
            """,
            user_id,
        )

    def insert_update_activity(
        self,
        *,
        target_user_id: int,
        actor: dict,
        old_values: str,
        new_values: str,
    ) -> None:
        self.cursor.execute(
            """
            INSERT INTO dbo.Activities
                (ActivityTime, Description, Category, UserID, Action,
                 EntityType, EntityID, OldValues, NewValues)
            VALUES (CONVERT(varchar(5), GETDATE(), 108), ?, N'Account', ?,
                    'UPDATE_USER', 'User', ?, ?, ?)
            """,
            f"{actor['FullName']} đã cập nhật tài khoản {target_user_id}",
            int(actor["UserID"]),
            str(target_user_id),
            old_values,
            new_values,
        )
