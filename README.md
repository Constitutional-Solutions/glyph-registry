# glyph-registry

**FSOU-compliant base-144k glyph registry** — production Python package.

> Schema spec: Pages 2–3 (Sections 9–10, 13, 15), Page 6 (Sections 24–25)

---

## Architecture

```
glyph_registry/
├── __init__.py     — public API surface
├── types.py        — GlyphCategory, GlyphPayload, Glyph144k, OuterContext
├── registry.py     — GlyphRegistry (full CRUD + FSOU audit)
└── radix.py        — RadixCore, Digit1440000
tests/
├── test_types.py
├── test_registry.py
└── test_radix.py
```

---

## Quick start

```python
from glyph_registry import GlyphRegistry, Glyph144k, GlyphCategory, GlyphPayload

reg = GlyphRegistry()

# Add
reg.add_glyph(Glyph144k(
    id=1,
    code="GEO_TETRA_A",
    category=GlyphCategory.GEOMETRY,
    description="Base tetrahedron cell A",
    geometry_payload=GlyphPayload(type="tetrahedron", data={"space": "R3"}),
))

# Get
g = reg.get_glyph(1)
print(g.code)           # GEO_TETRA_A

# Update (FSOU-audited)
reg.update_glyph(1, description="Updated description")

# Search
results = reg.search_by_category(GlyphCategory.GEOMETRY)
results = reg.search_by_description("tetrahedron")

# Export / import
jsonl = reg.export_jsonl()          # one compact JSON record per line
reg2 = GlyphRegistry()
reg2.import_jsonl(jsonl)

# Full snapshot (for persistence)
import json
snap = reg.export_snapshot()
reg3 = GlyphRegistry.from_snapshot(snap)

# Stats
print(reg.stats())
```

---

## Radix utilities

```python
from glyph_registry import RadixCore, Digit1440000

r = RadixCore()

# Base-144k conversion
digits = r.to_base(1_234_567, 144_000)      # [8, 81567]
back   = r.from_base(digits, 144_000)       # 1234567
enc    = r.encode_number(1_234_567, 144_000) # "000008-081567"
dec    = r.decode_number(enc, 144_000)       # 1234567

# Hierarchical base-1.44M digit
d = Digit1440000(outer=3, inner=81_567)
print(d.encode())       # "3:081567"
print(d.flat_value)     # 513567
d2 = Digit1440000.decode("3:081567")
assert d == d2
```

---

## FSOU audit log

Every mutation records a hash-chained entry in `reg.change_history`:

```python
{
    "action":      "ADD_GLYPH",          # ADD / UPDATE / DELETE / ADD_CONTEXT / ...
    "timestamp":   "2026-02-21T04:25:00+00:00",
    "hash_before": "a1b2c3...",
    "hash_after":  "d4e5f6...",
    "glyph_id":    1,
    "code":        "GEO_TETRA_A"
}
```

The registry hash is `Blake2b-256` over all glyphs + outer contexts (sorted JSON).

---

## Outer contexts (base-1.44M, Section 25)

10 default contexts are created on `__init__`:

| outer_id | code            | description                     |
|----------|-----------------|---------------------------------|
| 0        | CTX_BASE        | Default base context            |
| 1        | CTX_GEOMETRY    | Geometry-dominant context       |
| 2        | CTX_RESEARCH    | Research / experimental context |
| 3        | CTX_HARMONIC    | Harmonics-dominant context      |
| 4        | CTX_PROTOCOL    | Protocol state context          |
| 5        | CTX_STORY       | Narrative / story context       |
| 6        | CTX_TEMPORAL    | Temporal / chronos context      |
| 7        | CTX_SYMBOLIC    | Symbolic / glyph-language       |
| 8        | CTX_BIOMETRIC   | Biometric / sensor context      |
| 9        | CTX_SOVEREIGN   | Sovereign / governance context  |

---

## Running tests

```bash
pip install -e .[dev]
pytest -v
```

---

## What changed from the notebook prototype

| Issue | Fix |
|---|---|
| Missing imports (`Dict`, `datetime`) | Added via `from __future__ import annotations` + explicit imports |
| JSONL export produced multi-line records | `to_json()` defaults to compact single-line mode |
| `from_dict` crashed on payload dicts | `GlyphPayload.from_dict` reconstructs objects properly |
| No `update_glyph` | Added with full index maintenance + audit |
| No `delete_glyph` | Added with full index cleanup + audit |
| No `import_jsonl` | Added with optional overwrite mode |
| No snapshot persistence | `export_snapshot` / `from_snapshot` added |
| Outer contexts only initialised, never editable | `add_outer_context` / `update_outer_context` added |
| Only 6 default contexts | Expanded to full 10 (outer_ids 0–9) |
