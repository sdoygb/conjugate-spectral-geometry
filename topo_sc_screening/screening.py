# -*- coding: utf-8 -*-
"""
Topological superconductivity screening by space-group symmetry.

Criterion (Theorem 9.1.12.01, Geometric Theory of Superconductivity, article 9.1):

    A material can be a topological superconductor candidate only if its point
    group contains both a C3 rotation and a Z2 symmetry (mirror plane or
    spatial inversion), equivalently:

        [G_lattice, T] = 0

    This reduces the 32 crystallographic point groups to 11 candidate groups:

        D6h, D3h, D3d, Oh, Td, C3i, C3v, C3h, C6h, C6v, Th

    which correspond to 52 of the 230 space groups (22.6%).

The criterion is a *necessary* condition (first-level screening). It does not
by itself predict superconductivity: candidates must still pass the
topological surface-state test (K-tilde^0 != 0) and the magnetic ordering test.

Pure standard library -- no dependencies.

Usage (CLI):
    python screening.py 194          # -> candidate (P6_3/mmc, D6h)
    python screening.py 139          # -> excluded (I4/mmm, D4h)
    python screening.py --list       # -> the 52 candidate space groups
    python screening.py --selfcheck  # -> run the built-in regression tests

Usage (API):
    from screening import is_candidate, sg_to_pointgroup
    is_candidate(194)                # -> True
    sg_to_pointgroup(139)            # -> 'D4h'
"""

# ---------------------------------------------------------------------------
# Space group number (1-230) -> Schoenflies point group.
# Generated from the spglib database (530 Hall symbols, International Tables
# for Crystallography standard settings). Frozen here so the package has no
# runtime dependency.
# ---------------------------------------------------------------------------
SG2PG = {
    1: "C1", 2: "Ci", 3: "C2", 4: "C2", 5: "C2", 6: "Cs", 7: "Cs", 8: "Cs",
    9: "Cs", 10: "C2h", 11: "C2h", 12: "C2h", 13: "C2h", 14: "C2h", 15: "C2h", 16: "D2",
    17: "D2", 18: "D2", 19: "D2", 20: "D2", 21: "D2", 22: "D2", 23: "D2", 24: "D2",
    25: "C2v", 26: "C2v", 27: "C2v", 28: "C2v", 29: "C2v", 30: "C2v", 31: "C2v", 32: "C2v",
    33: "C2v", 34: "C2v", 35: "C2v", 36: "C2v", 37: "C2v", 38: "C2v", 39: "C2v", 40: "C2v",
    41: "C2v", 42: "C2v", 43: "C2v", 44: "C2v", 45: "C2v", 46: "C2v", 47: "D2h", 48: "D2h",
    49: "D2h", 50: "D2h", 51: "D2h", 52: "D2h", 53: "D2h", 54: "D2h", 55: "D2h", 56: "D2h",
    57: "D2h", 58: "D2h", 59: "D2h", 60: "D2h", 61: "D2h", 62: "D2h", 63: "D2h", 64: "D2h",
    65: "D2h", 66: "D2h", 67: "D2h", 68: "D2h", 69: "D2h", 70: "D2h", 71: "D2h", 72: "D2h",
    73: "D2h", 74: "D2h", 75: "C4", 76: "C4", 77: "C4", 78: "C4", 79: "C4", 80: "C4",
    81: "S4", 82: "S4", 83: "C4h", 84: "C4h", 85: "C4h", 86: "C4h", 87: "C4h", 88: "C4h",
    89: "D4", 90: "D4", 91: "D4", 92: "D4", 93: "D4", 94: "D4", 95: "D4", 96: "D4",
    97: "D4", 98: "D4", 99: "C4v", 100: "C4v", 101: "C4v", 102: "C4v", 103: "C4v", 104: "C4v",
    105: "C4v", 106: "C4v", 107: "C4v", 108: "C4v", 109: "C4v", 110: "C4v", 111: "D2d", 112: "D2d",
    113: "D2d", 114: "D2d", 115: "D2d", 116: "D2d", 117: "D2d", 118: "D2d", 119: "D2d", 120: "D2d",
    121: "D2d", 122: "D2d", 123: "D4h", 124: "D4h", 125: "D4h", 126: "D4h", 127: "D4h", 128: "D4h",
    129: "D4h", 130: "D4h", 131: "D4h", 132: "D4h", 133: "D4h", 134: "D4h", 135: "D4h", 136: "D4h",
    137: "D4h", 138: "D4h", 139: "D4h", 140: "D4h", 141: "D4h", 142: "D4h", 143: "C3", 144: "C3",
    145: "C3", 146: "C3", 147: "C3i", 148: "C3i", 149: "D3", 150: "D3", 151: "D3", 152: "D3",
    153: "D3", 154: "D3", 155: "D3", 156: "C3v", 157: "C3v", 158: "C3v", 159: "C3v", 160: "C3v",
    161: "C3v", 162: "D3d", 163: "D3d", 164: "D3d", 165: "D3d", 166: "D3d", 167: "D3d", 168: "C6",
    169: "C6", 170: "C6", 171: "C6", 172: "C6", 173: "C6", 174: "C3h", 175: "C6h", 176: "C6h",
    177: "D6", 178: "D6", 179: "D6", 180: "D6", 181: "D6", 182: "D6", 183: "C6v", 184: "C6v",
    185: "C6v", 186: "C6v", 187: "D3h", 188: "D3h", 189: "D3h", 190: "D3h", 191: "D6h", 192: "D6h",
    193: "D6h", 194: "D6h", 195: "T", 196: "T", 197: "T", 198: "T", 199: "T", 200: "Th",
    201: "Th", 202: "Th", 203: "Th", 204: "Th", 205: "Th", 206: "Th", 207: "O", 208: "O",
    209: "O", 210: "O", 211: "O", 212: "O", 213: "O", 214: "O", 215: "Td", 216: "Td",
    217: "Td", 218: "Td", 219: "Td", 220: "Td", 221: "Oh", 222: "Oh", 223: "Oh", 224: "Oh",
    225: "Oh", 226: "Oh", 227: "Oh", 228: "Oh", 229: "Oh", 230: "Oh",
}

# The 11 candidate point groups: contain C3 AND (mirror | inversion).
CANDIDATE_PGS = {"D6h", "D3h", "D3d", "Oh", "Td", "C3i", "C3v",
                 "C3h", "C6h", "C6v", "Th"}

# Point groups that contain C3 but lack the Z2 element (excluded).
C3_WITHOUT_Z2 = {"C3", "D3", "C6", "D6", "T", "O"}

__version__ = "1.0.0"
__all__ = ["SG2PG", "CANDIDATE_PGS", "sg_to_pointgroup", "is_candidate",
           "candidate_space_groups", "explain"]


def sg_to_pointgroup(sg_number):
    """Return the Schoenflies point group of a space group number (1-230)."""
    return SG2PG.get(int(sg_number), "UNKNOWN")


def is_candidate(sg_number):
    """
    Theorem 9.1.12.01: is the space group a topological-superconductor
    candidate? (necessary condition: point group contains C3 and Z2).
    """
    return SG2PG.get(int(sg_number)) in CANDIDATE_PGS


def candidate_space_groups():
    """Return the sorted list of the 52 candidate space group numbers."""
    return sorted(n for n in range(1, 231) if SG2PG.get(n) in CANDIDATE_PGS)


def explain(sg_number):
    """Human-readable explanation of the verdict for a space group."""
    pg = sg_to_pointgroup(sg_number)
    if pg == "UNKNOWN":
        return f"sg={sg_number}: invalid space group number"
    if pg in CANDIDATE_PGS:
        return (f"sg={sg_number} ({pg}): CANDIDATE -- contains C3 rotation "
                f"and Z2 symmetry (mirror/inversion)")
    if pg in C3_WITHOUT_Z2:
        return (f"sg={sg_number} ({pg}): EXCLUDED -- contains C3 but lacks "
                f"the Z2 symmetry (mirror/inversion)")
    return (f"sg={sg_number} ({pg}): EXCLUDED -- lacks C3 rotation "
            f"(no 3-fold axis)")


# ---------------------------------------------------------------------------
# Built-in regression tests (article 9.1, Sec. 12.2 key cases)
# ---------------------------------------------------------------------------
SELFCHECK = {
    # (space group, expected candidate?, example)
    194: (True, "UPt3 (P6_3/mmc, D6h)"),
    204: (True, "PrOs4Sb12 (Im-3, Th)"),
    227: (True, "Bi2Pd gamma phase (Fd-3m, Oh)"),
    166: (True, "Bi2Se3 family (R-3m, D3d)"),
    216: (True, "YPtBi / half-Heusler (F-43m, Td)"),
    225: (True, "SnTe, TCI (Fm-3m, Oh)"),
    139: (False, "Sr2RuO4 (I4/mmm, D4h) -- exclusion prediction"),
    71:  (False, "UTe2 (Immm, D2h) -- exclusion prediction"),
    47:  (False, "YBa2Cu3O7 (Pmmm, D2h) -- cuprate, non-topological path"),
    129: (False, "FeSe (P4/nmm, D4h) -- iron-based, non-topological path"),
    12:  (False, "2M-WS2 (C2/m, C2h) -- outside C3-protected regime"),
    143: (False, "C3 without Z2 (P3, C3)"),
}


def _run_selfcheck():
    n_pass = 0
    for sg, (exp, note) in sorted(SELFCHECK.items()):
        got = is_candidate(sg)
        ok = got == exp
        n_pass += ok
        print(f"  sg={sg:3d} {sg_to_pointgroup(sg):5s} candidate={str(got):5s} "
              f"expected={str(exp):5s} [{'OK' if ok else 'FAIL'}]  {note}")
    print(f"\n  {n_pass}/{len(SELFCHECK)} checks passed")
    return n_pass == len(SELFCHECK)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "--list":
        cand = candidate_space_groups()
        print(f"Candidate space groups ({len(cand)}): {cand}")
    elif args[0] == "--selfcheck":
        sys.exit(0 if _run_selfcheck() else 1)
    elif args[0] in ("-h", "--help"):
        print(__doc__)
    else:
        for a in args:
            try:
                sg = int(a)
            except ValueError:
                print(f"  invalid input: {a}")
                continue
            verdict = "CANDIDATE" if is_candidate(sg) else "EXCLUDED"
            print(f"  {explain(sg)}  ->  {verdict}")
