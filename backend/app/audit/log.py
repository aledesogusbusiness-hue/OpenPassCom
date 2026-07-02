import uuid
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.auth import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    payload: Optional[dict] = None,
    ip: Optional[str] = None,
) -> None:
    """
    Registra un'azione nell'audit log.
    NON esegue commit — viene committato con la transazione principale.
    """
    entry = AuditLog(
        id=uuid.uuid4(),
        studio_id=uuid.UUID(settings.STUDIO_ID),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        payload=payload,
        ip_address=ip,
    )
    db.add(entry)
