"""Unit tests for RM code basics (all values are hand-computed closed forms)."""
from qec_cert.rm_codes import ag_flat_count, build_cols, css_params, parity_big, rm_dim, rm_rows


def test_rm_dim_closed_form():
    assert rm_dim(1, 5) == 6        # 1 + 5
    assert rm_dim(2, 6) == 22       # 1 + 6 + 15
    assert rm_dim(3, 8) == 93       # 1 + 8 + 28 + 56
    assert rm_dim(4, 10) == 386     # 1 + 10 + 45 + 120 + 210


def test_css_params():
    assert css_params(1, 5) == (32, 20, 4)       # [[32,20,4]]
    assert css_params(2, 6) == (64, 20, 8)       # [[64,20,8]]
    assert css_params(4, 10) == (1024, 252, 32)  # [[1024,252,32]]


def test_ag_flat_count_closed_form():
    # 2-flats of AG(5,2) = 2^3 * [5;2]_2 = 8 * 155 = 1240 (anchor verified in 10.30)
    assert ag_flat_count(5, 2) == 1240
    # 2-flats of AG(6,2) = 2^4 * [6;2]_2 = 16 * 651 = 10416 (anchor verified in 10.30)
    assert ag_flat_count(6, 2) == 10416
    # 3-flats of AG(6,2) = 2^3 * [6;3]_2 = 8 * 1395 = 11160
    assert ag_flat_count(6, 3) == 11160


def test_rm_rows_shape_and_weights():
    rows = rm_rows(2, 6)
    assert len(rows) == rm_dim(2, 6)
    n = 2 ** 6
    # A monomial x_{i1}..x_{ik} takes the value 1 on exactly half of AG(m,2)
    # -> row weight 2^(m-k).
    # Row order: deg=0 first (the constant 1), then deg=1 (x_i), then deg=2 (x_i x_j).
    assert bin(rows[0]).count("1") == n             # constant row
    for i in range(6):
        assert bin(rows[1 + i]).count("1") == n // 2    # degree-1 monomials
    for i in range(15):
        assert bin(rows[7 + i]).count("1") == n // 4    # degree-2 monomials


def test_parity_big():
    n = 32
    assert parity_big(0, n) == 0
    assert parity_big(1, n) == 1
    assert parity_big(3, n) == 0   # two bits
    assert parity_big((1 << n) - 1, n) == 0   # 32 ones (even)
    assert parity_big((1 << n) - 2, n) == 1   # 31 ones (odd)


def test_build_cols_width():
    cols, w = build_cols(2, 6)
    assert w == 22
    assert len(cols) == 64
    cols32, w32 = build_cols(1, 5)
    assert w32 == 6
    assert len(cols32) == 32
