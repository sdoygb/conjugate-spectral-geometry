# qec-geometry

**Geometric diagnostics for quantum error correction codes.**

A zero-dependency Python toolkit that classifies decoding error patterns by their
topology (A0: local / trivial, A1: non-trivial crossing chains) and predicts
fault-tolerance thresholds from a closed-form formula.

```
qecgeo  ──  Pauli algebra ── stabilizer framework ── code zoo ── error geometry ── threshold closed form ── anyon typing
```

---

## What it does

### 1. Error-pattern geometry: A0/A1 classification (surface code)

After MWPM decoding of a surface code, every sampled error pattern is classified:

| class | meaning | topology |
|---|---|---|
| **A0** | correctable, local error chains | trivial (Berry phase 0) |
| **A1** | logical errors, chains crossing the code | non-trivial (Berry phase 2π) |

The MWPM **matching layer** separates the two classes sharply:

| feature | A0 median | A1 median | A1/A0 |
|---|---|---|---|
| `total_dist` (sum of pairing-edge lengths) | 2.00 | 6.00 | **3.00×** |
| `n_edges` | 3.00 | 5.00 | 1.67× |
| `cluster` (max excitation cluster) | 2.00 | 4.00 | 2.00× |
| crossing rate | 22% | 47% | 2.1× |

The A1/A0 separation **appears below threshold** (p ≈ 0.005 < p_th ≈ 0.011 for
the surface code): at low noise, logical error chains carry a measurable
topological signature in the pairing layer. At high noise the error patterns
lose structure and the distinction vanishes.

### 2. Fault-tolerance threshold: closed form

For single-round optimal decoding with depolarizing noise, the logical error
rate obeys the quadratic law

```
p_L(p) ≈ A·p²,    A = η·C(n,2),    p_th = 1/A
```

where η = fraction of weight-2 errors mis-recovered as logical operators
(exactly enumerated). Verified values:

| code | η | A | p_th |
|---|---|---|---|
| [[5,1,3]] five-qubit | 1.000 | 10.00 | 10.00% |
| [[7,1,3]] Steane | 0.3333 | 7.00 | 14.29% |
| [[15,7,3]] RM(1,4) CSS | 0.3333 | 35.00 | 2.86% |

Monte Carlo confirms p_L ≈ A·p² at low p (ratio ≈ 0.87 at p = 0.01, [7,1,3]).

### 3. Anyon typing

The δ = Cl(8) Majorana 8-cycle permutation closes with zero net phase
(δ⁸ ≡ 0 mod 2π, consistent with the Berry phase 2π) — an **Ising (Majorana)
type** anyon signature, not Fibonacci.

---

## Install & use

```bash
pip install numpy          # only hard dependency
pip install stim pymatching  # needed only for the surface-code demo
```

```python
from qecgeo.codes import steane_code
from qecgeo.threshold import analyze_eta

r = analyze_eta(steane_code())
print(r['eta'], r['p_th'])   # 0.3333, 0.1429
```

Surface-code error geometry (reproduces the 3.00× separation):

```bash
cd qec-geometry
python3 scripts/demo_error_geometry.py          # L=4, noise=0.005, 20000 shots
python3 scripts/demo_threshold.py               # η enumeration + MC + anyon
python3 -m unittest tests.test_qecgeo -v        # 14 tests
```

---

## Validation

- **Threshold closed form**: exact enumeration over all weight-2 errors for
  [[5,1,3]], [[7,1,3]], [[15,7,3]]; Monte Carlo verification of the quadratic
  law; concatenation compression p_{L+1} = A·p_L² shown for p0 = 0.001/0.01/0.05.
- **Error geometry**: 20,000 samples at p = 0.005 (L=4 surface code), 318 logical
  errors analyzed; the 3.00× total_dist separation is stable across runs.
- All numerical results are stored in `data/` (JSON) and reproduced by the
  scripts above.

## Honest limitations

- The A0/A1 geometric separation is a **sub-threshold phenomenon**: at noise
  above threshold the error patterns lose structure and the distinction
  vanishes. It is a diagnostic of the *decoding error topology*, not a decoder
  itself.
- Threshold closed form is a **single-round, memoryless optimal-decoding model**
  — it does not capture circuit-level noise correlations or multi-round
  propagation. Real circuit thresholds differ (typically lower).
- [[5,1,3]] has η = 1 (all weight-2 errors are mis-recovered): its p_th = 10%
  is an upper-bound estimate in this model, not a practical circuit threshold.
- Surface-code geometry was characterized at a single size (L=4) and code
  family; crossing-rate statistics fluctuate at the few-percent level with shot
  count (1.9–2.1× range).

## Theory source

The A0/A1 classification, threshold closed form, and anyon typing derive from
the Geometric Theory of quantum error correction (Ouyang Guobin):

- Article 10.27 — geometric code construction [[5,1,3]], [[7,1,3]], [[9,1,3]]
- Article 10.44 — threshold closed form p_th = 1/(η·C(n,2)), Ising anyon typing
- Article 10.54 — error-pattern geometry: A0/A1 pairing-layer separation

## License

MIT © 2026 Ouyang Guobin
