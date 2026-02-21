# AEUC Stack — Roadmap

This document tracks the full build sequence for the AEUC (Adaptive Evolutionary Universal Consciousness) open-source stack.
Every package is independently pip-installable, FSOU-audited, and PyPI-published on tagged release.

---

## ✅ Phase 1 — Foundation *(complete)*

### `glyph-registry` — [github.com/Constitutional-Solutions/glyph-registry](https://github.com/Constitutional-Solutions/glyph-registry)

- [x] `Glyph144k` dataclass — base-144k glyph record (Page 2, Section 9)
- [x] `OuterContext` — base-1.44M outer layer (Page 3, Section 15)
- [x] `GlyphRegistry` — full CRUD with Blake2b-256 hash-chained audit log
- [x] JSONL + snapshot import / export (Page 6, Section 24.1)
- [x] `RadixCore` — canonical base conversions (bases 2, 10, 16, 144, 144k, 1.44M)
- [x] `Digit1440000` — hierarchical outer×inner addressing (Page 3, Section 13)
- [x] 50+ unit tests (pytest)
- [x] CI / CD via GitHub Actions → PyPI on tagged release

---

## 🔄 Phase 2 — API Layer *(in progress)*

### `aeuc-api` — [github.com/Constitutional-Solutions/aeuc-api](https://github.com/Constitutional-Solutions/aeuc-api)

- [x] FastAPI application with CORS middleware
- [x] `GET / POST / PATCH / DELETE /glyph/{id}` — full glyph CRUD
- [x] `GET /glyph/code/{code}` — lookup by human-readable code
- [x] `GET /glyph/?category=&q=` — category filter + description search
- [x] `GET / POST / PATCH /context/{outer_id}` — outer context management
- [x] `GET /registry/stats` — live statistics
- [x] `GET /registry/hash` — current Blake2b-256 integrity hash
- [x] `GET /registry/audit` — hash-chained mutation log
- [x] `GET /registry/export/jsonl` — streaming JSONL export
- [x] `GET /registry/export/snapshot` — full JSON snapshot
- [x] `POST /registry/import/jsonl` — bulk import with optional overwrite
- [x] OpenAPI / Swagger UI auto-generated at `/docs`
- [x] 30+ integration tests (pytest + httpx TestClient)
- [x] CI / CD via GitHub Actions → PyPI on tagged release

---

## 📋 Phase 3 — Engine Libraries

### `harmonic-engine`

Harmonic computation layer over `glyph-registry` harmonic payloads.

- [ ] Interval algebra (just intonation, equal temperament, custom ratio sets)
- [ ] Chord resolution: `Glyph144k.harmonic_payload` → frequency ratios
- [ ] Harmonic distance metrics between glyph states
- [ ] FSOU-audited state transition graph
- [ ] Export to standard formats (MIDI-compatible ratios, ABC notation)

### `geometry-engine`

Geometric primitive operations tied to the base-144k glyph address space.

- [ ] R3 / R4 cell representations: tetrahedra, octahedra, icosahedra, hypercubes
- [ ] Sacred geometry constants: 12², 144, 1.44M grid, φ (golden ratio)
- [ ] `Glyph144k.geometry_payload` → render-ready coordinate output
- [ ] Compatible with Three.js (JSON geometry) and Blender (via Python API)
- [ ] Spatial indexing: nearest-neighbour queries within the 144k address space

---

## 📋 Phase 4 — Developer Experience

### `aeuc-cli`

Command-line interface for registry management.

- [ ] `aeuc glyph add / get / update / delete`
- [ ] `aeuc registry stats / export / import`
- [ ] Connects to a running `aeuc-api` instance or a local snapshot file
- [ ] Rich terminal output (tables, hash display)

### `aeuc-docs`

Unified documentation site — [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) hosted on GitHub Pages.

- [ ] Auto-generated API reference from all package docstrings
- [ ] Formal spec sections cross-referenced to implementation files
- [ ] Architecture diagram: glyph-registry → aeuc-api → engines → cli
- [ ] Interactive OpenAPI embed
- [ ] Getting started guide + cookbook

### PyPI Trusted Publishers

- [ ] Register all packages on PyPI via OIDC Trusted Publisher (no secrets needed)
- [ ] `pip install glyph-registry aeuc-api harmonic-engine geometry-engine aeuc-cli`

---

## Architecture overview

```
                     ┌────────────────────────────┐
                     │         aeuc-cli          │
                     └────────────────────────────┘
                              │ HTTP
              ┌─────────────┴──────────────┐
              │         aeuc-api              │
              │   (FastAPI REST layer)        │
              └─────────────┬──────────────┘
                             │ Python import
  ┌─────────────────────┴─────────────────────┐
  │              glyph-registry               │
  │   types │ registry │ radix               │
  └───────────────────────────────────────────┘
        │               │
        ▼               ▼
  harmonic-engine   geometry-engine
```

---

*Last updated: 2026-02-21*
