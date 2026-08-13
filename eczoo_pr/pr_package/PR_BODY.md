## Title

`quantum_reed_muller`: add self-orthogonal CSS(RM(r,m), RM(r,m)) family and its certified distance

## Description

This PR adds to the quantum Reed-Muller entry:

1. The CSS(RM(r,m), RM(r,m)) family (self-orthogonal for 2r < m-1), with explicit parameters [[2^m, 2^m - 2·Σ_{j≤r} C(m,j), 2^(r+1)]] and the distance derivation from the RM minimum-weight theorem (MacWilliams-Sloane, Ch. 13).
2. A `distance` feature noting that the distance of this family admits a certificate checkable without enumerating the exponentially many error patterns: for r ≥ 1, column-distinctness of the RM check matrix (no weight-2 logicals), the RM minimum-weight theorem (no intermediate weights), and affine (r+1)-flat indicators as weight-2^(r+1) vectors in RM(m-r-1,m) \ RM(r,m) saturating the bound.

## Checklist

- [x] `_meta.changelog` updated (user_id: oygb, 2026-08-13)
- [x] User entry added in `users/users_db.yml`
- [x] YAML syntax validated locally
- [ ] Previewed via https://errorcorrectionzoo.org/gitpreview

## Verification note

Family parameters and the certificate were verified numerically for members
[[32,20,4]], [[64,50,4]], [[64,20,8]], [[128,70,8]], [[256,70,16]], [[512,252,16]], [[1024,252,32]]:
weight-4 layer counts (1240 and 10416) match the affine-flat counting formula exactly, and
[[64,20,8]] passed a full brute-force check of all 7.05e8 error sets of weight 1..7 with zero undetected.
