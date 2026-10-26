from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FDR(Base):
    __tablename__ = "fdrs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    fdr_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )

    bank_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    branch_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    maturity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    validity_status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
    )

    administrative_status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING_VERIFICATION",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship(
        back_populates="fdrs",
    )