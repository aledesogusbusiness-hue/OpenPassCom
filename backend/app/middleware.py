from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.services.auth_service import decode_token


class StudioTenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware che verifica il studio_id dal JWT e lo inietta nello state della request.
    Endpoints pubblici (come /auth/login) vengono saltati.
    """

    PUBLIC_PATHS = {"/api/v1/auth/login", "/docs", "/openapi.json", "/redoc", "/health"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            payload = decode_token(token)
            studio_id = payload.get("studio_id")
            if studio_id:
                request.state.studio_id = studio_id
                request.state.user_role = payload.get("role")
                request.state.user_id = payload.get("sub")

        return await call_next(request)
