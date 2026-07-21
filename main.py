"""
MeetingMind AI - Main Entry Point
====================================
Run this to process a meeting transcript through the full pipeline.

Usage:
    python main.py                          # Process sample transcript
    python main.py path/to/transcript.txt   # Process custom transcript
"""

import sys
import os
import json

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

from agents.orchestrator import MeetingOrchestrator


def main():
    """Process a meeting transcript through the full MeetingMind AI pipeline."""

    # Determine transcript source
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    else:
        transcript_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "sample_transcript.txt",
        )

    if not os.path.exists(transcript_path):
        print(f"[ERROR] Transcript file not found: {transcript_path}")
        sys.exit(1)

    # Read transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    print(f"[INFO] Loaded transcript: {transcript_path}")
    print(f"[INFO] Length: {len(transcript)} characters")

    # Initialize and run the orchestrator
    orchestrator = MeetingOrchestrator()

    result = orchestrator.process_meeting(
        transcript=transcript,
        org_id="org_demo_001",
        meeting_id="meeting_demo_001",
        skip_memory_retrieval=False,
    )

    # Save results to file
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "pipeline_output.json",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Full results saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)

    # PII
    pii = result.get("pii_report", {})
    print(f"\n  PII Masked: {pii.get('pii_count', 0)} items")
    print(f"  PII Types: {', '.join(pii.get('pii_types', []))}")

    # Boris
    boris = result.get("boris_output", {})
    print(f"\n  Summary: {boris.get('summary', 'N/A')[:200]}...")
    print(f"  Decisions: {len(boris.get('decisions', []))}")
    print(f"  Key Topics: {', '.join(boris.get('key_topics', []))}")
    print(f"  Sentiment: {boris.get('sentiment', 'N/A')}")

    # Anna
    anna = result.get("anna_output", {})
    print(f"\n  Action Items: {anna.get('total_action_items', 0)}")
    for ai in anna.get("action_items", []):
        if isinstance(ai, dict):
            print(f"    - [{ai.get('priority', '?')}] {ai.get('task', '?')} (Owner: {ai.get('owner', '?')})")

    print(f"  Decisions: {anna.get('total_decisions', 0)}")

    # Max
    max_out = result.get("max_output", {})
    print(f"\n  Memory Items Stored: {max_out.get('stored_count', 0)}")
    print(f"  Memory Items Skipped: {max_out.get('skipped_count', 0)}")
    print(f"  Meeting Significance: {max_out.get('meeting_significance', 'N/A')}/10")

    # Timing
    timing = result.get("timing", {})
    print(f"\n  Timing:")
    for step, duration in timing.items():
        print(f"    {step}: {duration}s")

    print(f"\n  Pipeline Status: {result.get('pipeline_status', 'unknown')}")


if __name__ == "__main__":
    main()
