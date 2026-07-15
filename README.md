> ⚠️ **Deprecated — legacy AIUCE family.** This repo is being consolidated into **SONUV** / **AIOBR** / a unified history archive (2026). No new work is accepted. Current status: **[aiuce.com](https://aiuce.com)**. _Marked 2026-07-15._
>
> _本仓库属旧 AIUCE 体系，正整合进 SONUV / AIOBR / 统一历史归档，不再接受新改动；最新状态见 aiuce.com。_

# Identity Brain

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Paradigm](https://img.shields.io/badge/Paradigm-Brain--first%20PKM-purple.svg)]()

**A brain-first, entity-centric personal knowledge management library.**

Persistent personal knowledge base built on a Markdown file tree. Follows the **brain-first** protocol: consult before responding, update after every conversation, dream nightly.

## Installation

```bash
pip install .
# or development mode
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
