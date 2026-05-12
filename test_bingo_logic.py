"""Unit tests for bingo_logic — pure functions, no Firebase needed."""
from __future__ import annotations

from bingo_logic import ROWS, COLS, DIAGS, FULL, all_lines, detect_new_lines


def test_all_lines_count():
    lines = all_lines()
    # 4 rows + 4 cols + 2 diagonals + 1 full = 11
    assert len(lines) == 11
    types = {l.type for l in lines}
    assert types == {"horizontal", "vertical", "diagonal", "full"}


def test_row_detection():
    found = detect_new_lines(set(ROWS[2]), existing_claims=set())
    assert len(found) == 1
    assert found[0].type == "horizontal"
    assert found[0].line_id == "row_2"


def test_col_detection():
    found = detect_new_lines(set(COLS[0]), existing_claims=set())
    assert len(found) == 1
    assert found[0].type == "vertical"
    assert found[0].line_id == "col_0"


def test_main_diagonal():
    found = detect_new_lines(set(DIAGS[0]), existing_claims=set())
    assert len(found) == 1
    assert found[0].type == "diagonal"
    assert found[0].line_id == "diag_main"


def test_anti_diagonal():
    found = detect_new_lines(set(DIAGS[1]), existing_claims=set())
    assert len(found) == 1
    assert found[0].type == "diagonal"
    assert found[0].line_id == "diag_anti"


def test_full_board_emits_everything_once():
    found = detect_new_lines(set(FULL), existing_claims=set())
    # 4 rows + 4 cols + 2 diags + 1 full = 11
    assert len(found) == 11
    by_type: dict[str, int] = {}
    for l in found:
        by_type[l.type] = by_type.get(l.type, 0) + 1
    assert by_type == {"horizontal": 4, "vertical": 4, "diagonal": 2, "full": 1}


def test_existing_claims_are_skipped():
    existing = {("horizontal", "row_2"), ("vertical", "col_0")}
    found = detect_new_lines(set(ROWS[2]) | set(COLS[0]), existing_claims=existing)
    # row_2 and col_0 already claimed; nothing new — but col_0 shares idx 8 with row_2;
    # only completed tiles available are ROWS[2] | COLS[0] which still only completes
    # those two lines, both already claimed.
    assert found == []


def test_partial_row_no_match():
    found = detect_new_lines({0, 1, 2}, existing_claims=set())
    assert found == []


def test_completion_of_one_more_line():
    # Completing row 0 and col 0 → row_0 + col_0 (both new), nothing else.
    completed = set(ROWS[0]) | set(COLS[0])
    found = detect_new_lines(completed, existing_claims=set())
    ids = {(l.type, l.line_id) for l in found}
    assert ids == {("horizontal", "row_0"), ("vertical", "col_0")}
