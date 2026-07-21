from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import forbidden_error, unauthorized_error
from app.database.session import get_db
from app.models.auth import AppRole, RevokedToken, User

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def create_access_token(user: User, settings: Settings) -> tuple[str, datetime, UUID]:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.jwt_expire_minutes)
    token_id = uuid4()
    payload = {
        "sub": str(user.id),
        "jti": str(token_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at, token_id


def decode_access_token(token: str, settings: Settings) -> dict[str, str]:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        UUID(str(claims["sub"]))
        UUID(str(claims["jti"]))
    except (JWTError, KeyError, ValueError) as exc:
        raise unauthorized_error() from exc
    return {"sub": str(claims["sub"]), "jti": str(claims["jti"])}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized_error()

    claims = decode_access_token(credentials.credentials, settings)
    token_id = UUID(claims["jti"])
    if db.get(RevokedToken, token_id) is not None:
        raise unauthorized_error()

    user = db.scalar(
        select(User).where(
            User.id == UUID(claims["sub"]),
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise unauthorized_error()
    return user


def require_roles(*allowed_roles: AppRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise forbidden_error()
        return current_user

    return dependency
