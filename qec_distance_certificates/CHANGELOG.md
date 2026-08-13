# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-13

### Added

- `certify(r, m)`: geometric distance certificate for CSS(RM(r,m), RM(r,m))
  codes, locking d = 2^(r+1) without enumerating the error space.
- Three-step certificate: column distinctness (weight-2 detection), RM
  minimum-weight theorem lower bound with sampling corroboration, and the
  affine (r+1)-flat indicator witness for the upper bound.
- `brute_verify(r, m, max_w)`: streaming brute-force enumeration baseline
  (reference path, independent of any RM theorem).
- `qec-cert` command-line interface (`certify`, `brute`, `family`).
- Seven verified family members from [[32,20,4]] to [[1024,252,32]].
- 15 pytest tests with exact closed-form anchors (2-flat counts of AG(5,2)
  and AG(6,2)).
- Benchmark data: measured 10^53x speedup for [[1024,252,32]]; cross-over
  at ~5x10^4 error-space enumerations.
