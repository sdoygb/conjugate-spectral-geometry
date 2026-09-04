#!/usr/bin/env python3
"""H2O/cc-pVTZ natural-orbital (NO) basis builder + NO-basis discriminator.

Theory (10.86/10.87): a "barren/plateau or diffuse" appearance is a
tool-coordinate artefact.  10.87 §6.05 measured on N2/6-31G: the same FCI
ground state has eff-dim 160,423 in canonical RHF MOs but 555 in natural
orbitals (289x collapse; the "pseudo-multireference" vanishes).

This job:
  1. RHF + CCSD on H2O/cc-pVTZ (58 orbs) -> relaxed CCSD 1-RDM
  2. diagonalise -> natural orbitals (NOON sorted)
  3. transform integrals to the NO basis
  4. build the geoqc-format npz AND report NOON / orbital diagnostics
  5. (phase B, optional RESUME=2) run WCI/ball scan in the NO basis

Run under the watchdog:
  python3 scripts/_watch.py notes m2_nobasis \
      .venv311/bin/python3 -u geo10-15/scripts/m2_nobasis_build.py
"""
import os, sys, time
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore')
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore/examples')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))
import numpy as np
from pyscf import gto, scf, cc, ao2mo
from solver.runmon import RunMonitor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NOTES = os.path.join(ROOT, 'notes')
OUT = '/Users/oygb/Downloads/GeometryAI-Mac-Build/geocore/data/' \
      'h2o_ccpvtz_no_integrals.npz'


def main():
    mon = RunMonitor('m2_nobasis', NOTES, budget={
        'rhf': (60, 600), 'ccsd': (600, 2 * 3600), 'no_diag': (30, 300),
        'transform': (600, 3600), 'save': (60, 600),
    })
    # geometry: same as the canonical H2O cc-pVTZ dataset (verify E_RHF)
    mol = gto.M(atom='O 0 0 0; H 0.757 0.586 0; H -0.757 0.586 0',
                basis='cc-pvtz', verbose=0)
    mf = scf.RHF(mol)
    mon.phase('rhf')
    mf.kernel()
    e_rhf = mf.e_tot
    e_can_ref = -76.057160680627   # from h2o_ccpvtz_integrals.npz
    mon._log(f'RHF E={e_rhf:.10f}  canonical-ref={e_can_ref:.10f} '
             f'|diff|={abs(e_rhf - e_can_ref):.2e}')
    assert abs(e_rhf - e_can_ref) < 1e-6, 'geometry mismatch!'

    mon.phase('ccsd')
    mycc = cc.CCSD(mf)
    mycc.verbose = 0
    mycc.kernel()
    e_ccsd = mycc.e_tot
    mon._log(f'CCSD E_tot={e_ccsd:.8f}  '
             f'(CCSD(T) ref = -76.3457672654)')
    mon._log('computing relaxed 1-RDM ...')
    ldm1 = mycc.make_rdm1()          # relaxed, AO basis
    dm1 = np.asarray(ldm1) + np.asarray(ldm1).T.conj()
    dm1 = (dm1 + dm1.T) / 2.0        # symmetrise

    # natural orbitals in the RHF MO basis
    mon.phase('no_diag')
    C = mf.mo_coeff
    dm_mo = C.T @ dm1 @ C            # in canonical MO basis
    dm_mo = (dm_mo + dm_mo.T) / 2.0
    ev, U = np.linalg.eigh(dm_mo)
    order = np.argsort(ev)[::-1]
    noon = ev[order]
    U = U[:, order]
    mon._log('NOON (sorted):')
    for i in range(0, len(noon), 8):
        mon._log('  ' + ' '.join(f'{x:.4f}' for x in noon[i:i+8]))
    mon._log(f'#NOON>1.9 = {(noon > 1.9).sum()}, '
             f'#NOON>0.02 = {(noon > 0.02).sum()}, '
             f'#NOON>1e-3 = {(noon > 1e-3).sum()}, '
             f'#NOON>1e-4 = {(noon > 1e-4).sum()}')

    # transform integrals into NO basis (spatial, chemist-free)
    mon.phase('transform')
    h1e = C.T @ mf.get_hcore() @ C
    eri = ao2mo.kernel(mol, C, compact=False).reshape(
        mol.nao_nr(),) * 0 + 0     # placeholder; build properly below
    # (eri in canonical MOs via ao2mo)
    eri = ao2mo.kernel(mol, C, compact=False).reshape(
        mol.nao_nr(), mol.nao_nr(), mol.nao_nr(), mol.nao_nr())
    h1e_NO = U.T @ h1e @ U
    eri_NO = np.einsum('pqrs,pi,qj,rk,sl->ijkl', eri,
                       U, U, U, U, optimize=True)
    nuc = mol.energy_nuc()
    mon._log(f'NO integrals: h1e_NO {h1e_NO.shape}, '
             f'eri_NO {eri_NO.nbytes/1e6:.0f} MB')

    mon.phase('save')
    np.savez(OUT, n=mol.nao_nr(), h=h1e_NO, t=eri_NO, nuc=nuc,
             e_rhf=e_rhf, e_ccsdt=-76.3457672654, noon=noon)
    mon._log(f'saved {OUT}')
    mon.done(result={'e_rhf': e_rhf, 'e_ccsd': e_ccsd, 'noon_top':
                     noon[:12].tolist()})


if __name__ == '__main__':
    main()
