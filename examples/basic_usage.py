"""
Basic usage examples for aiuce-identity-brain.

Run directly:
    python examples/basic_usage.py

Or in a Python session:
    >>> from examples.basic_usage import run
    >>> run()
"""

import tempfile
from pathlib import Path

from aiuce_identity_brain import IdentityBrain, BrainEngine, MECEWing


def run():
    # Use a temporary directory for this demo (not ~/.identity-brain)
    with tempfile.TemporaryDirectory() as tmp:
        brain_path = str(Path(tmp) / "brain")
        brain = IdentityBrain(brain_path=brain_path)

        # ── 1. Store a conversation ──────────────────────────────────────
        updated = brain.update(
            (
                "Caught up with Sarah Chen over video call. She is the CEO of Novamind "
                "and they just closed their Series B at $40M. The round was led by "
                "Sequoia Capital. Next step: intro call with their CTO Marcus Reid "
                "to discuss technical integration."
            ),
            entities=[
                {"name": "Sarah Chen", "wing": "people"},
                {"name": "Novamind", "wing": "companies"},
                {"name": "Sequoia Capital", "wing": "companies"},
                {"name": "Marcus Reid", "wing": "people"},
            ],
        )
        print(f"Updated {len(updated)} files:")
        for f in updated:
            print(f"  • {Path(f).name}")

        # ── 2. Consult the brain before responding ───────────────────────
        ctx = brain.consult("Sarah Chen Novamind")
        print("\n--- Brain Context ---")
        print(ctx or "(no results)")

        # ── 3. Persist a second interaction ──────────────────────────────
        brain.update(
            "Intro call with Marcus Reid. He mentioned the engineering team uses "
            "Python + LangChain. Infrastructure runs on AWS. Key concern: latency "
            "on their embedding pipeline.",
            entities=[
                {"name": "Marcus Reid", "wing": "people"},
                {"name": "Novamind", "wing": "companies"},
            ],
        )

        # ── 4. Run the nightly dream cycle ───────────────────────────────
        report = brain.dream()
        print("\n--- Dream Cycle Report ---")
        for k, v in report.items():
            print(f"  {k}: {v}")

        # ── 5. Brain health check ────────────────────────────────────────
        stats = brain.stats()
        print("\n--- Brain Stats ---")
        print(f"  Total entities : {stats['total_entities']}")
        print(f"  Total mentions : {stats['total_mentions']}")
        print(f"  Entities by wing:")
        for wing, count in stats["by_wing"].items():
            print(f"    {wing:12s}: {count}")

        # ── 6. Low-level engine access ────────────────────────────────────
        print("\n--- Low-level BrainEngine demo ---")
        engine = BrainEngine(brain_path=brain_path)
        results = engine.consult("Marcus Reid", require_wing=MECEWing.PEOPLE)
        for page in results:
            print(f"  [{page.wing.value}] {page.title} (mentions: {page.mention_count})")

        print("\n✅ All examples completed successfully.")


if __name__ == "__main__":
    run()
