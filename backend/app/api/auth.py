from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, UserOut
from app.services.auth_service import authenticate_user, create_access_token
from app.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        audit_service.log_event(
            correlation_id="AUTH-CLIENT",
            actor=payload.username,
            event_type="LOGIN_FAILED",
            tool_name="login",
            details={"username": payload.username},
            status="ERROR",
            db=db
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(user)
    audit_service.log_event(
        correlation_id="AUTH-CLIENT",
        actor=user.username,
        event_type="LOGIN_SUCCESS",
        tool_name="login",
        details={"username": user.username, "role": user.role},
        status="SUCCESS",
        db=db
    )
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)