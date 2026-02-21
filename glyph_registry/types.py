"""
types.py — Core data types for the base-144k glyph registry.

Schema references:
  Glyph144k   : Page 2, Section 9
  OuterContext : Page 3, Section 15
  GlyphPayload : Page 6, Section 24.1
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enumerations ──────────────────────────────────────────────────────────────

class GlyphCategory(str, Enum):
    """Semantic category of a base-144k glyph."""
    GEOMETRY   = "GEOMETRY"
    HARMONIC   = "HARMONIC"
    PROTOSTATE = "PROTOSTATE"
    STORYEVENT = "STORYEVENT"
    SPECIAL    = "SPECIAL"


# ── Payload ───────────────────────────────────────────────────────────────────

@dataclass
class GlyphPayload:
    """Typed payload container for geometry / harmonic / protocol data."""
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "data": self.data or {}}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GlyphPayload":
        return cls(type=d.get("type"), data=d.get("data"))


# ── Primary record ────────────────────────────────────────────────────────────

@dataclass
class Glyph144k:
    """
    Base-144,000 glyph record.  (Page 2, Section 9)

    id          : 0 – 143,999  (base-144k digit value)
    code        : human-readable short code (unique, UPPER_SNAKE)
    category    : GlyphCategory enum
    description : plain-text explanation
    *_payload   : optional structured payload (geometry / harmonic / protocol)
    version     : semver string
    timestamp   : ISO-8601 UTC creation stamp (auto-set)
    """
    id:               int
    code:             str
    category:         GlyphCategory
    description:      str
    geometry_payload: Optional[GlyphPayload] = None
    harmonic_payload: Optional[GlyphPayload] = None
    protocol_payload: Optional[GlyphPayload] = None
    version:          str = "1.0.0"
    timestamp:        Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc).isoformat()
        if not (0 <= self.id <= 143_999):
            raise ValueError(f"Glyph ID {self.id} out of range [0, 143999]")
        if not self.code:
            raise ValueError("Glyph code must be a non-empty string")

    # ── serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d

    def to_json(self, *, indent: Optional[int] = None) -> str:
        """Compact JSON by default (suitable for JSONL); pass indent=2 for pretty."""
        kwargs: Dict[str, Any] = {"separators": (",", ":")} if indent is None else {"indent": indent}
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Glyph144k":
        """Full round-trip deserialisation — reconstructs GlyphPayload objects."""
        d = dict(data)
        d["category"] = GlyphCategory(d["category"]) if isinstance(d["category"], str) else d["category"]
        for field_name in ("geometry_payload", "harmonic_payload", "protocol_payload"):
            raw = d.get(field_name)
            if isinstance(raw, dict):
                d[field_name] = GlyphPayload.from_dict(raw)
        return cls(**d)


# ── Outer context ─────────────────────────────────────────────────────────────

@dataclass
class OuterContext:
    """
    Outer context layer for base-1,440,000 addressing.  (Page 3, Section 15)

    outer_id   : 0 – 9  (outer digit selects context layer)
    code       : short code
    description: context meaning
    layer_info : optional metadata dict
    version    : semver string
    timestamp  : ISO-8601 UTC creation stamp (auto-set)
    """
    outer_id:    int
    code:        str
    description: str
    layer_info:  Optional[Dict[str, Any]] = None
    version:     str = "1.0.0"
    timestamp:   Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc).isoformat()
        if not (0 <= self.outer_id <= 9):
            raise ValueError(f"Outer ID {self.outer_id} out of range [0, 9]")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        kwargs: Dict[str, Any] = {"separators": (",", ":")} if indent is None else {"indent": indent}
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OuterContext":
        return cls(**data)
