from hashlib import sha256
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.auth import AuditLog


def audit_event(
    db: Session,
    request: Request,
    *,
    action: str,
    outcome: str,
    actor_user_id: UUID | None = None,
    entity_type: str = "auth_session",
    entity_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    client_host = request.client.host if request.client else ""
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome=outcome,
            request_id=UUID(request.state.request_id),
            ip_hash=sha256(client_host.encode("utf-8")).hexdigest() if client_host else None,
            event_metadata=metadata or {},
        )
    )
