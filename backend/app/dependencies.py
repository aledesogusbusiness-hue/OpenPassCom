import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import User
from app.services.auth_service import decode_token, get_user_by_id
from app.services.user_service import has_client_access

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido: manca l'identificativo utente",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido: formato UUID errato",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato o disabilitato",
        )

    return user


def require_role(*roles: str):
    """Dependency factory per proteggere endpoint per ruolo."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permesso insufficiente per questa operazione",
            )
        return current_user

    return _check


async def verify_client_access(
    request: Request,
    client_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Dependency da registrare a livello di router (dependencies=[Depends(verify_client_access)])
    su ogni router con path del tipo /clients/{client_id}/....

    - Se il path non contiene client_id (es. GET /clients), non fa nulla: FastAPI
      inietta None perché il parametro diventa un query param opzionale.
    - Gli admin passano sempre.
    - Gli altri ruoli devono avere un ClientUserPermission per quel client_id;
      per i metodi di scrittura (POST/PUT/PATCH/DELETE) serve permesso='scrittura'.
    """
    if client_id is None or current_user.role == "admin":
        return

    is_write = request.method in ("POST", "PUT", "PATCH", "DELETE")
    if not await has_client_access(db, current_user.id, client_id, require_write=is_write):
        detail = (
            "Non hai i permessi di scrittura per questo cliente"
            if is_write
            else "Non hai accesso a questo cliente"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
