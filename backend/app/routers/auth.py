from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, TokenResponse
from app.services.audit_service import add_audit_log
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ALLOWED_ROLES = {"ADMIN", "OFFICER", "REVIEWER", "VIEWER"}


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    # Public registration must not allow users to assign privileged roles.
    if data.role != "VIEWER":
        raise HTTPException(
            status_code=403,
            detail="Public registration is limited to the VIEWER role.",
        )

    existing = db.query(User).filter(
        (User.username == data.username) |
        (User.email == data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists.",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="VIEWER",
    )

    db.add(user)
    db.flush()

    add_audit_log(
        db=db,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=user.id,
        actor=user.username,
        details="Public registration; role: VIEWER.",
    )
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if (
        user is None
        or not verify_password(form_data.password, user.password_hash)
    ):
        add_audit_log(
            db=db,
            action="LOGIN_FAILED",
            entity_type="USER",
            entity_id=user.id if user else 0,
            actor=user.username if user else "UNKNOWN_USER",
            details="Invalid username or password.",
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        add_audit_log(
            db=db,
            action="LOGIN_FAILED",
            entity_type="USER",
            entity_id=user.id,
            actor=user.username,
            details="Login rejected: account is inactive.",
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    add_audit_log(
        db=db,
        action="LOGIN_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        actor=user.username,
        details=f"Successful login; role: {user.role}.",
    )
    db.commit()

    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
