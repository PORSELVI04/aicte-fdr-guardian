from sqlalchemy import inspect

from app.database import engine


def ensure_columns() -> None:
    """Apply backward-compatible SQLite column additions."""
    inspector = inspect(engine)

    if "fdr_documents" not in inspector.get_table_names():
        raise RuntimeError(
            "fdr_documents table does not exist; create the schema first."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns("fdr_documents")
    }

    if "sha256" not in columns:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE fdr_documents ADD COLUMN sha256 VARCHAR(64)"
            )
