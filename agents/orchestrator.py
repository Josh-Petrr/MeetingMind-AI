"""
MeetingMind AI - Orchestrator
================================
The master pipeline that coordinates the entire meeting processing flow.

Pipeline:
1. Receive raw transcript
2. Mask PII (Presidio)
3. Retrieve historical context from Qdrant (Memory Loop via Max)
4. Run Boris (summary) and Anna (action extraction) in sequence
5. Run Max (significance scoring + memory storage)
6. Return the complete structured result

Usage:
    from agents.orchestrator import MeetingOrchestrator

    orchestrator = MeetingOrchestrator()
    result = orchestrator.process_meeting(
        transcript="...",
        org_id="org_001",
        meeting_id="meeting_001",
    )
"""

import time
from typing import Optional

from agents.lyzr_manager import LyzrManager
from agents.boris import BorisAgent
from agents.anna import AnnaAgent
from agents.max import MaxAgent
from utils.pii_masker import PIIMasker
from memory.qdrant_store import QdrantMemoryStore
from utils.embeddings import EmbeddingService


class MeetingOrchestrator:
    """Coordinates the full meeting processing pipeline."""

    def __init__(self):
        """Initialize all components with shared instances to avoid duplication."""
        print("[INIT] Initializing MeetingMind AI Orchestrator...")
        start = time.time()

        # Shared services
        self.lyzr_manager = LyzrManager()
        self.pii_masker = PIIMasker()
        self.embedding_service = EmbeddingService()
        self.memory_store = QdrantMemoryStore()

        # Agents — all share the same LyzrManager
        self.boris = BorisAgent(manager=self.lyzr_manager)
        self.anna = AnnaAgent(manager=self.lyzr_manager)
        self.max = MaxAgent(
            manager=self.lyzr_manager,
            memory_store=self.memory_store,
            embedding_service=self.embedding_service,
        )

        elapsed = time.time() - start
        print(f"[INIT] Orchestrator ready in {elapsed:.1f}s")

    def process_meeting(
        self,
        transcript: str,
        org_id: str,
        meeting_id: str,
        skip_memory_retrieval: bool = False,
    ) -> dict:
        """
        Process a complete meeting transcript through the full pipeline.

        Args:
            transcript: Raw meeting transcript text (may contain PII).
            org_id: Organization ID for data isolation.
            meeting_id: Unique meeting identifier.
            skip_memory_retrieval: If True, skip the Memory Loop context retrieval.

        Returns:
            Complete structured result with:
            - pii_report: PII masking details
            - boris_output: Executive summary and decisions
            - anna_output: Action items and decisions
            - max_output: Significance scores and memory storage results
            - historical_context: Past context used (if any)
            - timing: Execution times for each step
        """
        result = {
            "meeting_id": meeting_id,
            "org_id": org_id,
            "pipeline_status": "running",
        }
        timing = {}

        # =============================================
        # STEP 1: PII Masking
        # =============================================
        print(f"\n{'='*60}")
        print(f"  Processing Meeting: {meeting_id}")
        print(f"{'='*60}")

        print("\n[STEP 1/5] Masking PII...")
        step_start = time.time()

        pii_report = self.pii_masker.mask_with_report(transcript)
        masked_transcript = pii_report["masked_text"]

        timing["pii_masking"] = round(time.time() - step_start, 2)
        print(
            f"  Done -- {pii_report['pii_count']} PII items masked "
            f"({timing['pii_masking']}s)"
        )

        result["pii_report"] = {
            "pii_count": pii_report["pii_count"],
            "pii_types": list(
                set(item["entity_type"] for item in pii_report["pii_found"])
            ),
        }

        # =============================================
        # STEP 2: Memory Loop — Retrieve Historical Context
        # =============================================
        historical_context = ""
        if not skip_memory_retrieval:
            print("\n[STEP 2/5] Retrieving historical context (Memory Loop)...")
            step_start = time.time()

            try:
                # Use the first 500 chars of transcript as a query
                snippet = masked_transcript[:500]
                historical_context = self.max.retrieve_context(
                    transcript_snippet=snippet,
                    org_id=org_id,
                    top_k=5,
                )
                timing["memory_retrieval"] = round(time.time() - step_start, 2)

                if historical_context:
                    print(
                        f"  Done -- found relevant past context "
                        f"({timing['memory_retrieval']}s)"
                    )
                else:
                    print(
                        f"  Done -- no relevant past context found "
                        f"({timing['memory_retrieval']}s)"
                    )
            except Exception as e:
                print(f"  [WARN] Memory retrieval failed: {e}")
                timing["memory_retrieval"] = round(time.time() - step_start, 2)
        else:
            print("\n[STEP 2/5] Skipping memory retrieval (first meeting)")
            timing["memory_retrieval"] = 0

        result["historical_context"] = historical_context if historical_context else None

        # =============================================
        # STEP 3: Boris — Executive Summary
        # =============================================
        print("\n[STEP 3/5] Running Boris (Summary Agent)...")
        step_start = time.time()

        boris_output = self.boris.summarize(
            transcript=masked_transcript,
            historical_context=historical_context if historical_context else None,
        )

        timing["boris"] = round(time.time() - step_start, 2)
        print(f"  Done -- summary generated ({timing['boris']}s)")

        if "_parse_error" in boris_output:
            print(f"  [WARN] Boris parse issue: {boris_output['_parse_error']}")

        result["boris_output"] = boris_output

        # =============================================
        # STEP 4: Anna — Action Item Extraction
        # =============================================
        print("\n[STEP 4/5] Running Anna (Action Extractor)...")
        step_start = time.time()

        anna_output = self.anna.extract(transcript=masked_transcript)

        timing["anna"] = round(time.time() - step_start, 2)
        print(
            f"  Done -- {anna_output.get('total_action_items', 0)} action items, "
            f"{anna_output.get('total_decisions', 0)} decisions ({timing['anna']}s)"
        )

        if "_parse_error" in anna_output:
            print(f"  [WARN] Anna parse issue: {anna_output['_parse_error']}")

        result["anna_output"] = anna_output

        # =============================================
        # STEP 5: Max — Significance Scoring & Memory Storage
        # =============================================
        print("\n[STEP 5/5] Running Max (Memory Agent)...")
        step_start = time.time()

        max_output = self.max.evaluate_and_store(
            boris_output=boris_output,
            anna_output=anna_output,
            org_id=org_id,
            meeting_id=meeting_id,
        )

        timing["max"] = round(time.time() - step_start, 2)
        print(
            f"  Done -- stored {max_output.get('stored_count', 0)} items, "
            f"skipped {max_output.get('skipped_count', 0)} "
            f"({timing['max']}s)"
        )

        result["max_output"] = max_output

        # =============================================
        # DONE
        # =============================================
        timing["total"] = round(sum(timing.values()), 2)
        result["timing"] = timing
        result["pipeline_status"] = "completed"

        print(f"\n{'='*60}")
        print(f"  Pipeline Complete -- Total: {timing['total']}s")
        print(f"{'='*60}")

        return result
