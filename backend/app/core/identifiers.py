# SPDX-License-Identifier: MIT
"""Generate short business identifiers used by persisted entities."""

import uuid
from datetime import datetime


def business_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now():%y%m%d}-{uuid.uuid4().hex[:6].upper()}"
