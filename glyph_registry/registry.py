"""
registry.py — GlyphRegistry: production FSOU-compliant glyph store.

Features
--------
- Full CRUD  (add / get / update / delete)
- Hash-chained audit log  (Blake2b-256)
- Reverse lookup indices  (by code, by category)
- Full-text search over description fields
- JSONL import / export  (Page 6, Section 24.1)
- Snapshot export / restore  (for persistence)
- OuterContext CRUD  (Page 6, Section 25)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .types import Glyph144k, GlyphCategory, OuterContext


# ── Default outer contexts (Page 6, Section 25) ───────────────────────────────

_DEFAULT_CONTEXTS: List[tuple] = [
    (0, "CTX_BASE",      "Default base context"),
    (1, "CTX_GEOMETRY",  "Geometry-dominant context"),
    (2, "CTX_RESEARCH",  "Research / experimental context"),
    (3, "CTX_HARMONIC",  "Harmonics-dominant context"),
    (4, "CTX_PROTOCOL",  "Protocol state context"),
    (5, "CTX_STORY",     "Narrative / story context"),
    (6, "CTX_TEMPORAL",  "Temporal / chronos context"),
    (7, "CTX_SYMBOLIC",  "Symbolic / glyph-language context"),
    (8, "CTX_BIOMETRIC", "Biometric / sensor context"),
    (9, "CTX_SOVEREIGN", "Sovereign / governance context"),
]


# ── Registry ──────────────────────────────────────────────────────────────────

class GlyphRegistry:
    """
    Production glyph database with FSOU audit compliance.

    Storage
    -------
    glyphs_144k     : {id → Glyph144k}     sparse; grows on demand
    outer_contexts  : {outer_id → OuterContext}

    Indices  (maintained automatically on every mutation)
    -------
    code_to_id      : {code → id}
    category_index  : {GlyphCategory → [id, …]}

    FSOU integrity
    --------------
    Every mutation appends a change-history entry with:
        action, timestamp, hash_before, hash_after
    Registry hash = Blake2b-256( sorted JSON of all glyphs + contexts ).
    """

    VERSION = "1.0.0"

    def __init__(self) -> None:
        # Primary tables
        self.glyphs_144k:    Dict[int, Glyph144k]     = {}
        self.outer_contexts: Dict[int, OuterContext]  = {}

        # Reverse indices
        self.code_to_id:     Dict[str, int]                  = {}
        self.category_index: Dict[GlyphCategory, List[int]] = {
            cat: [] for cat in GlyphCategory
        }

        # Audit
        self.change_history: List[Dict[str, Any]] = []
        self.current_hash:   str = ""

        # Bootstrap
        self._init_default_contexts()
        self._update_hash()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def _update_hash(self) -> None:
        """Recompute Blake2b-256 hash over all glyphs and contexts."""
        content = json.dumps(
            {
                "glyphs":   {str(k): v.to_dict() for k, v in self.glyphs_144k.items()},
                "contexts": {str(k): v.to_dict() for k, v in self.outer_contexts.items()},
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        self.current_hash = hashlib.blake2b(
            content.encode(), digest_size=32
        ).hexdigest()

    def _audit(self, action: str, old_hash: str, **meta: Any) -> None:
        self.change_history.append(
            {
                "action":      action,
                "timestamp":   self._now(),
                "hash_before": old_hash,
                "hash_after":  self.current_hash,
                **meta,
            }
        )

    def _init_default_contexts(self) -> None:
        for outer_id, code, desc in _DEFAULT_CONTEXTS:
            ctx = OuterContext(outer_id=outer_id, code=code, description=desc)
            self.outer_contexts[outer_id] = ctx

    # ── GLYPH CRUD ─────────────────────────────────────────────────────────────

    def add_glyph(self, glyph: Glyph144k) -> int:
        """Insert a new glyph. Raises ValueError on duplicate id or code."""
        if glyph.id in self.glyphs_144k:
            raise ValueError(f"Glyph ID {glyph.id} already exists")
        if glyph.code in self.code_to_id:
            raise ValueError(f"Glyph code '{glyph.code}' already exists")

        old_hash = self.current_hash
        self.glyphs_144k[glyph.id]  = glyph
        self.code_to_id[glyph.code] = glyph.id
        self.category_index[glyph.category].append(glyph.id)
        self._update_hash()
        self._audit("ADD_GLYPH", old_hash, glyph_id=glyph.id, code=glyph.code)
        return glyph.id

    def get_glyph(self, glyph_id: int) -> Optional[Glyph144k]:
        """Retrieve a glyph by numeric ID. Returns None if not found."""
        return self.glyphs_144k.get(glyph_id)

    def get_glyph_by_code(self, code: str) -> Optional[Glyph144k]:
        """Retrieve a glyph by human-readable code."""
        glyph_id = self.code_to_id.get(code)
        return self.glyphs_144k.get(glyph_id) if glyph_id is not None else None

    def update_glyph(self, glyph_id: int, **updates: Any) -> Glyph144k:
        """
        Update scalar fields on an existing glyph (FSOU-audited).

        Mutable   : code, description, category,
                    geometry_payload, harmonic_payload,
                    protocol_payload, version
        Immutable : id, timestamp
        """
        _IMMUTABLE = {"id", "timestamp"}
        if glyph_id not in self.glyphs_144k:
            raise KeyError(f"Glyph ID {glyph_id} not found")

        old_hash = self.current_hash
        glyph = self.glyphs_144k[glyph_id]
        d = glyph.to_dict()
        d["category"] = glyph.category  # keep enum for from_dict

        for key, val in updates.items():
            if key in _IMMUTABLE:
                raise ValueError(f"Field '{key}' is immutable")
            if key not in d:
                raise ValueError(f"Unknown field: '{key}'")

            if key == "code" and val != glyph.code:
                if val in self.code_to_id:
                    raise ValueError(f"Code '{val}' already taken")
                del self.code_to_id[glyph.code]
                self.code_to_id[val] = glyph_id

            if key == "category":
                new_cat = GlyphCategory(val) if isinstance(val, str) else val
                self.category_index[glyph.category].remove(glyph_id)
                self.category_index[new_cat].append(glyph_id)
                val = new_cat

            d[key] = val

        updated = Glyph144k.from_dict(d)
        self.glyphs_144k[glyph_id] = updated
        self._update_hash()
        self._audit("UPDATE_GLYPH", old_hash, glyph_id=glyph_id, fields=list(updates.keys()))
        return updated

    def delete_glyph(self, glyph_id: int) -> Glyph144k:
        """Remove a glyph and clean all indices. Returns the deleted record."""
        if glyph_id not in self.glyphs_144k:
            raise KeyError(f"Glyph ID {glyph_id} not found")

        old_hash = self.current_hash
        glyph = self.glyphs_144k.pop(glyph_id)
        del self.code_to_id[glyph.code]
        self.category_index[glyph.category].remove(glyph_id)
        self._update_hash()
        self._audit("DELETE_GLYPH", old_hash, glyph_id=glyph_id, code=glyph.code)
        return glyph

    # ── SEARCH ─────────────────────────────────────────────────────────────────

    def search_by_category(self, category: GlyphCategory) -> List[Glyph144k]:
        """Return all glyphs in a given category, sorted by id."""
        return [
            self.glyphs_144k[gid]
            for gid in sorted(self.category_index.get(category, []))
        ]

    def search_by_description(self, query: str, *, case_sensitive: bool = False) -> List[Glyph144k]:
        """Full-text substring search over description fields."""
        q = query if case_sensitive else query.lower()
        results = [
            g for g in self.glyphs_144k.values()
            if q in (g.description if case_sensitive else g.description.lower())
        ]
        return sorted(results, key=lambda g: g.id)

    # ── OUTER CONTEXT CRUD ─────────────────────────────────────────────────────

    def get_outer_context(self, outer_id: int) -> Optional[OuterContext]:
        return self.outer_contexts.get(outer_id)

    def add_outer_context(self, ctx: OuterContext) -> int:
        """Add a new outer context. Raises ValueError if outer_id already exists."""
        if ctx.outer_id in self.outer_contexts:
            raise ValueError(f"Outer ID {ctx.outer_id} already exists")
        old_hash = self.current_hash
        self.outer_contexts[ctx.outer_id] = ctx
        self._update_hash()
        self._audit("ADD_CONTEXT", old_hash, outer_id=ctx.outer_id, code=ctx.code)
        return ctx.outer_id

    def update_outer_context(self, outer_id: int, **updates: Any) -> OuterContext:
        """Update fields on an existing outer context."""
        if outer_id not in self.outer_contexts:
            raise KeyError(f"Outer ID {outer_id} not found")
        old_hash = self.current_hash
        d = self.outer_contexts[outer_id].to_dict()
        for key, val in updates.items():
            if key == "outer_id":
                raise ValueError("outer_id is immutable")
            d[key] = val
        updated = OuterContext.from_dict(d)
        self.outer_contexts[outer_id] = updated
        self._update_hash()
        self._audit("UPDATE_CONTEXT", old_hash, outer_id=outer_id, fields=list(updates.keys()))
        return updated

    # ── IMPORT / EXPORT ────────────────────────────────────────────────────────

    def export_jsonl(self) -> str:
        """Export all glyphs as JSONL — one compact JSON record per line."""
        return "\n".join(
            g.to_json()
            for g in sorted(self.glyphs_144k.values(), key=lambda g: g.id)
        )

    def import_jsonl(self, jsonl_str: str, *, overwrite: bool = False) -> int:
        """
        Import glyphs from a JSONL string.

        Parameters
        ----------
        overwrite : if True, existing glyphs are replaced (delete + re-add).

        Returns number of glyphs successfully imported.
        """
        imported = 0
        for line in jsonl_str.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            glyph = Glyph144k.from_dict(json.loads(line))
            if glyph.id in self.glyphs_144k:
                if overwrite:
                    self.delete_glyph(glyph.id)
                else:
                    continue
            self.add_glyph(glyph)
            imported += 1
        return imported

    def export_snapshot(self) -> Dict[str, Any]:
        """Full registry snapshot as a plain dict (JSON-serialisable)."""
        return {
            "version":        self.VERSION,
            "hash":           self.current_hash,
            "glyphs":         [
                g.to_dict()
                for g in sorted(self.glyphs_144k.values(), key=lambda g: g.id)
            ],
            "outer_contexts": [
                c.to_dict()
                for c in sorted(self.outer_contexts.values(), key=lambda c: c.outer_id)
            ],
            "change_history": self.change_history,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> "GlyphRegistry":
        """Restore a full registry from a snapshot dict."""
        reg = cls.__new__(cls)
        reg.glyphs_144k    = {}
        reg.outer_contexts = {}
        reg.code_to_id     = {}
        reg.category_index = {cat: [] for cat in GlyphCategory}
        reg.change_history = list(snapshot.get("change_history", []))
        reg.current_hash   = ""

        for ctx_d in snapshot.get("outer_contexts", []):
            ctx = OuterContext.from_dict(ctx_d)
            reg.outer_contexts[ctx.outer_id] = ctx

        for g_d in snapshot.get("glyphs", []):
            g = Glyph144k.from_dict(g_d)
            reg.glyphs_144k[g.id]  = g
            reg.code_to_id[g.code] = g.id
            reg.category_index[g.category].append(g.id)

        reg._update_hash()
        return reg

    # ── Stats ──────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Summary statistics for monitoring / reporting."""
        return {
            "version":       self.VERSION,
            "total_glyphs":  len(self.glyphs_144k),
            "outer_contexts": len(self.outer_contexts),
            "change_count":  len(self.change_history),
            "registry_hash": self.current_hash,
            "categories": {
                cat.value: len(ids)
                for cat, ids in self.category_index.items()
                if ids
            },
        }
