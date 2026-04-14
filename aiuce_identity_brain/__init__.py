"""
AIUCE Identity Brain — Personal Knowledge Base Engine
A brain-first, entity-centric personal knowledge management system.

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │  IdentityBrain                                              │
  │   └── BrainEngine (core)                                    │
  │       ├── EntityGraph (Markdown file storage)               │
  │       ├── MECESchema (MECE category structure)              │
  │       └── DreamCycle (nightly integration)                  │
  └─────────────────────────────────────────────────────────────┘
"""

from aiuce_identity_brain.identity import IdentityBrain
from aiuce_identity_brain.engine import BrainEngine
from aiuce_identity_brain.types import MECEWing, BrainPage, EntityRef

__version__ = "0.1.0"
__all__ = [
    "IdentityBrain",
    "BrainEngine",
    "MECEWing",
    "BrainPage",
    "EntityRef",
]
