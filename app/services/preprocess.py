# Data preprocessing and PII anonymization services.

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


def preprocess_text(text: str) -> str:
    """Clean text, strip extra whitespace, and redact PII patterns.

    Removes emails, phone numbers, Aadhaar-like IDs, 10+ digit numbers,
    and personal title names (Mr./Mrs./Dr.).

    Args:
        text: Raw input complaint text.

    Returns:
        Anonymized and normalized text string.
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize whitespace
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Redact email addresses
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    text = re.sub(email_pattern, "[EMAIL]", text)

    # Redact phone numbers (standard Indian 10-digit formats, +91, with/without spaces/hyphens)
    phone_pattern = r"(\+91[\-\s]?)?[6-9]\d{9}\b"
    text = re.sub(phone_pattern, "[PHONE]", text)

    # Redact Aadhaar-like patterns (12 digits with spaces or hyphens)
    aadhaar_pattern = r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"
    text = re.sub(aadhaar_pattern, "[AADHAAR]", text)

    # Redact any remaining 10+ consecutive digit numbers
    ten_digit_pattern = r"\b\d{10,}\b"
    text = re.sub(ten_digit_pattern, "[REDACTED]", text)

    # Redact names like Mr. X, Mrs. Y, Dr. Z
    name_pattern = r"\b(Mr\.|Mrs\.|Ms\.|Dr\.|Shri|Smt\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
    text = re.sub(name_pattern, "[NAME]", text)

    return text.strip()


def load_and_anonymize(filepath: str) -> List[Dict[str, Any]]:
    """Load complaint records from CSV or JSON file and anonymize text fields.

    Args:
        filepath: Path to the CSV or JSON file.

    Returns:
        List of dictionaries with keys: text, ward, department, filed_date.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    records: List[Dict[str, Any]] = []

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if isinstance(raw_data, dict) and "complaints" in raw_data:
                raw_data = raw_data["complaints"]
            for item in raw_data:
                cleaned_text = preprocess_text(item.get("text", ""))
                if cleaned_text:
                    records.append(
                        {
                            "text": cleaned_text,
                            "ward": str(item.get("ward", "Ward 1")),
                            "department": item.get("department", "General"),
                            "filed_date": str(item.get("filed_date", "2026-01-01")),
                            "category": item.get("category", item.get("department", "General")),
                            "is_synthetic": item.get("is_synthetic", True),
                        }
                    )
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            cleaned_text = preprocess_text(str(row.get("text", "")))
            if cleaned_text:
                records.append(
                    {
                        "text": cleaned_text,
                        "ward": str(row.get("ward", "Ward 1")),
                        "department": str(row.get("department", "General")),
                        "filed_date": str(row.get("filed_date", "2026-01-01")),
                        "category": str(row.get("category", row.get("department", "General"))),
                        "is_synthetic": bool(row.get("is_synthetic", True)),
                    }
                )
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Expected .csv or .json")

    logger.info("Successfully loaded and anonymized %d records from %s", len(records), filepath)
    return records
