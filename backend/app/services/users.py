# SPDX-License-Identifier: MIT
"""Security-sensitive business rules for administrator account management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus

from app.core.security import USERNAME_PATTERN, hash_password, password_policy_error
from app.repositories.users import UserRepository
from app.schemas.admin import AccountPatch, AdminAccountPayload


@dataclass(slots=True)
class UserRuleError(Exception):
    status_code: int
    detail: str


@dataclass(frozen=True, slots=True)
class NewUser:
    full_name: str
    username: str
    password_hash: str
    role_id: str


@dataclass(frozen=True, slots=True)
class UserChange:
    role_id: str | None
    account_status: str | None


def _clean(value: str | None) -> str:
    return (value or "").strip()


def prepare_new_user(payload: AdminAccountPayload) -> NewUser:
    """Validate cheap input rules before opening a database connection."""
    full_name = _clean(payload.full_name)
    username = _clean(payload.username)
    if len(full_name) < 2:
        raise UserRuleError(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Họ và tên phải có ít nhất 2 ký tự.",
        )
    if not USERNAME_PATTERN.fullmatch(username):
        raise UserRuleError(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Tên đăng nhập chỉ gồm chữ không dấu, số, dấu chấm, gạch dưới hoặc gạch ngang.",
        )
    password_error = password_policy_error(payload.password)
    if password_error:
        raise UserRuleError(HTTPStatus.UNPROCESSABLE_ENTITY, password_error)
    return NewUser(
        full_name=full_name,
        username=username,
        password_hash=hash_password(payload.password),
        role_id=_clean(payload.role_id),
    )


def list_users(connection) -> dict:
    return UserRepository(connection.cursor()).list_with_roles()


def create_user(connection, new_user: NewUser, actor: dict) -> dict:
    repository = UserRepository(connection.cursor())
    if not repository.role_exists(new_user.role_id):
        raise UserRuleError(HTTPStatus.BAD_REQUEST, "Vai trò không hợp lệ.")

    created_user_id = repository.insert_user(
        username=new_user.username,
        password_hash=new_user.password_hash,
        full_name=new_user.full_name,
        role_id=new_user.role_id,
    )
    repository.insert_create_activity(
        created_user_id=created_user_id,
        username=new_user.username,
        actor=actor,
        new_values=json.dumps(
            {
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role_id": new_user.role_id,
            },
            ensure_ascii=False,
        ),
    )
    return {"success": True, "user_id": created_user_id}


def prepare_user_change(
    user_id: int,
    payload: AccountPatch,
    actor: dict,
) -> UserChange:
    role_id = _clean(payload.role_id) if payload.role_id is not None else None
    account_status = (
        _clean(payload.account_status)
        if payload.account_status is not None
        else None
    )
    if user_id == int(actor["UserID"]) and role_id is not None and role_id != "Admin":
        raise UserRuleError(
            HTTPStatus.BAD_REQUEST,
            "Bạn không thể tự hạ quyền tài khoản Admin đang đăng nhập.",
        )
    if (
        user_id == int(actor["UserID"])
        and account_status is not None
        and account_status != "Active"
    ):
        raise UserRuleError(
            HTTPStatus.BAD_REQUEST,
            "Bạn không thể tự khóa tài khoản đang đăng nhập.",
        )
    return UserChange(role_id=role_id, account_status=account_status)


def update_user(
    connection,
    user_id: int,
    change: UserChange,
    actor: dict,
) -> dict:
    repository = UserRepository(connection.cursor())
    target = repository.get_for_update(user_id)
    if target is None:
        raise UserRuleError(HTTPStatus.NOT_FOUND, "Không tìm thấy tài khoản.")

    current_role = str(target.RoleID)
    current_status = str(target.Status)
    role_changed = change.role_id is not None and change.role_id != current_role
    status_changed = (
        change.account_status is not None
        and change.account_status != current_status
    )
    removes_active_admin = (
        current_role.lower() == "admin"
        and current_status.lower() == "active"
        and (
            (change.role_id is not None and change.role_id.lower() != "admin")
            or (
                change.account_status is not None
                and change.account_status != "Active"
            )
        )
    )
    if removes_active_admin and repository.count_active_admins() <= 1:
        raise UserRuleError(
            HTTPStatus.BAD_REQUEST,
            "Hệ thống phải luôn còn ít nhất một tài khoản Admin đang hoạt động.",
        )

    if role_changed:
        repository.update_role(user_id, change.role_id)
    if status_changed:
        repository.update_status(user_id, change.account_status)
    changed = role_changed or status_changed
    if changed:
        repository.revoke_sessions(user_id)
        repository.insert_update_activity(
            target_user_id=user_id,
            actor=actor,
            old_values=json.dumps(
                {"role_id": current_role, "account_status": current_status},
                ensure_ascii=False,
            ),
            new_values=json.dumps(
                {
                    "role_id": change.role_id or current_role,
                    "account_status": change.account_status or current_status,
                },
                ensure_ascii=False,
            ),
        )
    return {"success": True, "session_revoked": changed}
