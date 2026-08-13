"""Tests for the geometric certificate verifier: all machine checks must pass
and the field semantics must be correct."""
import pytest

from qec_cert.certificate import certify
from qec_cert.rm_codes import FAMILY_EXAMPLES, css_params


@pytest.mark.parametrize("r,m", [(1, 5), (2, 6)])
def test_certificate_valid_small(r, m):
    cert = certify(r, m)
    n, k, d = css_params(r, m)
    assert (cert.n, cert.k, cert.d) == (n, k, d)
    assert cert.valid
    assert cert.cols_distinct
    assert cert.w2_undetected == 0
    assert cert.sample_miss == 0
    assert cert.wF_in_Cperp
    assert cert.wF_not_in_C
    assert cert.wF_weight == d == 2 ** (r + 1)


def test_certificate_full_family():
    """All 7 verified family members: certificates valid (including
    [[1024,252,32]])."""
    for r, m in FAMILY_EXAMPLES:
        cert = certify(r, m)
        assert cert.valid, f"certificate failed for RM({r},{m}): {cert.to_dict()}"


def test_certificate_reproducible():
    """The sampling corroboration is reproducible under the same seed
    (certificate deterministic, excluding the elapsed-time field)."""
    c1 = certify(2, 6, seed=123).to_dict()
    c2 = certify(2, 6, seed=123).to_dict()
    c1.pop("elapsed")
    c2.pop("elapsed")
    assert c1 == c2


def test_certificate_dict_and_summary():
    cert = certify(1, 5)
    d = cert.to_dict()
    assert d["n"] == 32 and d["d"] == 4
    assert "VALID" in cert.summary()
