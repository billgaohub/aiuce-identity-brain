# Identity Brain

A brain-first, entity-centric personal knowledge management library.

## Overview

`aiuce-identity-brain` is a persistent personal knowledge base built on a Markdown file tree. It follows the **brain-first** protocol:

1. **Consult before responding** — `brain.consult(query)` loads relevant context.
2. **Update after every conversation** — `brain.update(text)` writes verbatim (no summarisation).
3. **Dream nightly** — `brain.dream()` runs the integration cycle.

Each piece of knowledge lives as a single Markdown file organised under one of 11 MECE (Mutually Exclusive, Collectively Exhaustive) wings.

## Installation

```bash
pip install .
```

Or in development mode:

```bash
pip install -e .
```

## Quick Start

```python
from aiuce_identity_brain import IdentityBrain

brain = IdentityBrain()

# Consult the brain before responding
ctx = brain.consult("Sarah Chen")
print(ctx)

# After a conversation, persist it
brain.update(
    "Had lunch with Sarah Chen at Novamind HQ. She mentioned their Series B is closing next month.",
    entities=[{"name": "Sarah Chen", "wing": "people"}, {"name": "Novamind", "wing": "companies"}],
)

# Run the nightly integration cycle
report = brain.dream()
print(report)

# Check brain health
print(brain.stats())
```

## MECE Wings

| Wing | Description |
|------|-------------|
| `people` | Everyone you know |
| `companies` | Companies you interact with |
| `concepts` | Knowledge topics and ideas |
| `projects` | Active projects |
| `meetings` | Meeting records |
| `sources` | Original data and web clips |
| `decisions` | Important decisions |
| `experiences` | Lessons from success and failure |
| `tools` | Tools and services you use |
| `habits` | Personal habits and preferences |
| `general` | Miscellaneous |

## Architecture

```
IdentityBrain           ← public facade
  └── BrainEngine       ← core engine
        ├── consult()   ← read brain before responding
        ├── update()    ← write brain after conversation
        ├── dream_cycle()  ← nightly integration
        └── stats()     ← health check
```

## Storage

All data lives under `~/.identity-brain/`:

```
~/.identity-brain/
├── people/
│   └── sarah-chen.md
├── companies/
│   └── novamind.md
└── concepts/
    └── mece-taxonomy.md
```

## License

MIT © 2026 Bill Gao
