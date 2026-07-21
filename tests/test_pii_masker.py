"""
Test script for the PII Masker module.
Run this to verify the module is working correctly before proceeding.

Usage:
    python tests/test_pii_masker.py
"""

import sys
import os

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pii_masker import PIIMasker


def test_email_masking():
    """Test that email addresses are detected and masked."""
    masker = PIIMasker()
    text = "Contact John at john.smith@company.com for details."
    result = masker.mask(text)
    assert "<EMAIL_ADDRESS>" in result, f"FAIL: Email not masked. Got: {result}"
    assert "john.smith@company.com" not in result, f"FAIL: Email still present. Got: {result}"
    print("[PASS] Email masking works")


def test_phone_masking():
    """Test that phone numbers are detected and masked."""
    masker = PIIMasker()
    text = "Call me at 555-123-4567 to discuss."
    result = masker.mask(text)
    assert "555-123-4567" not in result, f"FAIL: Phone number still present. Got: {result}"
    print("[PASS] Phone number masking works")


def test_ssn_masking():
    """Test that SSNs are detected and masked."""
    masker = PIIMasker()
    text = "My SSN is 123-45-6789 for the form."
    result = masker.mask(text)
    assert "123-45-6789" not in result, f"FAIL: SSN still present. Got: {result}"
    print("[PASS] SSN masking works")


def test_no_pii():
    """Test that text without PII is returned unchanged."""
    masker = PIIMasker()
    text = "The quarterly report shows a 15% increase in revenue."
    result = masker.mask(text)
    assert result == text, f"FAIL: Text was modified when no PII present. Got: {result}"
    print("[PASS] No-PII text returned unchanged")


def test_mask_with_report():
    """Test the mask_with_report method returns structured data."""
    masker = PIIMasker()
    text = "Email john@test.com or call 555-999-8888."
    report = masker.mask_with_report(text)

    assert "masked_text" in report, "FAIL: Report missing 'masked_text'"
    assert "pii_found" in report, "FAIL: Report missing 'pii_found'"
    assert "pii_count" in report, "FAIL: Report missing 'pii_count'"
    assert report["pii_count"] > 0, f"FAIL: No PII found. Report: {report}"
    assert "john@test.com" not in report["masked_text"], "FAIL: Email still in masked text"
    print(f"[PASS] mask_with_report works -- found {report['pii_count']} PII items")
    for item in report["pii_found"]:
        print(f"   > {item['entity_type']}: '{item['original_text']}' (confidence: {item['score']})")


def test_sample_transcript():
    """Test against the actual sample transcript file."""
    masker = PIIMasker()
    transcript_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "sample_transcript.txt",
    )

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    report = masker.mask_with_report(transcript)

    print(f"\n[INFO] Sample Transcript PII Report:")
    print(f"   Total PII items found: {report['pii_count']}")
    for item in report["pii_found"]:
        print(f"   > {item['entity_type']}: '{item['original_text']}' (confidence: {item['score']})")

    # Verify specific known PII in our sample transcript is caught
    masked = report["masked_text"]
    known_pii = [
        ("john.smith@company.com", "email"),
        ("555-123-4567", "phone"),
        ("123-45-6789", "SSN"),
    ]

    all_caught = True
    for pii_value, pii_label in known_pii:
        if pii_value in masked:
            print(f"   [FAIL] {pii_label} '{pii_value}' was NOT masked")
            all_caught = False
        else:
            print(f"   [OK] {pii_label} '{pii_value}' was correctly masked")

    if all_caught:
        print("\n[PASS] All known PII in sample transcript was masked successfully")
    else:
        print("\n[FAIL] Some PII was not caught -- review score_threshold or entities list")

    # Print a snippet of the masked transcript for visual verification
    print(f"\n--- Masked Transcript (first 500 chars) ---")
    print(masked[:500])
    print("...")


if __name__ == "__main__":
    print("=" * 60)
    print("  MeetingMind AI -- PII Masker Module Tests")
    print("=" * 60)
    print()

    test_email_masking()
    test_phone_masking()
    test_ssn_masking()
    test_no_pii()
    test_mask_with_report()
    test_sample_transcript()

    print()
    print("=" * 60)
    print("  All PII Masker tests completed!")
    print("=" * 60)
