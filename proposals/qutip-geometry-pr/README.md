# qutip-geometry (PR skeleton)

Parameter-space Berry curvature and Chern number tools for the QuTiP
ecosystem.

This is the reference implementation accompanying the feature request
`proposals/qutip-berry-toolbox-issue.md`. It is a skeleton: the
numerical core is complete and tested, and the Qobj-based public API is
in place. Vectorization of the mesh loops is intentionally left as a
follow-up.

## API

```python
from qutip_geometry import berry_curvature, chern_number, nonabelian_chern_number

# h_func(v1, v2) -> Qobj, a Hermitian Hamiltonian family.
theta = np.linspace(0, np.pi, 33)          # open axis (spherical mesh)
phi = np.linspace(0, 2 * np.pi, 32, endpoint=False)  # periodic axis

F = berry_curvature(h_func, theta, phi, band=0, wrap1=False, wrap2=True)
C = chern_number(h_func, theta, phi, band=0, wrap1=False, wrap2=True)
C_deg = nonabelian_chern_number(h_func, theta, phi, bands=[0, 1],
                                wrap1=False, wrap2=True)
```

- `berry_curvature`: plaquette field strengths via the
  Fukui-Hatsugai-Suzuki link-variable formula; `F.sum() == 2*pi*C`.
- `chern_number`: the band Chern number.
- `nonabelian_chern_number`: joint Chern number of a degenerate
  subspace via the projector (overlap-matrix) method; gauge invariant
  under arbitrary subspace-basis rotations.

All outputs are gauge invariant by construction (link variables absorb
eigenstate phases; overlap matrices absorb subspace-basis rotations).

## Test cases

| Test | Content | Expected |
|---|---|---|
| `test_monopole.py` | inverted monopole on S^2, several resolutions, gauge invariance | C = +1 |
| `test_three_sector_zero_sum.py` | three sectors with Chern numbers (+1, +1, -2) | C_A + C_B + C_C = 0 |
| `test_nonabelian.py` | two degenerate monopole copies, lifted and exactly degenerate, basis-rotation invariance | C = +2 |

## Running

```bash
python3 -m pytest tests/ -q
```

## Notes for maintainers

- The FHS mesh handling supports open and periodic axes independently
  (`wrap1`, `wrap2`), covering spherical and toroidal parameter spaces.
- A pitfall we hit while validating the test cases: forgetting periodic
  wrapping on a torus axis drops an entire row of plaquettes, producing
  an O(1/N) slow drift away from the integer Chern number. The
  zero-sum test case catches exactly this class of bug, because the
  defect breaks the global constraint even when each sector looks
  roughly integer.
