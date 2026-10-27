from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.fdr import FDR


def get_fdr_notifications(db: Session) -> dict:
    today = date.today()

    seven_days = today + timedelta(days=7)
    thirty_days = today + timedelta(days=30)

    fdrs = db.query(FDR).order_by(FDR.maturity_date.asc()).all()

    expired = []
    expiring_soon = []
    expiring_within_30_days = []

    for fdr in fdrs:
        # Released FDRs should not generate maturity notifications.
        if fdr.validity_status == "RELEASED":
            continue

        record = {
            "fdr_id": fdr.id,
            "fdr_number": fdr.fdr_number,
            "institution_id": fdr.institution_id,
            "bank_name": fdr.bank_name,
            "deposit_amount": str(fdr.deposit_amount),
            "maturity_date": fdr.maturity_date.isoformat(),
        }

        if fdr.maturity_date < today:
            expired.append(record)

        elif fdr.maturity_date <= seven_days:
            expiring_soon.append(record)

        elif fdr.maturity_date <= thirty_days:
            expiring_within_30_days.append(record)

    return {
        "as_of_date": today.isoformat(),
        "expired_count": len(expired),
        "expiring_within_7_days_count": len(expiring_soon),
        "expiring_within_30_days_count": (
            len(expiring_soon) + len(expiring_within_30_days)
        ),
        "expired": expired,
        "expiring_within_7_days": expiring_soon,
        "expiring_in_8_to_30_days": expiring_within_30_days,
    }