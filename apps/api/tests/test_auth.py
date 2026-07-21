from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password, require_roles
from app.database.session import SessionLocal
from app.main import create_app
from app.models.auth import AppRole, AuditLog, RevokedToken, User


@pytest.fixture
def employee_user():
    email = f"employee-{uuid4()}@example.test"
    user = User(
        id=uuid4(), email=email, password_hash=hash_password("correct-password"),
        role=AppRole.EMPLOYEE, is_active=True,
    )
    with SessionLocal() as db:
        db.add(user)
        db.commit()
        db.refresh(user)
    yield user
    with SessionLocal() as db:
        db.execute(delete(AuditLog).where(AuditLog.actor_user_id == user.id))
        db.execute(delete(RevokedToken).where(RevokedToken.user_id == user.id))
        db.execute(delete(User).where(User.id == user.id))
        db.commit()


def test_login_me_logout_and_revocation(employee_user):
    client = TestClient(create_app())
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": employee_user.email, "password": "correct-password"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()["data"]
    assert login_body["token_type"] == "bearer"
    assert login_body["user"]["email"] == employee_user.email
    headers = {"Authorization": f"Bearer {login_body['access_token']}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["data"]["role"] == "employee"

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    revoked_response = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_response.status_code == 401
    assert revoked_response.json()["error"]["code"] == "unauthenticated"

    with SessionLocal() as db:
        assert db.scalar(select(RevokedToken).where(RevokedToken.user_id == employee_user.id))
        assert db.scalar(select(AuditLog).where(AuditLog.actor_user_id == employee_user.id))


def test_login_rejects_invalid_credentials_with_safe_error():
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/auth/login",
        json={"email": f"unknown-{uuid4()}@example.test", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "invalid_credentials", "message": "Invalid credentials.", "details": [],
        "request_id": response.headers["x-request-id"],
    }


def test_protected_endpoint_requires_a_valid_token():
    response = TestClient(create_app()).get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_role_dependency_blocks_unapproved_role():
    employee = User(role=AppRole.EMPLOYEE)
    with pytest.raises(HTTPException) as exc_info:
        require_roles(AppRole.ADMINISTRATOR)(employee)
    assert exc_info.value.status_code == 403
