from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.security import verify_password


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user: User, expiry_hours: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=expiry_hours or settings.JWT_EXPIRY_HOURS)
    payload: dict[str, Any] = {
        "sub": user.username,
        "role": user.role,
        "display_name": user.display_name,
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None