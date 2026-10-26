from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.notification_service import get_fdr_notifications

router = APIRouter(
    prefix="/api/notifications",
    tags=["FDR Notifications"],
)


@router.get("/maturity")
def maturity_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_fdr_notifications(db)