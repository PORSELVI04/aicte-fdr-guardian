from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VerificationReview(Base):
    __tablename__ = "verification_reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    fdr_id: Mapped[int] = mapped_column(
        ForeignKey("fdrs.id"),
        nullable=False,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("fdr_documents.id"),
        nullable=False,
        index=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        default="REVIEW_REQUIRED",
        nullable=False,
    )

    discrepancy_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewer_decision: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
    )

    reviewer_comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )