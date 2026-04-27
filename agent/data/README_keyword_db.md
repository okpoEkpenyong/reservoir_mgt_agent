# Reservoir Keyword Database v3.0

## Files
- **`reservoir_keywords_db.json`** — Main groundtruth database (3.8 MB)
- **`keyword_query.py`** — Python query interface for your agent

## Database Coverage
| Metric | Count |
|--------|-------|
| Total unique keywords | 1,673 |
| In both ECLIPSE + OPM | 1,018 |
| ECLIPSE-only | 533 |
| OPM-only | 122 |

## OPM Flow Support
| Status | Count |
|--------|-------|
| ✅ Fully supported | 569 |
| ❌ Not supported | 524 |
| ⚠️ Ignored (no effect) | 46 |
| 🔶 Partial | 1 |
| ❓ Unknown / ECLIPSE-only | 533 |

## Section Keyword Counts
| Section | Keywords |
|---------|----------|
| RUNSPEC | 246 |
| GRID | 252 |
| EDIT | 72 |
| PROPS | 633 |
| REGIONS | 96 |
| SOLUTION | 154 |
| SUMMARY | 41 |
| SCHEDULE | 430 |
| OPTIMIZE | 8 |
| GLOBAL | 12 |

## Sources
- ECLIPSE Reference Manual  (SLB)
- OPM Flow Reference Manual 2025-10 (Equinor/Open Porous Media)
- ECLIPSE Technical Description (SLB)

## Quick Start

```python
from keyword_query import KeywordDB

db = KeywordDB("reservoir_keywords_db.json")

# Ground-truth answer for your agent
print(db.agent_answer("WELSPECS", verbose=True))

# Check OPM support
print(db.check_opm_support("COMPDAT"))

# Search
results = db.search("aquifer Carter Tracy")

# All SCHEDULE keywords
schedule_kws = db.by_section("SCHEDULE")

# OPM compatibility report
print(db.export_opm_compatibility_report())
```

## Per-Keyword Schema
```json
{
  "keyword": "WELSPECS",
  "title": "General specification data for wells",
  "sections": ["SCHEDULE"],
  "description": "Full description from ECLIPSE manual...",
  "opm_description": "Description from OPM manual...",
  "items": [{"item": 1, "text": "Well name..."}],
  "units": {"METRIC": "m", "FIELD": "ft"},
  "defaults": ["OPEN", "STD"],
  "example": "WELSPECS\n  'PROD1' 'G1' 10 10 1* 'OIL' /\n/",
  "eclipse_100": true,
  "eclipse_300": true,
  "opm_supported": true,
  "opm_notes": "",
  "opm_parameters": [{"no": 1, "name": "WELNAME", "description": "...", "default": "None"}],
  "tech_context": "Context snippet from Technical Description...",
  "sources": ["ECLIPSE_Reference_2022.2", "OPM_Flow_2025-10"]
}
```
