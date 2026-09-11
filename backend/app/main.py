# SPDX-License-Identifier: MIT
"""FastAPI application factory and middleware configuration.

Router aggregation follows the MIT-licensed Full Stack FastAPI Template at
commit cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7, adapted for pyodbc and the
existing DX-Lab Core API contract.
"""

from contextlib import asynccontextmanager
import logging
import time
import uuid

import pyodbc
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.database.connection import check_database, database_error_message


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Fail fast with an actionable message when SQL Server is not ready."""
    try:
        result = check_database()
        logger.info(
            "SQL Server startup check passed: database=%s required_tables=%s",
            result["database"],
            result["required_tables"],
        )
    except (pyodbc.Error, RuntimeError) as exc:
        message = database_error_message(exc) if isinstance(exc, pyodbc.Error) else str(exc)
        logger.critical("Backend startup stopped: %s", message)
        raise RuntimeError(message) from exc
    yield


app = FastAPI(title="DX-Lab Core API", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a traceable request ID and log one concise access record."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    started_at = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s in %.1f ms request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started_at) * 1000,
        request_id,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
