# qec-geometry — Validation Report

All numbers below are produced by the scripts in this repository
(`scripts/demo_threshold.py`, `scripts/demo_error_geometry.py`) and stored in
`data/*.json`. Theory source: Geometric Theory of QEC (Ouyang Guobin),
articles 10.27 / 10.44 / 10.54.

---

## 1. Threshold closed form (Article 10.44)

### 1.1 Exact enumeration of η

For a stabilizer code with n physical qubits under depolarizing noise
(p/3 per X/Y/Z channel), the leading logical error rate is

```
p_L(p) ≈ A·p²,   A = η·C(n,2),   η = (weight-2 errors mis-recovered as logical)/total weight-2 errors
```

All non-trivial weight-2 Pauli errors (9 types per pair of coordinates) are
enumerated; each is classified by whether table-lookup recovery (built from
single-qubit syndromes) leaves a logical operator.

| code | n | weight-2 errors | same syndrome as single | mis-recovered | η | A | p_th = 1/A |
|---|---|---|---|---|---|---|---|
| [[5,1,3]] five-qubit | 5 | 90 | 90 (100%) | 90 (100%) | 1.000 | 10.00 | 10.00% |
| [[7,1,3]] Steane | 7 | 189 | 63 (33.3%) | 63 (33.3%) | 0.3333 | 7.00 | 14.29% |
| [[15,7,3]] RM(1,4) CSS | 15 | 945 | 315 (33.3%) | 315 (33.3%) | 0.3333 | 35.00 | 2.86% |

Notes:
- All weight-2 errors of [[5,1,3]] share a syndrome with a single-qubit error
  and all are mis-recovered → η = 1. Its p_th = 10% is a model upper bound.
- [[7,1,3]] and [[15,7,3]] share η = 1/3; the factor C(n,2) makes the RM code's
  threshold 5× lower than Steane's.
- Every mis-recovered error leaves a weight-3 logical residual in these codes
  (column `resid_w3` equals `misrecovered` for all three).

### 1.2 Monte Carlo verification of the quadratic law ([7,1,3])

300k trials per p, single-round optimal decoding, seed = 42:

| p | p_L (measured) | A·p² | p_L/(A·p²) |
|---|---|---|---|
| 0.01 | 6.03e-4 | 7.00e-4 | 0.86 |
| 0.03 | 5.48e-3 | 6.30e-3 | 0.87 |
| 0.05 | 1.38e-2 | 1.75e-2 | 0.79 |
| 0.08 | 3.16e-2 | 4.48e-2 | 0.71 |
| 0.10 | 4.56e-2 | 7.00e-2 | 0.65 |
| 0.14 | 7.52e-2 | 1.37e-1 | 0.55 |
| 0.20 | 1.21e-1 | 2.80e-1 | 0.43 |

The ratio approaches 1 as p → 0 (0.86–0.87 at p ≤ 0.03), confirming the
quadratic law at low noise; at higher p the O(p³) corrections and saturation
toward p_L → 1/2 take over (ratio decreases monotonically).

### 1.3 Concatenation compression

p_{L+1} = A·p_L² for [7,1,3] (A = 7, p_th = 0.1429):

```
p0 = 0.001: 1.0e-03 → 7.0e-06 → 3.4e-10 → 8.2e-19 → 4.8e-36
p0 = 0.01 : 1.0e-02 → 7.0e-04 → 3.4e-06 → 8.2e-11 → 4.8e-20
p0 = 0.05 : 5.0e-02 → 1.8e-02 → 2.1e-03 → 3.2e-05 → 7.2e-09
```

Below threshold, each concatenation level squares the error rate.

---

## 2. Error-pattern geometry (Article 10.54)

### 2.1 Setup

- Surface code `surface_code:unrotated_memory_z`, L=4, rounds=3
- Uniform depolarizing/measurement noise p = 0.005 (< threshold ≈ 0.011)
- 20,000 shots; MWPM decoding (PyMatching 2.4, Stim 1.15)
- Logical error rate p_L = 0.016 (318 logical errors, 19,682 correctable)

### 2.2 Excitation-layer features (A0 vs A1)

| feature | A0 med | A0 q90 | A1 med | A1 q90 | A1/A0 |
|---|---|---|---|---|---|
| exc (excitation count) | 5.0 | 9.0 | 9.0 | 14.0 | 1.80 |
| min_pair (nearest pair dist) | 2.0 | 4.0 | 2.0 | 2.0 | 1.00 |
| diam (spatial diameter) | 4.0 | 8.0 | 6.0 | 10.0 | 1.50 |
| cluster (max cluster) | 2.0 | 4.0 | 4.0 | 7.0 | 2.00 |
| crossing rate | 22.3% | — | 47.2% | — | 2.12× |

### 2.3 Matching-layer (pairing edge) features — the separating layer

| feature | A0 med | A0 q90 | A1 med | A1 q90 | A1/A0 |
|---|---|---|---|---|---|
| n_edges | 3.00 | 5.00 | 5.00 | 8.00 | **1.67** |
| total_dist (sum of edge lengths) | 2.00 | 6.00 | 6.00 | 10.00 | **3.00** |
| max_dist | 2.00 | 2.00 | 2.00 | 4.00 | 1.00 |
| long_rate (max_dist ≥ 4) | 0.00 | 0.00 | 0.00 | 1.00 | — |

The **matching layer is the strongest separator**: total_dist A1/A0 = 3.00×,
while the single-longest-edge (max_dist) has no separation (medians equal).
The A1 signature is carried by the *total chain length* across several
moderate edges, not by one exceptionally long edge. This is the geometric
content of the logical error: a non-trivial chain winding around the code.

### 2.4 Sub-threshold condition

At p = 0.03 (above threshold, p_L = 0.38) all separation vanishes
(total_dist A1/A0 = 1.00, crossing lift = 1.02×): the error patterns lose
structure near random guessing. The A0/A1 geometric distinction is a
**sub-threshold diagnostic**.

---

## 3. Anyon typing (Articles 10.43/10.44)

δ = Cl(8) Majorana 8-cycle = 7 adjacent transpositions; each transposition
carries the Ising (Majorana) exchange phase e^{±iπ/4}:

- δ net phase = 7·π/4 = 5.4978 rad = e^{i7π/4}
- δ⁸ net phase = 14π ≡ 0 (mod 2π) → loop closes with zero phase,
  consistent with the Berry phase 2π
- **Verdict: Ising (Majorana) type anyon statistics, not Fibonacci.**

---

## 4. Reproducibility

```bash
python3 scripts/demo_threshold.py            # Section 1 + 3
python3 scripts/demo_error_geometry.py       # Section 2
python3 -m unittest tests.test_qecgeo -v     # 14 unit tests
```

Unit tests cover: Pauli multiplication table, symplectic orthogonality,
code construction self-checks (commutation, independence), distance = 3 for
all three geometric codes, logical-zero stabilization, encode-correct-fidelity,
η enumeration sanity (total = C(n,2)·9), MC quadratic law (ratio ≈ 1 ± 0.15),
δ⁸ closure, Ising typing.

Environment: Python 3.9, numpy, Stim 1.15.0, PyMatching 2.4.0.
