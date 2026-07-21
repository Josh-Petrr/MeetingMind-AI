"""
MeetingMind AI - PII Masker Module
===================================
Uses Microsoft Presidio to detect and anonymize Personally Identifiable
Information (PII) from meeting transcripts BEFORE they reach any AI model.

Supported PII Types:
- Email addresses
- Phone numbers
- Social Security Numbers (US)
- Person names
- Credit card numbers
- IP addresses

Usage:
    from utils.pii_masker import PIIMasker

    masker = PIIMasker()
    masked_text = masker.mask(raw_transcript)
    print(masked_text)
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Optional


class PIIMasker:
    """Detects and masks PII from text using Microsoft Presidio."""

    # PII entity types we want to detect and mask
    DEFAULT_ENTITIES = [
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "US_SSN",
        "CREDIT_CARD",
        "IP_ADDRESS",
        "US_DRIVER_LICENSE",
        "US_PASSPORT",
        "IBAN_CODE",
    ]

    def __init__(
        self,
        entities: Optional[list[str]] = None,
        language: str = "en",
        score_threshold: float = 0.5,
    ):
        """
        Initialize the PII Masker.

        Args:
            entities: List of PII entity types to detect. Defaults to DEFAULT_ENTITIES.
            language: Language of the text. Defaults to "en".
            score_threshold: Minimum confidence score to consider a detection valid.
                             Lower = more aggressive masking. Defaults to 0.5.
        """
        self.entities = entities or self.DEFAULT_ENTITIES
        self.language = language
        self.score_threshold = score_threshold

        # Initialize Presidio engines
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Register custom US phone number recognizer.
        # Presidio's default PhoneRecognizer uses the 'phonenumbers' library
        # which requires a country code prefix (+1). This custom recognizer
        # catches common US formats like 555-123-4567 and (555) 123-4567.
        us_phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            name="USPhonePatternRecognizer",
            patterns=[
                Pattern(
                    name="us_phone_with_hyphens",
                    regex=r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                    score=0.7,
                ),
                Pattern(
                    name="us_phone_with_parens",
                    regex=r"\(\d{3}\)\s*\d{3}[-.\s]\d{4}",
                    score=0.7,
                ),
            ],
        )
        self.analyzer.registry.add_recognizer(us_phone_recognizer)

        # Register custom US SSN recognizer.
        # Presidio's default UsSsnRecognizer may miss SSNs without strong
        # contextual clues (e.g., "social security number"). This custom
        # recognizer catches the XXX-XX-XXXX format directly.
        us_ssn_recognizer = PatternRecognizer(
            supported_entity="US_SSN",
            name="UsSsnPatternRecognizer",
            patterns=[
                Pattern(
                    name="us_ssn_dashes",
                    regex=r"\b\d{3}-\d{2}-\d{4}\b",
                    score=0.7,
                ),
            ],
        )
        self.analyzer.registry.add_recognizer(us_ssn_recognizer)

    def analyze(self, text: str) -> list[RecognizerResult]:
        """
        Analyze text for PII entities without masking.

        Args:
            text: Raw text to analyze.

        Returns:
            List of RecognizerResult objects with detected PII locations and types.
        """
        results = self.analyzer.analyze(
            text=text,
            entities=self.entities,
            language=self.language,
            score_threshold=self.score_threshold,
        )
        return results

    def mask(self, text: str) -> str:
        """
        Detect and mask all PII in the given text.

        Replaces PII with placeholder tags like <EMAIL_ADDRESS>, <PHONE_NUMBER>, etc.

        Args:
            text: Raw text containing potential PII.

        Returns:
            Text with all detected PII replaced by type-specific placeholders.
        """
        # Step 1: Analyze — find all PII entities in the text
        analyzer_results = self.analyze(text)

        if not analyzer_results:
            return text  # No PII found, return original text

        # Step 2: Anonymize — replace detected PII with placeholders
        # Using "replace" operator which substitutes PII with its entity type label
        operators = {
            entity_type: OperatorConfig(
                "replace", {"new_value": f"<{entity_type}>"}
            )
            for entity_type in self.entities
        }

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators,
        )

        return anonymized_result.text

    def mask_with_report(self, text: str) -> dict:
        """
        Mask PII and return both the masked text and a report of what was found.

        Args:
            text: Raw text containing potential PII.

        Returns:
            Dictionary with:
              - "masked_text": The anonymized text
              - "pii_found": List of dicts with entity_type, original_text,
                             start, end, and confidence score
              - "pii_count": Total number of PII items detected
        """
        analyzer_results = self.analyze(text)

        pii_items = []
        for result in analyzer_results:
            pii_items.append(
                {
                    "entity_type": result.entity_type,
                    "original_text": text[result.start : result.end],
                    "start": result.start,
                    "end": result.end,
                    "score": round(result.score, 2),
                }
            )

        masked_text = self.mask(text)

        return {
            "masked_text": masked_text,
            "pii_found": pii_items,
            "pii_count": len(pii_items),
        }
