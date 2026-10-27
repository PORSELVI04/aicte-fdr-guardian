import argparse
import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path("fdr_guardian.db")
UPLOAD_DIR = Path("uploads")


def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill missing SHA-256 hashes for FDR documents."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing hashes to the database.",
    )
    args = parser.parse_args()

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH.resolve()}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(fdr_documents)"
            )
        }

        if "sha256" not in columns:
            raise RuntimeError(
                "sha256 column is missing. Run the migration first."
            )

        rows = connection.execute(
            """
            SELECT id, stored_filename, sha256
            FROM fdr_documents
            ORDER BY id
            """
        ).fetchall()

        prepared = []
        missing = []
        errors = []

        for document_id, filename, stored_hash in rows:
            if stored_hash:
                print(
                    f"SKIP | Document {document_id}: "
                    "hash already exists"
                )
                continue

            file_path = UPLOAD_DIR / filename

            if not file_path.is_file():
                missing.append(document_id)
                print(
                    f"MISSING | Document {document_id}: "
                    f"{file_path}"
                )
                continue

            try:
                digest = calculate_sha256(file_path)
                prepared.append((document_id, digest))
                print(
                    f"READY | Document {document_id}: "
                    f"{digest}"
                )
            except OSError as exc:
                errors.append((document_id, str(exc)))
                print(f"ERROR | Document {document_id}: {exc}")

        print("\nSummary")
        print(f"Total documents: {len(rows)}")
        print(f"Hashes ready: {len(prepared)}")
        print(f"Missing files: {len(missing)}")
        print(f"Read errors: {len(errors)}")

        if missing or errors:
            raise RuntimeError(
                "Backfill stopped because files are missing "
                "or could not be read."
            )

        if not args.apply:
            print("\nDRY RUN: No database changes were made.")
            print("Run with --apply to write the hashes.")
            return

        # Recheck the database before writing.
        connection.execute("BEGIN IMMEDIATE")

        for document_id, digest in prepared:
            connection.execute(
                """
                UPDATE fdr_documents
                SET sha256 = ?
                WHERE id = ?
                  AND (sha256 IS NULL OR sha256 = '')
                """,
                (digest, document_id),
            )

        connection.commit()

        # Verify that every document now has a hash.
        unhashed = connection.execute(
            """
            SELECT COUNT(*)
            FROM fdr_documents
            WHERE sha256 IS NULL OR sha256 = ''
            """
        ).fetchone()[0]

        print("\nBackfill completed.")
        print(f"Records still without hashes: {unhashed}")

        if unhashed:
            raise RuntimeError(
                "Some records still do not have hashes."
            )

    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()