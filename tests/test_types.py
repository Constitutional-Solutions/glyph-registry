"""Unit tests — glyph_registry.types"""

import json
import pytest
from glyph_registry import GlyphCategory, GlyphPayload, Glyph144k, OuterContext


class TestGlyphPayload:
    def test_round_trip(self):
        p = GlyphPayload(type="chord", data={"ratios": [1.0, 1.5]})
        assert GlyphPayload.from_dict(p.to_dict()) == p

    def test_none_data_defaults_to_empty_dict(self):
        p = GlyphPayload(type="x")
        assert p.to_dict()["data"] == {}

    def test_from_dict_with_none_type(self):
        p = GlyphPayload.from_dict({"type": None, "data": {}})
        assert p.type is None


class TestGlyph144k:
    def test_valid_creation(self):
        g = Glyph144k(id=0, code="ZERO", category=GlyphCategory.SPECIAL, description="Empty")
        assert g.id == 0
        assert g.timestamp is not None

    def test_timestamp_auto_set(self):
        g = Glyph144k(id=1, code="ONE", category=GlyphCategory.SPECIAL, description="x")
        assert "T" in g.timestamp  # ISO-8601 UTC

    def test_id_upper_boundary(self):
        g = Glyph144k(id=143_999, code="MAX", category=GlyphCategory.SPECIAL, description="x")
        assert g.id == 143_999

    def test_id_above_max_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            Glyph144k(id=144_000, code="BAD", category=GlyphCategory.SPECIAL, description="x")

    def test_id_negative_raises(self):
        with pytest.raises(ValueError):
            Glyph144k(id=-1, code="NEG", category=GlyphCategory.SPECIAL, description="x")

    def test_empty_code_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Glyph144k(id=1, code="", category=GlyphCategory.SPECIAL, description="x")

    def test_dict_round_trip_no_payload(self):
        g = Glyph144k(id=5, code="FIVE", category=GlyphCategory.GEOMETRY, description="Five")
        g2 = Glyph144k.from_dict(g.to_dict())
        assert g2.id == g.id
        assert g2.category == g.category
        assert g2.code == g.code

    def test_dict_round_trip_with_payload(self):
        g = Glyph144k(
            id=1,
            code="GEO_A",
            category=GlyphCategory.GEOMETRY,
            description="Test",
            geometry_payload=GlyphPayload(type="tetra", data={"space": "R3"}),
        )
        g2 = Glyph144k.from_dict(g.to_dict())
        assert g2.geometry_payload.type == "tetra"
        assert g2.geometry_payload.data == {"space": "R3"}

    def test_to_json_compact_no_newlines(self):
        g = Glyph144k(id=5, code="T", category=GlyphCategory.HARMONIC, description="t")
        j = g.to_json()
        assert "\n" not in j
        json.loads(j)  # must be valid JSON

    def test_to_json_pretty(self):
        g = Glyph144k(id=5, code="T", category=GlyphCategory.HARMONIC, description="t")
        j = g.to_json(indent=2)
        assert "\n" in j


class TestOuterContext:
    def test_valid(self):
        ctx = OuterContext(outer_id=3, code="CTX_H", description="Harmonic")
        assert ctx.outer_id == 3

    def test_boundary_zero(self):
        ctx = OuterContext(outer_id=0, code="BASE", description="x")
        assert ctx.outer_id == 0

    def test_boundary_nine(self):
        ctx = OuterContext(outer_id=9, code="SOVEREIGN", description="x")
        assert ctx.outer_id == 9

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            OuterContext(outer_id=10, code="X", description="x")

    def test_round_trip(self):
        ctx = OuterContext(outer_id=0, code="BASE", description="Base", layer_info={"k": 1})
        ctx2 = OuterContext.from_dict(ctx.to_dict())
        assert ctx2.outer_id == ctx.outer_id
        assert ctx2.layer_info == {"k": 1}
