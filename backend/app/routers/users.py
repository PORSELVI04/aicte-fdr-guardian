from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse
from app.services.auth_service import hash_password

router = APIRouter(
    prefix="/api/users",
    tags=["User Management"],
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    # Prevent duplicate usernames or email addresses.
    existing = db.query(User).filter(
        (User.username == data.username)
        | (User.email == data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )

    # Do not create additional ADMIN accounts through this endpoint.
    if data.role not in {"OFFICER", "REVIEWER", "VIEWER"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only OFFICER, REVIEWER, and VIEWER roles can be created here.",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    add_audit_log(
        db,
        action="USER_CREATED",
        entity_type="USER",
        entity_id=user.id,
        actor=current_user.username,
        details=f"User {user.username} created with role {user.role}.",
    )
    db.commit()
    db.refresh(user)

    return user