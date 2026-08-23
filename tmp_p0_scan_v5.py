"""P0 scan v5: convex mixes M + t*(PPTES) + Horodecki 4x4 + chessboard fine scan."""
import sys
import numpy as np
sys.path.insert(0, '/tmp/toqito_clone')

from toqito.state_props import is_separable
from toqito.states import horodecki, tile, chessboard

FINAL = "inconclusive: PPT but no implemented sufficient condition proved separability"


def pt_min(rho, dA, dB):
    X = rho.reshape(dA, dB, dA, dB).transpose(0, 3, 2, 1).reshape(dA * dB, dA * dB)
    return np.min(np.linalg.eigvalsh(X))


def ccnr(rho, dA, dB):
    R = rho.reshape(dA, dB, dA, dB).transpose(0, 2, 1, 3).reshape(dA * dA, dB * dB)
    return np.linalg.norm(R, ord='nuc')


# ---------- A) convex mixes of maximally mixed + known PPTES ----------
pptess = {
    'tiles': (np.eye(9) - sum(np.outer(tile(i), tile(i).conj()) for i in range(5))) / 4,
    'horodecki_3x3_a08': horodecki(0.8, dim=[3, 3]),
    'horodecki_3x3_a06': horodecki(0.6, dim=[3, 3]),
}
I9 = np.eye(9) / 9

for name, E in pptess.items():
    cE = ccnr(E, 3, 3)
    for t in np.arange(0.30, 0.99, 0.05):
        rho = (1 - t) * I9 + t * E
        m = pt_min(rho, 3, 3)
        if m < -1e-10:
            continue
        c = ccnr(rho, 3, 3)
        if c > 1.0:
            continue
        r = is_separable(rho, dim=[3, 3], level=2)
        tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
        print(f'[mix {name}] t={t:.2f} ptmin={m:+.2e} ccnr={c:.4f} | {r}{tag}', flush=True)
        if r == (False, FINAL):
            np.save(f'/tmp/p0_mix_{name}_t{t:.2f}.npy', rho)

# ---------- B) Horodecki 4x4 ----------
for a in [0.5, 0.6, 0.7, 0.8, 0.9]:
    try:
        rho = horodecki(a, dim=[4, 4])
    except Exception as e:
        print(f'[hor4] a={a} construct failed: {e}', flush=True)
        continue
    m = pt_min(rho, 4, 4)
    if m < -1e-10:
        print(f'[hor4] a={a} NPT (ptmin={m:+.2e})', flush=True)
        continue
    c = ccnr(rho, 4, 4)
    print(f'[hor4] a={a} ptmin={m:+.2e} ccnr={c:.4f}', flush=True)
    if c <= 1.0:
        r = is_separable(rho, dim=[4, 4], level=2)
        tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
        print(f'  -> {r}{tag}', flush=True)

# ---------- C) chessboard fine scan: find PPT with CCNR<=1 ----------
rng = np.random.default_rng(77)
for i in range(200):
    mp = rng.uniform(0.5, 2.0, 6)
    try:
        rho = chessboard(mp)
    except Exception:
        continue
    m = pt_min(rho, 3, 3)
    if m < -1e-10:
        continue
    c = ccnr(rho, 3, 3)
    if c > 1.0:
        continue
    r = is_separable(rho, dim=[3, 3], level=2)
    tag = "  <== FINAL HIT" if r == (False, FINAL) else ""
    print(f'[chess] #{i} ptmin={m:+.2e} ccnr={c:.4f} mp={np.round(mp,3)} | {r}{tag}', flush=True)
    if r == (False, FINAL):
        np.save(f'/tmp/p0_chess_hit_{i}.npy', rho)
        np.save(f'/tmp/p0_chess_hit_{i}_params.npy', mp)

print('--- done ---', flush=True)
