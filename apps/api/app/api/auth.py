from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.rate_limit import auth_rate_limiter
from app.core.security import (
    bearer_scheme,
    create_access_token,
    decode_access_token,
    get_current_user,
    verify_password,
)
from app.database.session import get_db
from app.models.auth import RevokedToken, User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.audit import audit_event

router = APIRouter(prefix="/auth", tags=["authentication"])


def _request_key(request: Request, email: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{email}"


@router.post("/login", response_model=dict)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    auth_rate_limiter.check(
        _request_key(request, payload.email),
        limit=settings.rate_limit_auth_per_minute,
    )
    user = db.scalar(
        select(User).where(User.email == payload.email, User.deleted_at.is_(None))
    )
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        audit_event(db, request, action="login", outcome="denied")
        db.commit()
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "Invalid credentials."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, _, _ = create_access_token(user, settings)
    user.last_login_at = datetime.now(UTC)
    audit_event(
        db,
        request,
        action="login",
        outcome="succeeded",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    response = LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )
    return {"data": response.model_dump(mode="json"), "meta": {}}


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    if credentials is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication is required."})
    claims = decode_access_token(credentials.credentials, settings)
    token_id = UUID(claims["jti"])
    if db.get(RevokedToken, token_id) is None:
        db.add(
            RevokedToken(
                jti=token_id,
                user_id=current_user.id,
                expires_at=datetime.fromtimestamp(
                    jwt.get_unverified_claims(credentials.credentials)["exp"], tz=UTC
                ),
            )
        )
    audit_event(
        db,
        request,
        action="logout",
        outcome="succeeded",
        actor_user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
    )
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=dict)
def me(current_user: User = Depends(get_current_user)):
    return {"data": UserResponse.model_validate(current_user).model_dump(mode="json"), "meta": {}}
