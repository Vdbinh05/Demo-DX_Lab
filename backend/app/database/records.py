# SPDX-License-Identifier: MIT
"""Convert SQL Server cursor rows into JSON-safe dictionaries."""

from datetime import date, datetime
from decimal import Decimal


def json_value(value):
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def rows(cursor) -> list[dict]:
    columns = [column[0] for column in cursor.description]
    return [
        {columns[index]: json_value(value) for index, value in enumerate(row)}
        for row in cursor.fetchall()
    ]


def one(cursor) -> dict | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return {columns[index]: json_value(value) for index, value in enumerate(row)}
