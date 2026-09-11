# SPDX-License-Identifier: MIT
"""Authentication request schemas."""

from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    portal: Literal["employee", "admin"]


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
