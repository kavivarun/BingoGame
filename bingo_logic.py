"""Pure functions for detecting bingo patterns on a 4x4 grid.

Tile indices laid out row-major:
     0  1  2  3
     4  5  6  7
     8  9 10 11
    12 13 14 15
"""
from __future__ import annotations

from dataclasses import dataclass

ROWS: list[list[int]] = [
    [0, 1, 2, 3],
    [4, 5, 6, 7],
    [8, 9, 10, 11],
    [12, 13, 14, 15],
]

COLS: list[list[int]] = [
    [0, 4, 8, 12],
    [1, 5, 9, 13],
    [2, 6, 10, 14],
    [3, 7, 11, 15],
]

DIAGS: list[list[int]] = [
    [0, 5, 10, 15],
    [3, 6, 9, 12],
]

FULL: list[int] = list(range(16))


@dataclass(frozen=True)
class Line:
    type: str            # 'horizontal' | 'vertical' | 'diagonal' | 'full'
    line_id: str         # stable id within type, e.g. 'row_0', 'col_2', 'diag_main', 'full'
    indices: tuple[int, ...]


def all_lines() -> list[Line]:
    out: list[Line] = []
    for i, r in enumerate(ROWS):
        out.append(Line("horizontal", f"row_{i}", tuple(r)))
    for i, c in enumerate(COLS):
        out.append(Line("vertical", f"col_{i}", tuple(c)))
    out.append(Line("diagonal", "diag_main", tuple(DIAGS[0])))
    out.append(Line("diagonal", "diag_anti", tuple(DIAGS[1])))
    out.append(Line("full", "full", tuple(FULL)))
    return out


def detect_new_lines(
    completed_tiles: set[int],
    existing_claims: set[tuple[str, str]],
) -> list[Line]:
    """Return lines fully covered by `completed_tiles` and not already in
    `existing_claims` (set of (type, line_id) pairs)."""
    out: list[Line] = []
    for line in all_lines():
        if (line.type, line.line_id) in existing_claims:
            continue
        if all(idx in completed_tiles for idx in line.indices):
            out.append(line)
    return out
