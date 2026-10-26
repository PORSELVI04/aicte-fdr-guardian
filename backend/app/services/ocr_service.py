import re
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

    # Normalize OCR text and common spacing issues.
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
    # Supports examples:
    # Deposit Amount: 100000.00
    # Deposit Amount: ₹ 1,00,000.00
    # Deposit Amount: % 1,00,000.00
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
        # Remove Indian-style grouping commas.
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
    Compare extracted text with a stored value.

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