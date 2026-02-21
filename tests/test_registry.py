"""Unit tests — glyph_registry.registry"""

import json
import pytest
from glyph_registry import GlyphRegistry, Glyph144k, GlyphCategory, GlyphPayload, OuterContext


def _g(gid: int, code: str, cat: GlyphCategory = GlyphCategory.SPECIAL) -> Glyph144k:
    return Glyph144k(id=gid, code=code, category=cat, description=f"Glyph {code}")


class TestInit:
    def test_default_contexts_populated(self):
        reg = GlyphRegistry()
        assert len(reg.outer_contexts) == 10

    def test_hash_set_on_init(self):
        reg = GlyphRegistry()
        assert len(reg.current_hash) == 64

    def test_empty_glyph_table(self):
        assert len(GlyphRegistry().glyphs_144k) == 0


class TestAddGlyph:
    def test_returns_id(self):
        reg = GlyphRegistry()
        assert reg.add_glyph(_g(0, "ZERO")) == 0

    def test_duplicate_id_raises(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        with pytest.raises(ValueError, match="already exists"):
            reg.add_glyph(_g(0, "OTHER"))

    def test_duplicate_code_raises(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        with pytest.raises(ValueError, match="already exists"):
            reg.add_glyph(_g(1, "ZERO"))

    def test_hash_changes(self):
        reg = GlyphRegistry()
        h1 = reg.current_hash
        reg.add_glyph(_g(0, "ZERO"))
        assert reg.current_hash != h1

    def test_audit_entry_created(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        actions = [e["action"] for e in reg.change_history]
        assert "ADD_GLYPH" in actions

    def test_category_index_updated(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A", GlyphCategory.GEOMETRY))
        assert 0 in reg.category_index[GlyphCategory.GEOMETRY]


class TestGetGlyph:
    def test_get_by_id(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(5, "FIVE"))
        assert reg.get_glyph(5).code == "FIVE"

    def test_missing_returns_none(self):
        assert GlyphRegistry().get_glyph(999) is None

    def test_get_by_code(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(5, "FIVE"))
        assert reg.get_glyph_by_code("FIVE").id == 5

    def test_missing_code_returns_none(self):
        assert GlyphRegistry().get_glyph_by_code("NOPE") is None


class TestUpdateGlyph:
    def test_update_description(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        reg.update_glyph(0, description="Updated desc")
        assert reg.get_glyph(0).description == "Updated desc"

    def test_update_code_refreshes_index(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "OLD"))
        reg.update_glyph(0, code="NEW")
        assert reg.get_glyph_by_code("NEW") is not None
        assert reg.get_glyph_by_code("OLD") is None

    def test_update_code_collision_raises(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        reg.add_glyph(_g(1, "B"))
        with pytest.raises(ValueError, match="already taken"):
            reg.update_glyph(0, code="B")

    def test_update_category_refreshes_index(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A", GlyphCategory.GEOMETRY))
        reg.update_glyph(0, category=GlyphCategory.HARMONIC)
        assert 0 not in reg.category_index[GlyphCategory.GEOMETRY]
        assert 0 in reg.category_index[GlyphCategory.HARMONIC]

    def test_update_immutable_id_raises(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        with pytest.raises(ValueError, match="immutable"):
            reg.update_glyph(0, id=99)

    def test_update_unknown_field_raises(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        with pytest.raises(ValueError, match="Unknown field"):
            reg.update_glyph(0, nonexistent="x")

    def test_update_missing_glyph_raises(self):
        with pytest.raises(KeyError):
            GlyphRegistry().update_glyph(999, description="x")

    def test_audit_entry_created(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        reg.update_glyph(0, description="New")
        assert any(e["action"] == "UPDATE_GLYPH" for e in reg.change_history)


class TestDeleteGlyph:
    def test_delete_removes_glyph(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        reg.delete_glyph(0)
        assert reg.get_glyph(0) is None

    def test_delete_cleans_code_index(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        reg.delete_glyph(0)
        assert "ZERO" not in reg.code_to_id

    def test_delete_cleans_category_index(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO", GlyphCategory.GEOMETRY))
        reg.delete_glyph(0)
        assert 0 not in reg.category_index[GlyphCategory.GEOMETRY]

    def test_delete_returns_glyph(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        deleted = reg.delete_glyph(0)
        assert deleted.code == "ZERO"

    def test_delete_missing_raises(self):
        with pytest.raises(KeyError):
            GlyphRegistry().delete_glyph(999)

    def test_audit_entry_created(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "ZERO"))
        reg.delete_glyph(0)
        assert any(e["action"] == "DELETE_GLYPH" for e in reg.change_history)


class TestSearch:
    def test_search_by_category(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A", GlyphCategory.GEOMETRY))
        reg.add_glyph(_g(1, "B", GlyphCategory.HARMONIC))
        geo = reg.search_by_category(GlyphCategory.GEOMETRY)
        assert len(geo) == 1 and geo[0].code == "A"

    def test_search_empty_category(self):
        assert GlyphRegistry().search_by_category(GlyphCategory.STORYEVENT) == []

    def test_search_by_description_case_insensitive(self):
        reg = GlyphRegistry()
        reg.add_glyph(Glyph144k(id=0, code="A", category=GlyphCategory.SPECIAL, description="Sacred geometry unit"))
        assert len(reg.search_by_description("sacred")) == 1

    def test_search_by_description_no_match(self):
        reg = GlyphRegistry()
        assert reg.search_by_description("xyz") == []

    def test_search_by_description_case_sensitive(self):
        reg = GlyphRegistry()
        reg.add_glyph(Glyph144k(id=0, code="A", category=GlyphCategory.SPECIAL, description="Sacred geometry"))
        assert reg.search_by_description("sacred", case_sensitive=True) == []
        assert len(reg.search_by_description("Sacred", case_sensitive=True)) == 1


class TestExportImport:
    def test_export_jsonl_valid_lines(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        reg.add_glyph(_g(1, "B"))
        lines = [l for l in reg.export_jsonl().splitlines() if l.strip()]
        assert len(lines) == 2
        for line in lines:
            assert "\n" not in line
            json.loads(line)

    def test_import_jsonl_round_trip(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(42, "FORTY_TWO", GlyphCategory.HARMONIC))
        jsonl = reg.export_jsonl()
        reg2 = GlyphRegistry()
        assert reg2.import_jsonl(jsonl) == 1
        assert reg2.get_glyph(42).category == GlyphCategory.HARMONIC

    def test_import_skips_duplicates_by_default(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        assert reg.import_jsonl(reg.export_jsonl()) == 0

    def test_import_overwrite(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        line = Glyph144k(id=0, code="A", category=GlyphCategory.SPECIAL, description="Overwritten").to_json()
        assert reg.import_jsonl(line, overwrite=True) == 1
        assert reg.get_glyph(0).description == "Overwritten"

    def test_snapshot_round_trip(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        reg.add_glyph(_g(1, "B"))
        snap = reg.export_snapshot()
        reg2 = GlyphRegistry.from_snapshot(snap)
        assert len(reg2.glyphs_144k) == 2
        assert reg2.current_hash == reg.current_hash

    def test_snapshot_preserves_change_history(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A"))
        reg.delete_glyph(0)
        snap = reg.export_snapshot()
        reg2 = GlyphRegistry.from_snapshot(snap)
        assert len(reg2.change_history) == len(reg.change_history)


class TestStats:
    def test_stats_structure(self):
        reg = GlyphRegistry()
        reg.add_glyph(_g(0, "A", GlyphCategory.GEOMETRY))
        s = reg.stats()
        assert s["total_glyphs"] == 1
        assert s["outer_contexts"] == 10
        assert "GEOMETRY" in s["categories"]
        assert s["categories"]["GEOMETRY"] == 1
