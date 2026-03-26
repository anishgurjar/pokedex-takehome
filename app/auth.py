from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import get_jwt_secret

ALGORITHM = "HS256"
ALLOWED_ROLES = {"trainer", "ranger"}  # TODO: Centralize this later


@dataclass(frozen=True)
class CurrentPrincipal:
    user_id: str
    role: str
    status: str
    display_name: str | None = None


def _decode_access_token(token: str) -> CurrentPrincipal:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "role", "exp"]},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc

    user_id = payload.get("sub")
    role = payload.get("role")
    status = payload.get("status", "active")
    display_name = payload.get("name")

    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Token subject is required")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=401, detail="Token role is invalid")
    if status != "active":
        raise HTTPException(status_code=403, detail="User account is not active")

    return CurrentPrincipal(
        user_id=user_id,
        role=role,
        status=status,
        display_name=display_name if isinstance(display_name, str) else None,
    )


def get_current_principal(authorization: str | None = Header(None)) -> CurrentPrincipal:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token is required")

    return _decode_access_token(token)


def require_role(role: str):
    def _require_role(
        principal: CurrentPrincipal = Depends(get_current_principal),
    ) -> CurrentPrincipal:
        if principal.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Only {role}s can access this endpoint",
            )
        return principal

    return _require_role
