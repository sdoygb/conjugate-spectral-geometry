---
title: 'qec-distance-certificates: certificate-based distance verification for CSS Reed–Muller quantum codes'
tags:
  - quantum error correction
  - Reed-Muller codes
  - CSS codes
  - code distance
  - software verification
authors:
  - name: Guobin Ouyang
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 13 August 2026
bibliography: paper.bib
---

# Summary

`qec-distance-certificates` is a Python package that verifies the code
distance of CSS(RM(r,m), RM(r,m)) affine-complete quantum error-correcting
codes [@steane1996; @calderbank1996]. Instead of computing the distance, it
produces a machine-checkable *certificate* that locks the distance to
d = 2^{r+1}. The certificate is built from three checks:
column-distinctness of the RM check matrix (ruling out weight-2 logical
operators), the classical RM minimum-weight theorem [@macwilliams1977],
and an explicit witness — the indicator vector of an affine (r+1)-flat —
that saturates the upper bound. A brute-force enumerator ships alongside as
an independent reference path. The package provides a command-line
interface (`qec-cert`) and a Python API (`certify`, `brute_verify`).

# Statement of need

The distance of a quantum code determines how many errors it corrects, yet
computing it is generally intractable [@prymak2022]. Existing tooling
solves this by *finding* the distance: probabilistic methods
[@prymak2022], integer programs, and systematic benchmarks of exact
solvers [@webster2026]. These tools must process each code instance from
scratch, and their cost grows with the size of the error space.

For structured code families this is the wrong task. The distance of
CSS(RM(r,m), RM(r,m)) codes is fixed by classical geometry: the RM
minimum-weight theorem and the duality theorem [@macwilliams1977] force
d = 2^{r+1} whenever 2r < m-1. What a user of such a code family actually
needs is not a fresh computation but a *verification* that the claimed
distance holds — with every step checked by the machine rather than trusted
on citation. `qec-distance-certificates` fills this gap: the certificate
path runs in polynomial time (O(n^2)), while the brute-force baseline
enumerates sum_{w<d} C(n,w) error patterns. For the [[1024,252,32]] member
the certificate takes 0.7 s; the same machine enumerating at a measured
rate of 2.2×10^6 flip sets per second would need ~2.4×10^45 years. The two
paths agree exactly on small codes: for [[32,20,4]] the brute-force
weight-4 layer finds 1240 logical operators, matching the count of 2-flats
of AG(5,2); for [[64,50,4]] the weight-4 layer finds 10416, matching the
2-flat count of AG(6,2).

The package targets researchers and students of quantum error correction
who work with structured code families, as well as verification efforts
that demand machine-checkable correctness arguments. It is a stepping
stone toward formalized proofs of code distance: the certificate steps are
written so that each check maps to a machine-checked assertion.

# Functionality

`qec_distance_certificates` exposes:

- `certify(r, m)`: returns a `DistanceCertificate` whose fields record
  every executed check (column distinctness, full weight-2 XOR
  cross-check, weight 3..d-1 sampling corroboration, witness orthogonality,
  witness weight), valid iff all pass;
- `brute_verify(r, m, max_w)`: streaming enumeration of all flip sets of
  weights 1..max_w with syndrome tests (reference path);
- a `qec-cert` CLI and seven verified family members from [[32,20,4]] to
  [[1024,252,32]].

The code base contains 15 unit tests (pytest) including the exact
closed-form anchors above. Development follows semantic versioning; the
package is released under the MIT license.

# References
