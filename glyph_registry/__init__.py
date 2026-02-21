"""
glyph-registry — FSOU-compliant base-144k glyph registry.

Quick start
-----------
>>> from glyph_registry import GlyphRegistry, Glyph144k, GlyphCategory
>>> reg = GlyphRegistry()
>>> reg.add_glyph(Glyph144k(id=0, code="ZERO", category=GlyphCategory.SPECIAL, description="Neutral empty glyph"))
0
>>> reg.stats()
"""

from .types    import GlyphCategory, GlyphPayload, Glyph144k, OuterContext
from .registry import GlyphRegistry
from .radix    import RadixCore, Digit1440000

__all__ = [
    "GlyphCategory",
    "GlyphPayload",
    "Glyph144k",
    "OuterContext",
    "GlyphRegistry",
    "RadixCore",
    "Digit1440000",
]

__version__ = "1.0.0"
