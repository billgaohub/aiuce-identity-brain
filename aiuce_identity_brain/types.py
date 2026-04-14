"""
Data types and models for the Identity Brain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
import re


class MECEWing(Enum):
    """
    MECE Wing — top-level category for every entity.

    MECE = Mutually Exclusive, Collectively Exhaustive.
    Every entity belongs to exactly one wing; wings together
    cover the entire space of personal knowledge.
    """

    PEOPLE = "people"
    COMPANIES = "companies"
    CONCEPTS = "concepts"
    PROJECTS = "projects"
    MEETINGS = "meetings"
    SOURCES = "sources"
    DECISIONS = "decisions"
    EXPERIENCES = "experiences"
    TOOLS = "tools"
    HABITS = "habits"
    GENERAL = "general"

    @classmethod
    def for_file(cls, filepath: str) -> "MECEWing":
        """Infer the wing from a file path."""
        path_lower = filepath.lower()
        for wing in cls:
            if f"/{wing.value}/" in path_lower or path_lower.endswith(f"/{wing.value}"):
                return wing
        return cls.GENERAL


@dataclass
class EntityRef:
    """
    Lightweight reference to an entity stored in the brain.

    Tracks metadata used for ranking during consult (mention count,
    recency, aliases) without loading the full page content.
    """

    name: str
    wing: MECEWing
    aliases: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    last_mentioned: datetime = field(default_factory=datetime.now)
    mention_count: int = 0
    relationships: Dict[str, List[str]] = field(default_factory=dict)

    def canonical_name(self) -> str:
        """Return the canonical display name (title-cased)."""
        return self.name.strip().title()

    def mentions(self, delta: int = 1) -> int:
        """Increment mention counter and update timestamp."""
        self.mention_count += delta
        self.last_mentioned = datetime.now()
        return self.mention_count


@dataclass
class BrainPage:
    """
    A single entity page stored as a Markdown file.

    File format::

        ---
        wing: people
        entity: sarah-chen
        title: Sarah Chen
        aliases: ["Sarah", "Sarah Chen"]
        tags: ["founder", "ai", "stanford"]
        mention_count: 42
        last_mentioned: 2026-04-14
        ---
        # Sarah Chen

        ## Background
        ...

        ## Relationships
        - works_with: marcus-reid, priya-patel
        - founded: novamind

        ## Notes
        ...
    """

    wing: MECEWing
    entity_id: str
    title: str
    aliases: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    mention_count: int = 0
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    content: str = ""
    last_mentioned: datetime = field(default_factory=datetime.now)
    metadata_yaml: str = ""

    @staticmethod
    def slugify(name: str) -> str:
        """Convert a name into a URL-safe slug."""
        s = name.lower().strip()
        s = re.sub(r"/", "-", s)          # convert slashes to dashes before stripping
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_]+", "-", s)
        return s

    @staticmethod
    def parse(content: str) -> Optional["BrainPage"]:
        """Parse a BrainPage from a Markdown file body."""
        if "---\n" not in content:
            return None
        parts = content.split("---\n", 2)
        if len(parts) < 3:
            return None
        # parts[0] may be empty when frontmatter starts with "---\n" (blank line after opening ---).
        # The actual YAML block lives in parts[1] and the body in parts[2].
        yaml_block = parts[1] if parts[0] == "" else parts[0]
        _, _, body = parts
        page = BrainPage(
            wing=MECEWing.GENERAL,
            entity_id="",
            title="",
            content=body.strip(),
        )
        for line in yaml_block.split("\n"):
            if ": " not in line and ":" not in line:
                continue
            key, _, val = line.partition(": ")
            if not val:
                key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("[]\"'")
            if key == "wing":
                try:
                    page.wing = MECEWing(val)
                except ValueError:
                    pass
            elif key == "entity":
                page.entity_id = val
            elif key == "aliases":
                page.aliases = [
                    a.strip()
                    for a in val.replace("[", "").replace("]", "").split(",")
                    if a.strip()
                ]
            elif key == "tags":
                page.tags = {
                    t.strip()
                    for t in val.replace("[", "").replace("]", "").split(",")
                    if t.strip()
                }
            elif key == "mention_count":
                try:
                    page.mention_count = int(val)
                except ValueError:
                    pass
            elif key == "title":
                page.title = val
        return page

    def to_yaml(self) -> str:
        """Render the page as a Markdown string with YAML frontmatter."""
        aliases_str = "[" + ", ".join(f'"{a}"' for a in self.aliases) + "]"
        tags_str = "[" + ", ".join(f'"{t}"' for t in self.tags) + "]"
        return (
            f"---\n"
            f"wing: {self.wing.value}\n"
            f"entity: {self.entity_id}\n"
            f"title: {self.title}\n"
            f"aliases: {aliases_str}\n"
            f"tags: {tags_str}\n"
            f"mention_count: {self.mention_count}\n"
            f"last_mentioned: {self.last_mentioned.strftime('%Y-%m-%d')}\n"
            f"---\n"
            f"# {self.title}\n\n"
            f"{self.content}"
        )
