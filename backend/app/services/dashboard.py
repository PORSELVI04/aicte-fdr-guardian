from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.fdr import FDR


def get_dashboard_summary(db: Session) -> dict:
    today = date.today()
    upcoming_limit = today + timedelta(days=30)

    fdrs = db.query(FDR).all()

    active_count = 0
    expiring_count = 0
    expired_count = 0
    total_deposit = Decimal("0.00")

    for fdr in fdrs:
        total_deposit += fdr.deposit_amount

        if fdr.maturity_date < today:
            expired_count += 1
        else:
            active_count += 1

            if fdr.maturity_date <= upcoming_limit:
                expiring_count += 1

    return {
        "total_fdrs": len(fdrs),
        "active_fdrs": active_count,
        "expiring_within_30_days": expiring_count,
        "expired_fdrs": expired_count,
        "total_deposit_amount": str(total_deposit),
        "as_of_date": today.isoformat(),
    }