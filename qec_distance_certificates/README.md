# qec-distance-certificates

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21916476.svg)](https://doi.org/10.5281/zenodo.21916476)

**Certificate-based distance verification for CSS(RM) affine-complete quantum codes — distance-certifying, not distance-finding.**

> When the distance is a theorem, stop computing it — verify it.

## Positioning

The distance d = 2^(r+1) of CSS(RM(r,m), RM(r,m)) affine-complete quantum
codes is fixed by geometric structure (the RM minimum-weight theorem and the
duality theorem, classical results). This package produces a
**machine-checkable distance certificate** at **O(n²) polynomial cost**; the
brute-force enumeration baseline costs sum_{w<d} C(n,w) (exponential in n).

Unlike distance-finding tools (brute force / ILP / Brouwer-Zimmermann, see
arXiv:2603.22532), this package does not "compute" the distance. For
structured code families it **verifies** the distance, emitting a certificate
of machine-checked steps.

## Installation

```bash
pip install -e .          # editable install (local)
```

Dependencies: numpy >= 1.24, Python >= 3.9.

## Usage

### Command line

```bash
qec-cert certify -r 2 -m 6          # [[64,20,8]] distance certificate
qec-cert certify -r 4 -m 10         # [[1024,252,32]] distance certificate
qec-cert brute -r 1 -m 5 --max-w 4  # brute-force reference (all weights <= 4)
qec-cert family                     # list verified family members
```

### Python API

```python
from qec_cert import certify, brute_verify

cert = certify(r=2, m=6)                  # [[64,20,8]]
print(cert.summary())
# [[64,20,8]] certificate VALID (cols_distinct=True, w2_undetected=0, ...)

layers = brute_verify(r=1, m=5, max_w=4)  # [[32,20,4]] full closure
assert layers[4]["undetected"] == 1240    # weight-4 logicals = AG(5,2) 2-flats
```

## Certificate contents

Every step of `DistanceCertificate` is a machine check, not a theorem to be
trusted:

| Step | Check | Justification |
|---|---|---|
| (1) | Column distinctness (O(n)) | Column distinctness ⟺ all weight-2 errors detected (structural criterion, Thm. 10.30.2.01) |
| (1') | Full weight-2 column-pair XOR | Machine-level cross-check (O(n²) column pairs, not an error enumeration) |
| (2) | Lower bound d ≥ 2^(r+1) | RM minimum-weight theorem + self-orthogonality 2r < m−1; weight 3..d−1 sampling corroboration |
| (3) | Upper bound d ≤ 2^(r+1) | Certificate w_F: indicator vector of an affine (r+1)-flat in C⊥∖C, \|w_F\| = 2^(r+1) |

## Benchmark (same machine, same implementation, measured)

| Code | n | d | Brute-force enumerations | Brute-force time | Certificate (measured) | Speedup |
|---|---|---|---|---|---|---|
| [[32,20,4]] | 32 | 4 | 5.5×10³ | 0.0s measured | 0.02s | 0.1× (brute wins) |
| [[64,50,4]] | 64 | 4 | 4.4×10⁴ | 0.0s measured | 0.02s | 0.6× (brute wins) |
| [[64,20,8]] | 64 | 8 | 7.0×10⁸ | 5.3min measured | 0.03s | 1.2×10⁴× |
| [[128,70,8]] | 128 | 8 | 1.0×10¹¹ | 12.7h extrapolated | 0.03s | 1.4×10⁶× |
| [[256,70,16]] | 256 | 16 | 7.1×10²³ | 1.0×10¹⁰ yr | 0.07s | 4.4×10¹⁸× |
| [[512,252,16]] | 512 | 16 | 2.8×10²⁸ | 4.1×10¹⁴ yr | 0.17s | 7.5×10²²× |
| [[1024,252,32]] | 1024 | 32 | 1.7×10⁵⁹ | 2.4×10⁴⁵ yr | 0.70s | 1.1×10⁵³× |

Cross-over: around 5×10⁴ error-space enumerations (n=64, between d≈4 and 5).
Beyond the cross-over the speedup is proportional to the enumeration size
(fit slope 0.97): the certificate path compresses the exponential enumeration
into constant time. Measured brute-force rate ~2.2×10⁶ flip/s (Mac, Python 3.9,
numpy vectorization).

## References

- G. Ouyang, *Affine-complete RM/CSS codes: enumeration-free verification* (in preparation).
- R. MacWilliams, N. Sloane, *The Theory of Error-Correcting Codes*, Ch. 13
  (RM minimum-weight and duality theorems).

## License

MIT
