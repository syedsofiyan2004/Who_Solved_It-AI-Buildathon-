from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get("/health/live")
def liveness(settings: Settings = Depends(get_settings)):
    return {
        "data": {
            "service": "api",
            "status": "ok",
            "environment": settings.app_env,
            "version": settings.app_version,
            "rag_enabled": settings.rag_enabled,
        },
        "meta": {},
    }


@router.get("/health/ready")
def readiness(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("select 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "database_unavailable",
                "message": "Database readiness check failed.",
            },
        ) from exc

    return {
        "data": {
            "service": "api",
            "status": "ready",
            "environment": settings.app_env,
            "database": "ok",
            "bedrock": settings.bedrock_status,
        },
        "meta": {},
    }
