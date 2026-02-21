"""
radix.py — RadixCore and Digit1440000.

Schema references:
  Base conversion algorithms : Page 2, Sections 7.1 / 7.2
  Fixed-width encoding       : Page 2, Section 8.1
  Hierarchical Digit1440000  : Page 3, Section 13
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── RadixCore ─────────────────────────────────────────────────────────────────

class RadixCore:
    """
    Canonical base conversions for the AEUC numeral family.

    Supported bases
    ---------------
    2          binary
    10         decimal
    16         hexadecimal
    144        base-144
    144_000    base-144k   (6-digit fixed-width: 000000 – 143999)
    1_440_000  base-1.44M  (7-digit fixed-width: 0000000 – 1439999)
    """

    BASES: Dict[int, Dict[str, Any]] = {
        2:         {"name": "binary",      "digit_width": None, "max_digit": 1},
        10:        {"name": "decimal",     "digit_width": None, "max_digit": 9},
        16:        {"name": "hexadecimal", "digit_width": None, "max_digit": 15},
        144:       {"name": "base-144",    "digit_width": None, "max_digit": 143},
        144_000:   {"name": "base-144k",   "digit_width": 6,    "max_digit": 143_999},
        1_440_000: {
            "name": "base-1.44M",
            "digit_width": 7,
            "max_digit": 1_439_999,
            "hierarchical": True,
            "outer_base": 10,
            "inner_base": 144_000,
        },
    }

    def __init__(self) -> None:
        self.conversion_count    = 0
        self.validation_failures = 0

    # ── Core algorithms ───────────────────────────────────────────────────────

    def to_base(self, n: int, base: int) -> List[int]:
        """
        Page 2, Section 7.1 — integer → digit list (MSB first).
        """
        if base not in self.BASES:
            raise ValueError(f"Unsupported base: {base}")
        if n < 0:
            raise ValueError("Negative numbers not supported")
        if n == 0:
            self.conversion_count += 1
            return [0]
        digits: List[int] = []
        while n:
            n, r = divmod(n, base)
            digits.append(r)
        digits.reverse()
        self.conversion_count += 1
        return digits

    def from_base(self, digits: List[int], base: int) -> int:
        """
        Page 2, Section 7.2 — digit list → integer.
        """
        if base not in self.BASES:
            raise ValueError(f"Unsupported base: {base}")
        max_d = self.BASES[base]["max_digit"]
        n = 0
        for d in digits:
            if not (0 <= d <= max_d):
                self.validation_failures += 1
                raise ValueError(f"Digit {d} not in valid range [0, {max_d}]")
            n = n * base + d
        self.conversion_count += 1
        return n

    # ── Fixed-width encoding (Page 2, Section 8.1) ────────────────────────────

    def encode_digit_fixed(self, digit: int, base: int) -> str:
        """Encode a single digit as a zero-padded decimal string."""
        info = self.BASES.get(base)
        if info is None:
            raise ValueError(f"Unsupported base: {base}")
        width = info["digit_width"] or len(str(base - 1))
        max_d = info["max_digit"]
        if not (0 <= digit <= max_d):
            raise ValueError(f"Digit {digit} out of range [0, {max_d}]")
        return str(digit).zfill(width)

    def decode_digit_fixed(self, s: str, base: int) -> int:
        """Decode a zero-padded decimal string to an integer digit."""
        info = self.BASES.get(base)
        if info is None:
            raise ValueError(f"Unsupported base: {base}")
        digit = int(s)
        max_d = info["max_digit"]
        if not (0 <= digit <= max_d):
            self.validation_failures += 1
            raise ValueError(f"Digit {digit} out of range [0, {max_d}]")
        return digit

    def encode_number(self, n: int, base: int, separator: str = "-") -> str:
        """Encode integer as separator-joined fixed-width digit string."""
        return separator.join(
            self.encode_digit_fixed(d, base) for d in self.to_base(n, base)
        )

    def decode_number(self, encoded: str, base: int, separator: str = "-") -> int:
        """Decode separator-joined fixed-width digit string to integer."""
        return self.from_base(
            [self.decode_digit_fixed(s, base) for s in encoded.split(separator)],
            base,
        )

    def round_trip_test(self, n: int, base: int) -> bool:
        """Verify N → base-b → N round-trip."""
        try:
            return self.from_base(self.to_base(n, base), base) == n
        except Exception:
            return False


# ── Digit1440000 ──────────────────────────────────────────────────────────────

class Digit1440000:
    """
    Hierarchical base-1,440,000 digit.  (Page 3, Section 13)

    flat_value = outer × 144,000 + inner
      outer : 0 – 9        (context / outer layer)
      inner : 0 – 143,999  (base-144k inner digit)
    """

    INNER_BASE = 144_000
    OUTER_MAX  = 9
    INNER_MAX  = 143_999

    def __init__(
        self,
        outer: int = 0,
        inner: int = 0,
        *,
        flat_value: Optional[int] = None,
    ) -> None:
        if flat_value is not None:
            outer, inner = divmod(flat_value, self.INNER_BASE)
        if not (0 <= outer <= self.OUTER_MAX):
            raise ValueError(f"Outer digit {outer} not in [0, {self.OUTER_MAX}]")
        if not (0 <= inner <= self.INNER_MAX):
            raise ValueError(f"Inner digit {inner} not in [0, {self.INNER_MAX}]")
        self.outer = outer
        self.inner = inner

    @property
    def flat_value(self) -> int:
        return self.outer * self.INNER_BASE + self.inner

    def encode(self, separator: str = ":") -> str:
        """Encode as 'outer:inner' — e.g. '3:081567'."""
        return f"{self.outer}{separator}{str(self.inner).zfill(6)}"

    @classmethod
    def decode(cls, encoded: str, separator: str = ":") -> "Digit1440000":
        outer_s, inner_s = encoded.split(separator, 1)
        return cls(outer=int(outer_s), inner=int(inner_s))

    def __repr__(self) -> str:
        return (
            f"Digit1440000(outer={self.outer}, "
            f"inner={self.inner}, flat={self.flat_value})"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Digit1440000):
            return self.flat_value == other.flat_value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.flat_value)
