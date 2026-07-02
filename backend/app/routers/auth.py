from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.log import log_action
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticazione"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )

    token = create_access_token(user)

    await log_action(
        db=db,
        user_id=user.id,
        action="login",
        entity_type="User",
        entity_id=str(user.id),
        payload={"email": user.email},
        ip=request.client.host if request.client else None,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
