# Unit tests for text cleaning and PII redaction.

import pytest
from app.services.preprocess import preprocess_text


def test_preprocess_removes_emails():
    """Verify email addresses are properly redacted with [EMAIL]."""
    text = "Please reach out to official.user@citygov.in or contact@ward4.org regarding the broken pipe."
    cleaned = preprocess_text(text)
    assert "[EMAIL]" in cleaned
    assert "official.user@citygov.in" not in cleaned
    assert "contact@ward4.org" not in cleaned


def test_preprocess_removes_phone_numbers():
    """Verify 10-digit Indian phone numbers with/without prefixes are redacted."""
    text = "Call me urgently at +91 9876543210 or 8765432109 for the street light issue."
    cleaned = preprocess_text(text)
    assert "[PHONE]" in cleaned
    assert "9876543210" not in cleaned
    assert "8765432109" not in cleaned


def test_preprocess_redacts_ten_digit_numbers():
    """Verify arbitrary 10+ digit numbers (e.g. meter numbers, IDs) are redacted."""
    text = "Account grievance number 1234567890123 submitted for resolution."
    cleaned = preprocess_text(text)
    assert "[REDACTED]" in cleaned or "[AADHAAR]" in cleaned
    assert "1234567890123" not in cleaned


def test_preprocess_preserves_complaint_meaning():
    """Verify domain complaint facts and vocabulary remain intact."""
    text = "Garbage not collected in Ward 7 for 5 days. Severe foul smell near market."
    cleaned = preprocess_text(text)
    assert "Garbage not collected" in cleaned
    assert "Ward 7" in cleaned
    assert "Severe foul smell" in cleaned
