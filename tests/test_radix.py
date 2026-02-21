"""Unit tests — glyph_registry.radix"""

import pytest
from glyph_registry import RadixCore, Digit1440000


class TestRadixCore:
    def setup_method(self):
        self.r = RadixCore()

    def test_to_base_zero(self):
        assert self.r.to_base(0, 144_000) == [0]

    def test_to_base_one(self):
        assert self.r.to_base(1, 10) == [1]

    def test_to_base_carries(self):
        assert self.r.to_base(10, 10) == [1, 0]

    def test_from_base_simple(self):
        assert self.r.from_base([1, 0], 10) == 10

    def test_round_trip_base_144k(self):
        for n in [0, 1, 143_999, 1_000_000, 1_234_567, 143_999 * 10]:
            assert self.r.round_trip_test(n, 144_000), f"Round-trip failed for {n}"

    def test_encode_fixed_6_digits(self):
        assert self.r.encode_digit_fixed(42, 144_000) == "000042"
        assert self.r.encode_digit_fixed(0, 144_000) == "000000"
        assert self.r.encode_digit_fixed(143_999, 144_000) == "143999"

    def test_decode_fixed(self):
        assert self.r.decode_digit_fixed("000042", 144_000) == 42

    def test_encode_number_round_trip(self):
        for n in [0, 42, 1_234_567, 143_999 * 5 + 12_345]:
            assert self.r.decode_number(self.r.encode_number(n, 144_000), 144_000) == n

    def test_custom_separator(self):
        encoded = self.r.encode_number(1_234_567, 144_000, separator="|")
        assert "|" in encoded
        assert self.r.decode_number(encoded, 144_000, separator="|") == 1_234_567

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="Negative"):
            self.r.to_base(-1, 10)

    def test_invalid_base_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            self.r.to_base(1, 99999)

    def test_digit_out_of_range_raises(self):
        with pytest.raises(ValueError):
            self.r.from_base([144_000], 144_000)

    def test_conversion_count_increments(self):
        before = self.r.conversion_count
        self.r.to_base(42, 144_000)
        self.r.from_base([42], 144_000)
        assert self.r.conversion_count == before + 2

    def test_validation_failure_tracked(self):
        before = self.r.validation_failures
        with pytest.raises(ValueError):
            self.r.from_base([144_000], 144_000)
        assert self.r.validation_failures == before + 1


class TestDigit1440000:
    def test_construct_from_parts(self):
        d = Digit1440000(outer=3, inner=81_567)
        assert d.flat_value == 3 * 144_000 + 81_567

    def test_construct_from_flat(self):
        flat = 3 * 144_000 + 81_567
        d = Digit1440000(flat_value=flat)
        assert d.outer == 3
        assert d.inner == 81_567

    def test_flat_round_trip(self):
        for flat in [0, 1, 144_000, 1_439_999]:
            d = Digit1440000(flat_value=flat)
            assert d.flat_value == flat

    def test_encode_decode_round_trip(self):
        d = Digit1440000(outer=5, inner=12_345)
        assert Digit1440000.decode(d.encode()) == d

    def test_encode_format(self):
        d = Digit1440000(outer=3, inner=81_567)
        assert d.encode() == "3:081567"

    def test_outer_out_of_range_raises(self):
        with pytest.raises(ValueError):
            Digit1440000(outer=10, inner=0)

    def test_inner_out_of_range_raises(self):
        with pytest.raises(ValueError):
            Digit1440000(outer=0, inner=144_000)

    def test_equality(self):
        a = Digit1440000(outer=1, inner=1)
        b = Digit1440000(flat_value=144_001)
        assert a == b

    def test_hash_usable_in_set(self):
        d = Digit1440000(outer=1, inner=0)
        s = {d}
        assert d in s

    def test_repr(self):
        d = Digit1440000(outer=2, inner=500)
        assert "Digit1440000" in repr(d)
        assert "288500" in repr(d)  # 2*144000+500
