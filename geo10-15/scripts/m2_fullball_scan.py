#!/usr/bin/env python3
"""Theory-vs-engineering discriminator (instrumented): E_var vs |V| across
the FULL HF Bruhat ball (25720 members) of H2O/cc-pVTZ.

If E_var -> few mHa as V -> 25720, truncation was the culprit (engineering).
If E_var plateaus at 20-40 mHa, the single-centre wavepacket picture fails
(theory).

Observability (geo10-15 discipline, user-confirmed 2026-09-03):
  - RunMonitor markers + status file + per-chunk progress
  - per-|V| checkpoint: resume, never rerun a killed H build
  - budgets: H_build, eigh windows logged in status

Usage:
  PYTHONPATH=. python3 scripts/m2_fullball_scan.py            # foreground
  python3 scripts/_watch.py notes m2_fullball <cmd...>        # watchdog
"""
import sys, os, time, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore')
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore/examples')
import numpy as np
from solver.system import SectorSystem
from solver.descent import Descent
from solver.runmon import RunMonitor, save_checkpoint, load_checkpoint
from scipy.sparse.linalg import eigsh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NOTES = os.path.join(ROOT, 'notes')
RESUME = os.environ.get('RESUME', '0') == '1'
FRACTIONS = [0.5, 0.75, 1.0]


def main():
    mon = RunMonitor('m2_fullball', NOTES, budget={
        'gpu_init': (120, 600),
        'hf_ball':  (30, 300),
        'H_build':  (900, 45 * 60),
        'eigh':     (300, 25 * 60),
    })
    d = np.load('/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore/data/'
                'h2o_ccpvtz_integrals.npz')
    n_orb = int(d['n']); n_occ = 5
    h_sp, t_sp, nuc = d['h'], d['t'], float(d['nuc'])
    e_ref = float(d['e_ccsdt'])
    from gpu_occ_aware_doubles_sp import GPUApplyOccAwareSP
    from geoqc.gpu import _get_global_gpu
    mon.phase('gpu_init')
    gpu_ctx, gpu_queue, _ = _get_global_gpu()
    gpu_apply = GPUApplyOccAwareSP(n_orb, n_occ, t_sp, eps=1e-4,
                                   chunk_size=32)
    s = SectorSystem(n_orb, n_occ, n_occ, h_sp, t_sp, nuc, eps=1e-4,
                     gpu_apply=gpu_apply)
    mon.phase('hf_ball')
    u, w = s.h_col(s.seed_idx)
    mon._log(f'full HF ball: {len(u)} members')
    des = Descent(s, h_chunk=200)

    # resume: which |V| checkpoints already exist?
    done = set()
    for p in glob.glob(os.path.join(NOTES, 'm2_fullball.ckpt-*.npz')):
        tag = os.path.basename(p).split('.ckpt-')[1].split('.npz')[0]
        done.add(tag)
    if done:
        mon._log(f'resume mode: existing checkpoints {sorted(done)}')

    results = []
    for frac in FRACTIONS:
        nv = int(len(u) * frac)
        tag = f'v{nv}'
        order = np.argsort(-np.abs(w))[:nv]
        V = np.sort(u[order])
        if tag in done:
            mon._log(f'skip {tag}: checkpoint exists')
            ck = load_checkpoint(NOTES, 'm2_fullball', tag)
            # recompute eigsh from the saved H? H may be too big to keep
            # for all tags at once; store eig result in a meta file.
            continue
        mon.phase('H_build', n_total=nv, note=f'|V|={nv} ({frac:.0%} ball)')
        H, H_cols = des._build_H(V, cache_cols=False)
        save_checkpoint(NOTES, 'm2_fullball', tag, {'H': H})
        mon.heartbeat(note=f'H saved ({tag}) H={H.shape}')
        mon.phase('eigh', note=f'|V|={nv}')
        ev, cv = eigsh(H, k=1, which='SA', maxiter=5000, tol=1e-7)
        ev = float(ev[0])
        err = (ev - e_ref) * 1000
        mon._log(f'|V|={nv:6d} ({frac:.0%} ball): E_var={ev:.8f} '
                 f'err={err:+.2f} mHa')
        results.append((nv, ev, err))
        del H, H_cols, cv
        import gc; gc.collect()

    mon.done(result=results)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
