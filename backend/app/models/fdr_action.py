from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class FDRAction(Base):
    __tablename__ = "fdr_actions"

    id = Column(Integer, primary_key=True, index=True)

    fdr_id = Column(
        Integer,
        ForeignKey("fdrs.id"),
        nullable=False,
        index=True,
    )

    action_type = Column(
        String(30),
        nullable=False,
    )

    action_status = Column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    remarks = Column(Text, nullable=True)

    performed_by = Column(
        String(100),
        nullable=False,
    )

    # NEW: Records who approved or rejected the request
    decided_by = Column(
        String(100),
        nullable=True,
    )

    # NEW: Records when the decision was made
    decided_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    fdr = relationship("FDR")