# Topological Superconductivity Screening by Space-Group Symmetry

**A zero-cost, first-pass filter: which crystal structures can host topological superconductivity?**

Given only a space group number (1–230), this tool applies a symmetry
criterion to answer one question: *can this material be a topological
superconductor candidate at all?* The answer takes ~1 microsecond and
requires no electronic-structure calculation.

- **Criterion**: Theorem 9.1.12.01 from the *Geometric Theory of
  Superconductivity* (Ouyang, 2026; article 9.1).
- **Input**: space group number (or point group symbol).
- **Output**: `CANDIDATE` / `EXCLUDED`, with a human-readable explanation.
- **Dependencies**: none (pure Python standard library).

---

## The criterion

A necessary condition for topological superconductivity is that the crystal
point group contains **both**:

1. a **C₃ rotation** (threefold axis), and
2. a **Z₂ symmetry** (mirror plane or spatial inversion).

Equivalently, the lattice symmetry group commutes with the triality
permutation: `[G_lattice, T] = 0`.

This reduces the 32 crystallographic point groups to **11 candidates**:

```
D6h  D3h  D3d  Oh  Td  C3i  C3v  C3h  C6h  C6v  Th
```

corresponding to **52 of the 230 space groups (22.6%)**.

Point groups that contain C₃ but *lack* Z₂ (C3, D3, C6, D6, T, O) are
excluded, as are all groups without a threefold axis (e.g. D4h, D2h — the
point groups of most cuprates and iron-based superconductors).

> **Important**: this is a *necessary* condition — a first-level screen.
> It does **not** predict superconductivity by itself. Candidates must still
> pass the full three-question test (topological surface states
> K̃⁰ ≠ 0; effective channel count N_eff ≥ 3; magnetic ordering compatible
> with pairing). See the full theory in article 9.1, §11–§12.

---

## Quick start

```bash
# Python 3.8+, no dependencies
python screening.py 194          # CANDIDATE  (P6_3/mmc, D6h  -> UPt3)
python screening.py 139          # EXCLUDED   (I4/mmm, D4h    -> Sr2RuO4)
python screening.py 166          # CANDIDATE  (R-3m, D3d      -> Bi2Se3)
python screening.py 47           # EXCLUDED   (Pmmm, D2h      -> YBCO)

python screening.py --list       # the 52 candidate space groups
python screening.py --selfcheck  # built-in regression tests (12/12)
```

As a library:

```python
from screening import is_candidate, sg_to_pointgroup, explain

is_candidate(194)      # True   (UPt3-type: D6h)
is_candidate(129)      # False  (FeSe-type: D4h)
sg_to_pointgroup(216)  # 'Td'   (half-Heusler)
print(explain(71))     # EXCLUDED -- lacks C3 rotation (no 3-fold axis)
```

---

## Validation

Three independent validation layers, all passing.

### Layer 1 — 94 known superconductors (independent list)

94 known superconductors from Wikipedia's *List of superconductors*
(independently fetched, not from the theory's article set).

| Outcome | Count | Fraction |
|---|---|---|
| Space group is a candidate | 70 | 74.5% |
| Space group is excluded | 24 | 25.5% |

**All 24 excluded cases are accounted for by non-topological pairing
paths** — none is an established topological superconductor:

- 5 type-I BCS elements (Ga, In, Pa, Sn, U) — bulk BCS (S1 path)
- 6 cuprates (YBCO, BSCCO, HBCCO, 214…) — d-wave, non-topological
- 8 iron-based (1111, 122, 11 families) — s± spin fluctuation
- 1 nickelate (La₃Ni₂O₇) — non-topological
- FeB₄ — weak-coupling BCS
- Sr₂RuO₄, UTe₂ — **exclusion predictions** of the criterion
  (criterion says: not topological; Sr₂RuO₄ consistent with 2021–2024
  experiments; UTe₂ still under active experimental debate)

**All established topological superconductor candidates pass** (100%
coverage): Bi₂Se₃ family, Bi₂Te₃/Sb₂Te₃, MnBi₂Te₄, SnTe (TCI), YPtBi /
LuPtBi / LaPtBi (half-Heusler), UPt₃, PrOs₄Sb₁₂, Bi₂Pd (γ-phase, Fd-3m).

### Layer 2 — Materials Project full database (154,377 compounds)

Query of the Materials Project API (2026-08): of 154,377 materials,

- **41,077 (26.61%)** fall in the 52 candidate space groups
- **113,300 (73.39%)** are excluded at the symmetry level alone

This quantifies the *selectivity* of the first-level screen: roughly 3 of 4
materials are removed by symmetry before any electronic-structure work.

### Layer 3 — 22 key materials, independent confirmation via MP

For 22 landmark materials, the space group assigned by the Materials
Project (independent DFT database) was checked against the criterion:

| Material | MP space group | Criterion |
|---|---|---|
| Bi₂Se₃ / Bi₂Te₃ / Sb₂Te₃ | R-3m (166) | CANDIDATE ✅ |
| MnBi₂Te₄ | R-3m (166) / P-3m1 (164) | CANDIDATE ✅ |
| SnTe | Fm-3m (225) | CANDIDATE ✅ |
| YPtBi / LuPtBi | F-43m (216) | CANDIDATE ✅ |
| UPt₃ | P6₃/mmc (194) | CANDIDATE ✅ |
| PrOs₄Sb₁₂ | Im-3 (204) | CANDIDATE ✅ |
| MgB₂ | P6/mmm (191) | CANDIDATE ✅ |
| Nb₃Sn | Pm-3n (223) | CANDIDATE ✅ |
| Sr₂RuO₄ | I4/mmm (139) | EXCLUDED ✅ |
| UTe₂ | Immm (71) | EXCLUDED ✅ |
| YBa₂Cu₃O₇ | Pmmm (47) | EXCLUDED ✅ |
| FeSe | P4/nmm (129) | EXCLUDED ✅ |
| La₃Ni₂O₇ | Amam (63) | EXCLUDED ✅ |

Space groups of key materials were additionally cross-checked against the
Crystallography Open Database (COD).

---

## Honest limitations

1. **Necessary, not sufficient.** Passing the symmetry screen does not mean
   a material superconducts. Most candidates (fcc/hcp/bcc elements, A15
   compounds, MgB₂…) are ordinary BCS superconductors and are excluded at
   the topological-surface-state question (Q1).

2. **Applicability domain.** The criterion targets the C₃-protected Dirac
   cone / helical-state route to topological superconductivity. Materials
   whose topological character comes from *other* mechanisms (e.g. Weyl-type
   band crossings such as 2M-WS₂, space group C2/m (12)) fall outside this
   domain — they are not counterexamples, but the domain must be stated
   explicitly.

3. **UTe₂ is a live risk.** The criterion predicts UTe₂ (Immm, D2h) is not
   a topological superconductor. Since 2019 UTe₂ has been the most actively
   debated spin-triplet topological superconductor candidate; surface-state
   observations were reported in 2024. This is the single most important
   open experimental question for the criterion.

4. **Phase identification matters.** The criterion applies to the specific
   superconducting phase. Polymorphs may fall on different sides (e.g. Bi₂Pd:
   γ-Fd-3m is a candidate, while the MP-listed C2/m and I4/mmm phases are
   not). Always screen the experimentally determined superconducting phase.

---

## Theory source

The criterion is Theorem 9.1.12.01 of the **Geometric Theory of
Superconductivity** (共扼谱几何 · 超导几何理论, article 9.1, Ouyang Guobin,
2026), where it is derived from the spectral-geometric framework:
`[G_lattice, T] = 0` with T the triality 3-cycle and the Z₂ interchange.
The full three-question criterion (Q1: topological surface states K̃⁰ ≠ 0;
Q2: N_eff ≥ 3 from irreducible representations of the nanowire cross-section
point group; Q3: magnetic compatibility) is developed in article 9.1,
§11–§12. The screening rule presented here is the symmetry-only fragment,
extracted so it can be validated and reused independently.

**Citation suggestion:**

> Ouyang, G. *Geometric Theory of Superconductivity*, article 9.1, Theorem
> 9.1.12.01 (2026). Symmetry screening criterion for topological
> superconductivity candidates.

---

## Repository layout

```
screening.py            core criterion (space group -> verdict), zero deps
data/materials_94.csv   94 known superconductors used in Layer-1 validation
data/mp_sg_stats.json   Materials Project counts per candidate space group
scripts/validate_wiki.py  Layer-1 reproduction script (needs spglib)
scripts/query_mp.py       Layer-2/3 reproduction script (needs MP API key)
tests/test_screening.py   unit tests (unittest, zero deps)
```

## License

MIT
