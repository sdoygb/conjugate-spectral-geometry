"""Machine-precision checks for the descent (geo10-15 discipline).

Checks (10.91 §11 testable predictions):
  1. sign:  E_corr <= 0 every round (Lemma D) — a positive value is a bug
  2. monotonicity: E_var non-increasing as |V| grows (Prop 4.2)
  3. ordering: |E_2nd^exact| <= |E_block| <= |E_PT2^diag| on a positive-
     definite diagonally-dominant H_N (10.91 §12.2)
  4. block Jacobi: inter-block residual shrinks geometrically when
     rho(D^-1 O) < 1 (10.91 §9.1)
"""
import numpy as np


def check_sign(stats, raise_on_error=True):
    """E_corr <= 0 every round."""
    bad = [r for r in stats.rounds if r[2] > 1e-12]
    if bad:
        msg = f"sign check FAILED: {len(bad)} rounds with E_corr > 0"
        if raise_on_error:
            raise AssertionError(msg)
        return False
    return True


def check_monotone(stats, raise_on_error=True):
    """E_var non-increasing across rounds (|V| strictly grows)."""
    Es = [r[1] for r in stats.rounds]
    for a, b in zip(Es, Es[1:]):
        if b > a + 1e-12:
            msg = f"monotonicity FAILED: E rose {a:+.10f} -> {b:+.10f}"
            if raise_on_error:
                raise AssertionError(msg)
            return False
    return True


def check_ordering(E_exact2, E_block, E_diag, raise_on_error=True):
    """|E_exact| <= |E_block| <= |E_diag| (10.91 §12.2, diagonal-dominant H_N)."""
    a, b, d = abs(E_exact2), abs(E_block), abs(E_diag)
    ok = (a <= b + 1e-12) and (b <= d + 1e-12)
    if not ok and raise_on_error:
        raise AssertionError(
            f"ordering FAILED: |exact|={a:.3e} |block|={b:.3e} "
            f"|diag|={d:.3e}")
    return ok


def report(stats, E_final=None, E_ref=None):
    """Human-readable convergence report + error vs reference."""
    print("\n=== convergence report ===")
    print(stats)
    if E_ref is not None:
        last = stats.rounds[-1]
        E_var, E_corr = last[1], last[2]
        err_var = (E_var - E_ref) * 1000
        err_corr = (E_var + E_corr - E_ref) * 1000
        print(f"\nreference E = {E_ref:+.10f} Ha")
        print(f"final variational err = {err_var:+.4f} mHa")
        print(f"final variational+E_corr err = {err_corr:+.4f} mHa "
              f"(chemical accuracy 1.59 mHa)")
        if E_final is not None:
            print(f"reported E_final = {E_final:+.10f} Ha "
                  f"(err {((E_final - E_ref) * 1000):+.4f} mHa)")
    return True
