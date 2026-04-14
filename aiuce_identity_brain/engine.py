"""
BrainEngine — core knowledge-base engine for Identity Brain.

Design principles:
1. Brain-first lookup: consult() before every response
2. Entity-centric: people / companies / concepts / projects → nodes
3. MECE structure: every file belongs to exactly one wing
4. Write-through: every conversation updates the brain (raw verbatim,
   no summarisation)
5. Markdown filesystem storage (no external DB required)
"""

import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiuce_identity_brain.types import BrainPage, MECEWing

logger = logging.getLogger(__name__)


class BrainEngine:
    """
    Personal brain engine backed by a Markdown file tree.

    Each entity occupies one ``.md`` file inside a wing directory::

        ~/.identity-brain/
        ├── people/
        │   ├── sarah-chen.md
        │   └── marcus-reid.md
        ├── companies/
        │   └── novamind.md
        └── concepts/
            └── mece-taxonomy.md

    Core methods:
    - ``consult()`` — read the brain before responding
    - ``update()``   — write to the brain after a conversation
    - ``dream_cycle()`` — nightly integration pass
    - ``stats()``    — brain health statistics
    """

    def __init__(
        self,
        brain_path: str = "~/.identity-brain",
        consult_threshold: int = 3,
        max_context_chars: int = 8000,
    ):
        self.brain_path = Path(os.path.expanduser(brain_path))
        self.consult_threshold = consult_threshold
        self.max_context_chars = max_context_chars

        # In-memory indexes rebuilt from disk on init
        self._entity_index: Dict[str, BrainPage] = {}   # entity_id → page
        self._name_index: Dict[str, str] = {}           # name/alias → entity_id

        self._ensure_mece_structure()
        self._build_index()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _ensure_mece_structure(self) -> None:
        """Create the MECE directory tree if it does not exist."""
        for wing in MECEWing:
            (self.brain_path / wing.value).mkdir(parents=True, exist_ok=True)

        ignore_path = self.brain_path / ".brainignore"
        if not ignore_path.exists():
            ignore_path.write_text("*.tmp\n__pycache__/\n.git/\n.DS_Store\n")

    def _build_index(self) -> None:
        """Rebuild in-memory indexes by scanning all wing directories."""
        self._entity_index.clear()
        self._name_index.clear()

        for wing in MECEWing:
            wing_dir = self.brain_path / wing.value
            if not wing_dir.exists():
                continue
            for md_file in wing_dir.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                page = BrainPage.parse(content)
                if page and page.entity_id:
                    page.wing = wing
                    self._entity_index[page.entity_id] = page
                    self._name_index[page.title.lower()] = page.entity_id
                    for alias in page.aliases:
                        self._name_index[alias.lower()] = page.entity_id

    # ------------------------------------------------------------------
    # consult — read from the brain
    # ------------------------------------------------------------------

    def consult(
        self,
        query: str,
        max_pages: int = 5,
        require_wing: Optional[MECEWing] = None,
    ) -> List[BrainPage]:
        """
        Query the brain and return the most relevant entity pages.

        Uses deterministic keyword + recency scoring (no LLM required).

        Args:
            query: free-text query string
            max_pages: maximum number of pages to return
            require_wing: restrict search to a specific wing

        Returns:
            List of matching BrainPages, sorted by relevance score
            (highest first).
        """
        query_lower = query.lower()
        words = set(re.findall(r"[\w\u4e00-\u9fff]{2,}", query_lower))

        scored: Dict[str, float] = {}
        wings_to_search = [require_wing] if require_wing else list(MECEWing)

        for wing in wings_to_search:
            for entity_id, page in self._entity_index.items():
                if require_wing and page.wing != require_wing:
                    continue

                score = 0.0

                # 1. Exact alias match (highest weight)
                for alias in [page.title.lower()] + [a.lower() for a in page.aliases]:
                    if alias in query_lower:
                        score += 10.0

                # 2. Keyword overlap
                page_words = set(re.findall(r"[\w\u4e00-\u9fff]{2,}", page.content.lower()))
                overlap = words & page_words
                score += len(overlap) * 0.5

                # 3. Mention frequency (higher count → more relevant)
                score += min(page.mention_count * 0.1, 5.0)

                # 4. Recency bonus (time decay)
                days_ago = (datetime.now() - page.last_mentioned).days
                score += max(0, 2.0 - days_ago * 0.05)

                if score > 0.1:
                    scored[entity_id] = score

        ranked = sorted(scored.items(), key=lambda x: -x[1])
        return [self._entity_index[eid] for eid, _ in ranked[:max_pages]]

    def consult_context(
        self,
        query: str,
        max_chars: Optional[int] = None,
    ) -> str:
        """
        Return ``consult()`` results formatted as a Markdown string
        suitable for injecting into an LLM prompt.

        Args:
            query: free-text query
            max_chars: maximum total characters (default: ``max_context_chars``)

        Returns:
            Markdown-formatted context string, or an empty string if
            no results were found.
        """
        max_chars = max_chars or self.max_context_chars
        pages = self.consult(query)
        if not pages:
            return ""

        chunks: List[str] = []
        total = 0
        for page in pages:
            chunk = f"## [{page.wing.value.upper()}] {page.title}\n{page.content[:500]}"
            if total + len(chunk) > max_chars:
                break
            chunks.append(chunk)
            total += len(chunk)

        header = (
            f"<!-- Identity Brain Context | consulted at "
            f"{datetime.now().isoformat()} | {len(pages)} pages -->\n\n"
        )
        return header + "\n\n".join(chunks)

    # ------------------------------------------------------------------
    # update — write to the brain
    # ------------------------------------------------------------------

    def update(
        self,
        conversation: str,
        entities: Optional[List[Dict[str, str]]] = None,
        wing: MECEWing = MECEWing.GENERAL,
    ) -> List[str]:
        """
        Write conversation content into the brain (raw verbatim, no filtering).

        If ``entities`` is not provided, they are auto-detected from the text.

        Args:
            conversation: raw conversation text to record
            entities: list of entity dicts with keys ``name`` and ``wing``
            wing: default wing for auto-detected entities

        Returns:
            List of absolute paths of the updated/created files.
        """
        if entities is None:
            entities = self._extract_entities(conversation)

        updated_files: List[str] = []
        for entity_def in entities:
            name = entity_def.get("name", "")
            if not name:
                continue

            entity_id = BrainPage.slugify(name)
            wing_str = entity_def.get("wing", wing.value)
            try:
                wing_enum = MECEWing(wing_str)
            except ValueError:
                wing_enum = MECEWing.GENERAL

            page = self._get_or_create_page(entity_id, name, wing_enum)

            # Append raw conversation verbatim
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n---\n**[{timestamp}]**\n\n{conversation.strip()}\n"
            page.content += entry
            page.mention_count += 1

            self._save_page(page)

            # Update in-memory indexes
            self._entity_index[entity_id] = page
            self._name_index[page.title.lower()] = entity_id
            for alias in page.aliases:
                self._name_index[alias.lower()] = entity_id

            updated_files.append(
                str(self.brain_path / wing_enum.value / f"{entity_id}.md")
            )

        return updated_files

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Detect entities in free text using deterministic regex patterns.

        Detects:
        - People: ``FirstName LastName`` or Chinese names with honorifics
        - Companies: names ending with Inc / LLC / Ltd / Corp / 集团 / 公司 etc.
        """
        entities: List[Dict[str, str]] = []

        # Person patterns
        person_patterns = [
            r"([A-Z][a-z]+ [A-Z][a-z]+)",
            r"([\u4e00-\u9fff]{2,4}(?:总|老师|先生|女士|博士|教授|CEO|CTO|CFO|VP))",
        ]
        for pat in person_patterns:
            for match in re.finditer(pat, text):
                name = match.group(1).strip()
                if len(name) >= 2:
                    entities.append({"name": name, "wing": "people"})

        # Company patterns
        company_patterns = [
            r"([A-Z][a-zA-Z]+(?: Inc|LLC|Ltd|Corp|Group|Technologies))",
            r"([\u4e00-\u9fff]{3,15}(?:公司|集团|企业|工作室|实验室))",
        ]
        for pat in company_patterns:
            for match in re.finditer(pat, text):
                name = match.group(1).strip()
                if len(name) >= 2:
                    entities.append({"name": name, "wing": "companies"})

        # Deduplicate
        seen: set = set()
        unique: List[Dict[str, str]] = []
        for e in entities:
            key = (e["name"].lower(), e["wing"])
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique

    def _get_or_create_page(
        self,
        entity_id: str,
        name: str,
        wing: MECEWing,
    ) -> BrainPage:
        """Load an existing page or create a new one."""
        filepath = self.brain_path / wing.value / f"{entity_id}.md"
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            page = BrainPage.parse(content)
            if page:
                page.wing = wing
                return page

        return BrainPage(
            wing=wing,
            entity_id=entity_id,
            title=name.title(),
            aliases=[],
            tags=set(),
            mention_count=0,
            relationships={},
            content="",
            last_mentioned=datetime.now(),
        )

    def _save_page(self, page: BrainPage) -> None:
        """Write a BrainPage to disk."""
        filepath = self.brain_path / page.wing.value / f"{page.entity_id}.md"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(page.to_yaml(), encoding="utf-8")

    # ------------------------------------------------------------------
    # dream_cycle — nightly integration
    # ------------------------------------------------------------------

    def dream_cycle(self, max_entities: int = 20) -> Dict[str, Any]:
        """
        Nightly integration cycle.

        Process:
        1. Entity sweep — rank all entities by mention count / recency
        2. Relationship discovery — link entities seen together
        3. Decision migration — move pages containing decision keywords
           into the DECISIONS wing
        4. Save all changes and rebuild indexes

        Args:
            max_entities: maximum number of top entities to process

        Returns:
            Dict with keys: ``entities_scanned``, ``relationship_updates``,
            ``decisions_migrated``, ``dream_cycle_time``.
        """
        # 1. Entity sweep: top entities by mention + recency
        all_pages = sorted(
            self._entity_index.values(),
            key=lambda p: (p.mention_count, -(datetime.now() - p.last_mentioned).days),
            reverse=True,
        )[:max_entities]

        # 2. Relationship discovery (deterministic heuristic)
        relationship_updates = 0
        for page in all_pages:
            if page.mention_count > 5:
                for other in all_pages[:3]:
                    if other.entity_id == page.entity_id:
                        continue
                    key = "associated"
                    if key not in page.relationships:
                        page.relationships[key] = []
                    if other.entity_id not in page.relationships[key]:
                        page.relationships[key].append(other.entity_id)
                        relationship_updates += 1

        # 3. Decision migration
        migrated: List[str] = []
        decision_keywords = [
            "decided", "decision", "approved", "rejected",
            "决定", "决策",
        ]
        for page in all_pages:
            if page.mention_count > 3 and any(
                kw in page.content.lower() for kw in decision_keywords
            ):
                if page.wing != MECEWing.DECISIONS:
                    old_wing = page.wing
                    page.wing = MECEWing.DECISIONS
                    old_path = self.brain_path / old_wing.value / f"{page.entity_id}.md"
                    new_path = self.brain_path / MECEWing.DECISIONS.value / f"{page.entity_id}.md"
                    if old_path.exists():
                        shutil.move(str(old_path), str(new_path))
                    migrated.append(f"{page.title} ({old_wing.value} → decisions)")

        # 4. Persist and rebuild
        for page in all_pages:
            self._save_page(page)
        self._build_index()

        return {
            "entities_scanned": len(all_pages),
            "relationship_updates": relationship_updates,
            "decisions_migrated": migrated,
            "dream_cycle_time": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # stats — brain health
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """
        Return brain health statistics.

        Returns:
            Dict with keys: ``total_entities``, ``total_mentions``,
            ``by_wing`` (dict of wing → count), ``recent_mentions_7d``,
            ``brain_path``.
        """
        wing_counts: Dict[str, int] = {}
        total_mentions = 0
        recent_count = 0
        cutoff = datetime.now().timestamp() - 7 * 86400

        for page in self._entity_index.values():
            wing_counts[page.wing.value] = wing_counts.get(page.wing.value, 0) + 1
            total_mentions += page.mention_count
            if page.last_mentioned.timestamp() > cutoff:
                recent_count += 1

        return {
            "total_entities": len(self._entity_index),
            "total_mentions": total_mentions,
            "by_wing": wing_counts,
            "recent_mentions_7d": recent_count,
            "brain_path": str(self.brain_path),
        }
