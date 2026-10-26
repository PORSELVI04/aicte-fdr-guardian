from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.fdr import FDR
from app.models.institution import Institution
from app.models.user import User
from app.schemas.fdr import FDRCreate, FDRResponse

router = APIRouter(
    prefix="/api/fdrs",
    tags=["FDR Records"],
)


# --------------------------------------------------
# 1. Create FDR
# ADMIN and OFFICER only
# --------------------------------------------------
@router.post("/", response_model=FDRResponse, status_code=201)
def create_fdr(
    data: FDRCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER")
    ),
):
    # Verify that the institution exists
    institution = db.get(Institution, data.institution_id)

    if institution is None:
        raise HTTPException(
            status_code=404,
            detail="Institution not found",
        )

    # Prevent duplicate FDR numbers
    existing = (
        db.query(FDR)
        .filter(FDR.fdr_number == data.fdr_number)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="FDR number already exists",
        )

    # Create and save the FDR record
    fdr = FDR(**data.model_dump())

    db.add(fdr)
    db.commit()
    db.refresh(fdr)

    return fdr


# --------------------------------------------------
# 2. List and Search FDR Records
# ADMIN, OFFICER, and REVIEWER only
# --------------------------------------------------
@router.get("/", response_model=list[FDRResponse])
def list_fdrs(
    search: str | None = Query(default=None, max_length=100),
    institution_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    query = db.query(FDR)

    # Search by FDR number, bank name, or branch name
    if search:
        term = f"%{search}%"

        query = query.filter(
            or_(
                FDR.fdr_number.ilike(term),
                FDR.bank_name.ilike(term),
                FDR.branch_name.ilike(term),
            )
        )

    # Filter by institution
    if institution_id is not None:
        query = query.filter(
            FDR.institution_id == institution_id
        )

    # Sort by earliest maturity date
    return query.order_by(FDR.maturity_date.asc()).all()


# --------------------------------------------------
# 3. Retrieve an Individual FDR
# ADMIN, OFFICER, and REVIEWER only
# --------------------------------------------------
@router.get("/{fdr_id}", response_model=FDRResponse)
def get_fdr(
    fdr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "OFFICER", "REVIEWER")
    ),
):
    fdr = db.get(FDR, fdr_id)

    if fdr is None:
        raise HTTPException(
            status_code=404,
            detail="FDR not found",
        )

    return fdr