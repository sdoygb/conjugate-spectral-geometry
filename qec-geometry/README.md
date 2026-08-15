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

### Phase 2: distance scaling law (L = 4, 6, 8)

As the code distance L grows (fixed physical noise p = 0.005), the **absolute**
topological signal survives and scales linearly with L:

| L | p_L | A0 total_dist | A1 total_dist | **A1 − A0** | A1/A0 | A1 long-chain rate |
|---|---|---|---|---|---|---|
| 4 | 1.48% | 2.0 | 6.0 | **4.0 = L** | 3.00× | 12.9% |
| 6 | 0.49% | 8.0 | 14.0 | **6.0 = L** | 1.75× | 33.9% |
| 8 | 0.17% | 16.0 | 24.0 | **8.0 = L** | 1.50× | 51.2% |

**Scaling law: A1_total_dist − A0_total_dist = L.** The logical-error pairing
chain carries an extra contribution of exactly one code distance — the geometric
cost of the non-trivial homology class (Berry phase 2π). Meanwhile the *ratio*
decays (3.00× → 1.50×) because the local-error background grows as ∝ L²
(error count ∝ code area) and dilutes the relative signal.

Two further consequences:

- **Explicit long chains become more common with L**: the fraction of A1
  samples with a pairing edge ≥ 4 grows 12.9% → 33.9% → 51.2% (answering the
  open question of article 10.54 §6.3).
- **Seed reproducibility**: median features are identical across seeds
  42/123/777 at every L (deterministic sampling via
  `compile_detector_sampler(seed=...)`).

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
python3 scripts/phase2_scaling.py --scan        # Phase 2: L=4/6/8 × 3 seeds scaling
python3 -m unittest tests.test_qecgeo -v        # 14 tests
```

---

## Validation

- **Threshold closed form**: exact enumeration over all weight-2 errors for
  [[5,1,3]], [[7,1,3]], [[15,7,3]]; Monte Carlo verification of the quadratic
  law; concatenation compression p_{L+1} = A·p_L² shown for p0 = 0.001/0.01/0.05.
- **Error geometry (Phase 1)**: 20,000 samples at p = 0.005 (L=4 surface code),
  the 3.00× total_dist separation is stable across runs.
- **Error geometry (Phase 2 scaling)**: L = 4/6/8 × seeds 42/123/777 at p = 0.005,
  30k–600k shots per point; scaling law A1 − A0 = L exact (4.0/6.0/8.0);
  long-chain rate 12.9% → 51.2%; seed-stable medians (results in `data/phase2/`).
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
- Surface-code geometry was characterized for L = 4/6/8 (one code family);
  crossing-rate statistics fluctuate at the few-percent level with shot count
  (1.2–2.1× range). The relative separation (A1/A0) decays with L (background
  dilution); the absolute scaling law (A1 − A0 = L) is the robust observable.

## Theory source

The A0/A1 classification, threshold closed form, and anyon typing derive from
the Geometric Theory of quantum error correction (Ouyang Guobin):

- Article 10.27 — geometric code construction [[5,1,3]], [[7,1,3]], [[9,1,3]]
- Article 10.44 — threshold closed form p_th = 1/(η·C(n,2)), Ising anyon typing
- Article 10.54 — error-pattern geometry: A0/A1 pairing-layer separation

## License

MIT © 2026 Ouyang Guobin
