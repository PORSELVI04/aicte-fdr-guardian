from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionResponse

from app.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/api/institutions",
    tags=["Institutions"],
)


@router.post("/", response_model=InstitutionResponse, status_code=201)
def create_institution(
    data: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "OFFICER")),
):
    existing = db.query(Institution).filter(
        Institution.institution_code == data.institution_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Institution code already exists",
        )

    institution = Institution(**data.model_dump())

    db.add(institution)
    db.commit()
    db.refresh(institution)

    return institution


@router.get("/", response_model=list[InstitutionResponse])
def list_institutions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Institution).order_by(Institution.name).all()