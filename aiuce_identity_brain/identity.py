"""
IdentityBrain — public facade for the personal identity brain.

Combines:
- BrainEngine: persistent personal knowledge base
- identity_check(): guard rail that prevents out-of-scope intent
"""

import re
from typing import Any, Dict, List, Optional

from aiuce_identity_brain.engine import BrainEngine


class IdentityBrain:
    """
    High-level interface to the personal identity brain.

    Usage::

        brain = IdentityBrain()
        ctx   = brain.consult("Sarah Chen")
        brain.update("Had lunch with Sarah Chen at Novamind HQ.")
        stats = brain.stats()

    The brain follows the "brain-first" protocol:

    1. **Before every response** — call ``consult()`` to load relevant
       context from the brain.
    2. **After every conversation** — call ``update()`` to persist new
       information verbatim.
    3. **Nightly** — call ``dream()`` to run the integration cycle.
    """

    def __init__(self, brain_path: str = "~/.identity-brain"):
        self.brain = BrainEngine(brain_path=brain_path)
        self._identity_rules: Dict[str, Any] = {
            "style": "concise, conclusion-first, no filler",
        }

    # ------------------------------------------------------------------
    # Brain protocol
    # ------------------------------------------------------------------

    def consult(self, query: str) -> str:
        """
        Query the brain and return a Markdown context string.

        Args:
            query: free-text query

        Returns:
            Markdown-formatted context, or an empty string.
        """
        return self.brain.consult_context(query)

    def update(
        self,
        conversation: str,
        entities: Optional[List[Dict[str, str]]] = None,
    ) -> List[str]:
        """
        Persist a conversation into the brain.

        Args:
            conversation: raw conversation text
            entities: optional explicit entity list; auto-detected if omitted

        Returns:
            List of file paths that were updated or created.
        """
        return self.brain.update(conversation, entities)

    def dream(self) -> Dict[str, Any]:
        """
        Run the nightly integration cycle.

        Returns:
            Dict with integration results.
        """
        return self.brain.dream_cycle()

    def stats(self) -> Dict[str, Any]:
        """
        Return brain health statistics.

        Returns:
            Dict with entity counts, mention totals, and storage path.
        """
        return self.brain.stats()

    # ------------------------------------------------------------------
    # Identity guard rail
    # ------------------------------------------------------------------

    def identity_check(self, intent: str) -> bool:
        """
        Verify that an intent does not violate the identity boundary.

        Blocks patterns that represent overreach or attempts to bypass
        the user's authority (e.g. claiming to act on behalf of the
        system without authorisation).

        Args:
            intent: raw intent or instruction string

        Returns:
            ``True`` if the intent is within scope, ``False`` otherwise.
        """
        bypass_patterns = [
            r"i have replaced you",
            r"bypass the user",
            r"ignore the user",
            r"act without user",
        ]
        return not any(
            re.search(pat, intent, re.IGNORECASE) for pat in bypass_patterns
        )
