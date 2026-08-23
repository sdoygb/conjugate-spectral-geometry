"""P0 scan v3: random search for a state reaching the final inconclusive return.

Filter pipeline: PSD -> PPT -> CCNR pass (||R(rho)||_1 <= 1) -> full is_separable.
"""
import sys
import numpy as np
sys.path.insert(0, '/tmp/toqito_clone')

from toqito.state_props import is_separable, is_ppt

FINAL = "inconclusive: PPT but no implemented sufficient condition proved separability"


def ccnr_norm1(rho, dA, dB):
    """Realignment matrix R(rho) with entries R_{iA iB, jA jB} = rho_{iA jA, iB jB}."""
    R = rho.reshape(dA, dB, dA, dB).transpose(0, 2, 1, 3).reshape(dA * dA, dB * dB)
    return np.linalg.norm(R, ord='nuc')


def random_ppt_pass_ccnr(dA, dB, rng, max_tries=2000):
    """Return (rho, ccnr) for a random PSD+PPT state with CCNR <= 1, or None."""
    D = dA * dB
    for _ in range(max_tries):
        A = rng.standard_normal((D, D)) + 1j * rng.standard_normal((D, D))
        rho = A @ A.conj().T
        rho /= np.trace(rho)
        if not is_ppt(rho, 2, [dA, dB]):
            continue
        c = ccnr_norm1(rho, dA, dB)
        if c <= 1.0:
            return rho, c
    return None


def scan(dA, dB, n_states, seed):
    rng = np.random.default_rng(seed)
    found = 0
    for i in range(n_states):
        hit = random_ppt_pass_ccnr(dA, dB, rng)
        if hit is None:
            print(f'[{dA}x{dB}] #{i}: no PPT+CCNR-pass state in 2000 tries')
            continue
        rho, c = hit
        r = is_separable(rho, dim=[dA, dB], level=2)
        tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
        print(f'[{dA}x{dB}] #{i}: ccnr={c:.4f} | {r}{tag}')
        if r == (False, FINAL):
            found += 1
            np.save(f'/tmp/p0_final_hit_{dA}x{dB}_{i}.npy', rho)
            print(f'  saved /tmp/p0_final_hit_{dA}x{dB}_{i}.npy')
            if found >= 2:
                return
    print(f'[{dA}x{dB}] done, final hits: {found}')


if __name__ == '__main__':
    scan(3, 3, 12, seed=11)
    scan(4, 4, 8, seed=23)
