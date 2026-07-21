from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def api_error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


def unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "unauthenticated", "message": "Authentication is required."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_error() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "forbidden", "message": "You do not have permission to perform this action."},
    )
