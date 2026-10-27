import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps
from rapidfuzz import fuzz


# Update this path if Tesseract is installed elsewhere.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an FDR certificate image using Tesseract OCR.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("Certificate file not found.")

    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)

        extracted_text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )

    return extracted_text.strip()


def extract_fdr_fields(text: str) -> dict:
    """
    Extract the FDR number, deposit amount, and dates from OCR text.
    """
    normalized_text = text.replace("\r", "\n")
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text)

    # Extract FDR numbers from labels such as:
    # FDR Number: FD-DEMO-001
    # FDR No: FD-DEMO-001
    # FDR Number: FDR-OFFICER-TEST-001
    fdr_number = None

    number_pattern = re.compile(
        r"\b(?:FDR|FD|FOR)\s*"
        r"(?:NUMBER|NO\.?|NUM(?:BER)?)\s*[:#-]?\s*"
        r"([A-Z0-9][A-Z0-9/-]{2,})",
        re.IGNORECASE,
    )

    number_match = number_pattern.search(normalized_text)

    if number_match:
        fdr_number = number_match.group(1).strip(" :-")

    # Extract deposit amounts.
    # Supports:
    # Deposit Amount: 100000.00
    # Deposit Amount: ₹ 1,00,000.00
    # Amount: Rs. 50,000
    amount_pattern = re.compile(
        r"(?:DEPOSIT\s+AMOUNT|AMOUNT)\s*[:\-]?\s*"
        r"(?:(?:INR|RS\.?|₹|%)\s*)?"
        r"([\d,]+(?:\.\d{1,2})?)",
        re.IGNORECASE,
    )

    amount_match = amount_pattern.search(normalized_text)
    deposit_amount = None

    if amount_match:
        deposit_amount = amount_match.group(1).replace(",", "")

    # Extract dates for subsequent comparison.
    date_pattern = re.compile(
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b"
    )

    dates_found = date_pattern.findall(normalized_text)

    return {
        "fdr_number": fdr_number,
        "deposit_amount": deposit_amount,
        "dates_found": dates_found,
        "raw_text": normalized_text,
    }


def compare_text(
    extracted: str | None,
    expected: str | None,
) -> dict:
    """
    Fuzzy comparison for names and other non-critical text.

    The score is a string similarity score, not a probability
    or a certificate authenticity score.
    """
    if not extracted or not expected:
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    score = fuzz.ratio(
        str(extracted).strip().casefold(),
        str(expected).strip().casefold(),
    )

    return {
        "score": round(score, 2),
        "status": "MATCH" if score >= 90 else "REVIEW_REQUIRED",
    }


def _normalize_identifier(value: str | None) -> str:
    """
    Normalize an identifier by removing whitespace and ignoring case.
    Punctuation, including hyphens, is preserved.
    """
    return re.sub(r"\s+", "", str(value or "")).upper()


def compare_identifier(
    extracted: str | None,
    expected: str | None,
) -> dict:
    """
    Exact comparison for identifiers such as FDR numbers.
    """
    if extracted is None or expected is None:
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    extracted_value = _normalize_identifier(extracted)
    expected_value = _normalize_identifier(expected)

    if not extracted_value or not expected_value:
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    is_match = extracted_value == expected_value

    return {
        "score": 100.0 if is_match else 0.0,
        "status": "MATCH" if is_match else "REVIEW_REQUIRED",
    }


def compare_amount(
    extracted: str | None,
    expected: str | None,
) -> dict:
    """
    Exact monetary comparison using Decimal.

    Thousands separators are ignored. Values are compared to two
    decimal places. Invalid or missing values require review.
    """
    if extracted is None or expected is None:
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    extracted_text = str(extracted).replace(",", "").strip()
    expected_text = str(expected).replace(",", "").strip()

    if not extracted_text or not expected_text:
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    try:
        extracted_value = Decimal(extracted_text)
        expected_value = Decimal(expected_text)

        if (
            not extracted_value.is_finite()
            or not expected_value.is_finite()
        ):
            return {
                "score": None,
                "status": "NOT_AVAILABLE",
            }

        extracted_value = extracted_value.quantize(Decimal("0.01"))
        expected_value = expected_value.quantize(Decimal("0.01"))

    except (InvalidOperation, ValueError):
        return {
            "score": None,
            "status": "NOT_AVAILABLE",
        }

    is_match = extracted_value == expected_value

    return {
        "score": 100.0 if is_match else 0.0,
        "status": "MATCH" if is_match else "REVIEW_REQUIRED",
    }