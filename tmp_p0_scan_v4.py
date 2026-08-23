"""P0 scan v4: chessboard 3x3 param scan + fast 4x4 random search."""
import sys
import numpy as np
sys.path.insert(0, '/tmp/toqito_clone')

from toqito.state_props import is_separable
from toqito.states import chessboard

FINAL = "inconclusive: PPT but no implemented sufficient condition proved separability"


def is_ppt_fast(rho, dA, dB):
    X = rho.reshape(dA, dB, dA, dB).transpose(0, 3, 2, 1).reshape(dA * dB, dA * dB)
    return np.min(np.linalg.eigvalsh(X)) >= -1e-10


def ccnr_norm1(rho, dA, dB):
    R = rho.reshape(dA, dB, dA, dB).transpose(0, 2, 1, 3).reshape(dA * dA, dB * dB)
    return np.linalg.norm(R, ord='nuc')


# ---------- 1) chessboard 3x3 param scan ----------
def scan_chessboard(n, seed):
    rng = np.random.default_rng(seed)
    hits = 0
    for i in range(n):
        mp = rng.uniform(0.2, 3.0, 6)
        try:
            rho = chessboard(mp)
        except Exception:
            continue
        if not is_ppt_fast(rho, 3, 3):
            continue
        c = ccnr_norm1(rho, 3, 3)
        if c > 1.0:
            continue
        r = is_separable(rho, dim=[3, 3], level=2)
        tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
        print(f'[chess] #{i} ccnr={c:.4f} mp={np.round(mp,3)} | {r}{tag}', flush=True)
        if r == (False, FINAL):
            hits += 1
            np.save(f'/tmp/p0_chess_hit_{i}.npy', rho)
            np.save(f'/tmp/p0_chess_hit_{i}_params.npy', mp)
            print(f'  saved /tmp/p0_chess_hit_{i}.npy', flush=True)
            if hits >= 3:
                return hits
    return hits


# ---------- 2) fast random 4x4 ----------
def random_ppt_ccnr_4x4(rng, max_tries=3000):
    for _ in range(max_tries):
        A = rng.standard_normal((16, 16)) + 1j * rng.standard_normal((16, 16))
        rho = A @ A.conj().T
        rho /= np.trace(rho)
        if not is_ppt_fast(rho, 4, 4):
            continue
        c = ccnr_norm1(rho, 4, 4)
        if c <= 1.0:
            return rho, c
    return None


def scan_4x4(n, seed):
    rng = np.random.default_rng(seed)
    hits = 0
    for i in range(n):
        hit = random_ppt_ccnr_4x4(rng)
        if hit is None:
            print(f'[4x4] #{i}: none in 3000 tries', flush=True)
            continue
        rho, c = hit
        r = is_separable(rho, dim=[4, 4], level=2)
        tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
        print(f'[4x4] #{i} ccnr={c:.4f} | {r}{tag}', flush=True)
        if r == (False, FINAL):
            hits += 1
            np.save(f'/tmp/p0_4x4_hit_{i}.npy', rho)
            print(f'  saved /tmp/p0_4x4_hit_{i}.npy', flush=True)
            if hits >= 3:
                return hits
    return hits


if __name__ == '__main__':
    h1 = scan_chessboard(60, seed=31)
    print(f'--- chessboard hits: {h1}', flush=True)
    h2 = scan_4x4(15, seed=47)
    print(f'--- 4x4 hits: {h2}', flush=True)
