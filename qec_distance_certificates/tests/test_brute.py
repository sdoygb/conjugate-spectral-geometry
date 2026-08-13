"""Tests for the brute-force baseline: exact agreement with closed forms
(cross-validation anchors).

These tests are the core of the two-path independent verification:
  * the certificate path (certify) claims d = 2^(r+1);
  * the brute-force path (brute_verify) references no RM theorems, purely
    enumerating the error space;
  * the two must agree on small codes.
"""
from qec_cert.brute import brute_verify
from qec_cert.certificate import certify
from qec_cert.rm_codes import ag_flat_count


def test_brute_32_20_4_full_closure():
    """[[32,20,4]]: weights 1..3 fully detected (d>=4); the weight-4 layer
    = 1240 = 2-flat count (d<=4)."""
    layers = brute_verify(1, 5, max_w=4)
    s = layers.pop("_summary")
    assert s["n"] == 32 and s["k"] == 20 and s["d"] == 4
    for w in (1, 2, 3):
        assert layers[w]["undetected"] == 0, f"weight {w} should be fully detected"
    assert layers[1]["total"] == 32
    assert layers[2]["total"] == 496
    assert layers[3]["total"] == 4960
    # The weight-4 syndrome=0 count = number of logical X operators
    # = 2-flat count of AG(5,2) (closed form)
    assert layers[4]["total"] == 35960
    assert layers[4]["undetected"] == ag_flat_count(5, 2) == 1240


def test_brute_64_50_4_full_closure():
    """[[64,50,4]]: the weight-4 layer = 10416 = 2-flat count of AG(6,2)
    (anchor verified in the 10.30 article)."""
    layers = brute_verify(1, 6, max_w=4)
    s = layers.pop("_summary")
    assert s["n"] == 64 and s["d"] == 4
    for w in (1, 2, 3):
        assert layers[w]["undetected"] == 0
    assert layers[4]["total"] == 635376   # C(64,4)
    assert layers[4]["undetected"] == ag_flat_count(6, 2) == 10416


def test_brute_64_20_8_lower_layers():
    """[[64,20,8]]: weights 1..3 fully detected (corroborating d>=8; full
    enumeration of 43,744 flip sets)."""
    layers = brute_verify(2, 6, max_w=3)
    s = layers.pop("_summary")
    assert s["n"] == 64 and s["k"] == 20 and s["d"] == 8
    assert layers[1]["total"] == 64
    assert layers[2]["total"] == 2016
    assert layers[3]["total"] == 41664
    for w in (1, 2, 3):
        assert layers[w]["undetected"] == 0


def test_brute_consistent_with_certificate():
    """Two-path consistency: codes with a valid certificate must have zero
    undetected errors in the brute-force lower-bound verification."""
    for r, m in [(1, 5), (1, 6), (2, 6)]:
        cert = certify(r, m)
        assert cert.valid
        layers = brute_verify(r, m, max_w=3)
        for w in (1, 2, 3):
            assert layers[w]["undetected"] == 0
