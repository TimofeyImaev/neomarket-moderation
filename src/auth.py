import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import src.config as config
from src.errors import ApiError

_bearer = HTTPBearer(auto_error=False)


def get_current_moderator_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise ApiError(401, "UNAUTHORIZED", "Missing Authorization header")
    try:
        claims = jwt.decode(
            credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "UNAUTHORIZED", "Token expired")
    except jwt.InvalidTokenError:
        raise ApiError(401, "UNAUTHORIZED", "Invalid token")
    if claims.get("role") != "moderator":
        raise ApiError(403, "FORBIDDEN", "Moderator role required")
    sub = claims.get("sub")
    if not sub:
        raise ApiError(401, "UNAUTHORIZED", "Invalid sub claim")
    return str(sub)


def verify_b2b_service_key(
    x_service_key: str | None = Header(default=None, alias="X-Service-Key"),
) -> None:
    if not config.B2B_TO_MOD_KEY or x_service_key != config.B2B_TO_MOD_KEY:
        raise ApiError(401, "UNAUTHORIZED", "Missing or invalid X-Service-Key")
