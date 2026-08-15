# -*- coding: utf-8 -*-
"""Unit tests for the symmetry screening criterion (Theorem 9.1.12.01).

Run:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screening import (SG2PG, CANDIDATE_PGS, is_candidate,
                       sg_to_pointgroup, candidate_space_groups, explain)


class TestMapping(unittest.TestCase):
    """The frozen space-group -> point-group map must cover all 230 groups."""

    def test_full_coverage(self):
        self.assertEqual(len(SG2PG), 230)
        self.assertEqual(set(SG2PG.keys()), set(range(1, 231)))

    def test_known_point_groups(self):
        self.assertEqual(sg_to_pointgroup(194), "D6h")   # P6_3/mmc
        self.assertEqual(sg_to_pointgroup(225), "Oh")    # Fm-3m
        self.assertEqual(sg_to_pointgroup(166), "D3d")   # R-3m
        self.assertEqual(sg_to_pointgroup(139), "D4h")   # I4/mmm
        self.assertEqual(sg_to_pointgroup(71), "D2h")    # Immm
        self.assertEqual(sg_to_pointgroup(47), "D2h")    # Pmmm


class TestCriterion(unittest.TestCase):
    """Article 9.1, Sec. 12.2 key cases."""

    def test_candidates(self):
        for sg in [194, 204, 227, 166, 216, 225, 191, 223, 221, 229]:
            self.assertTrue(is_candidate(sg), f"sg={sg} should be candidate")

    def test_excluded(self):
        for sg in [139, 71, 47, 129, 63, 12, 143, 149, 168, 195, 207]:
            self.assertFalse(is_candidate(sg), f"sg={sg} should be excluded")

    def test_candidate_count(self):
        cand = candidate_space_groups()
        self.assertEqual(len(cand), 52)
        # every candidate point group is in the official list
        for sg in cand:
            self.assertIn(sg_to_pointgroup(sg), CANDIDATE_PGS)

    def test_c3_without_z2_excluded(self):
        # point groups with C3 but no mirror/inversion are NOT candidates
        for sg, pg in SG2PG.items():
            if pg in {"C3", "D3", "C6", "D6", "T", "O"}:
                self.assertFalse(is_candidate(sg), f"sg={sg} ({pg})")

    def test_invalid_input(self):
        self.assertEqual(sg_to_pointgroup(999), "UNKNOWN")
        self.assertFalse(is_candidate(0))
        self.assertFalse(is_candidate(231))


class TestExplain(unittest.TestCase):
    def test_verdicts(self):
        self.assertIn("CANDIDATE", explain(194))
        self.assertIn("EXCLUDED", explain(139))
        self.assertIn("EXCLUDED", explain(143))   # C3 without Z2
        self.assertIn("invalid", explain(999))


class TestDataFile(unittest.TestCase):
    """Layer-1 validation data: 94 known superconductors."""

    def test_materials_94(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "materials_94.csv")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            rows = list(csv_reader(f))
        self.assertEqual(len(rows) - 1, 94)   # minus header
        # every space group number in the file must be consistent with the map
        for row in rows[1:]:
            sg = int(row[3])
            self.assertEqual(sg_to_pointgroup(sg), row[4])

    def test_candidate_fraction(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "materials_94.csv")
        with open(path) as f:
            rows = list(csv_reader(f))
        n_cand = sum(1 for r in rows[1:] if r[5] == "YES")
        self.assertEqual(n_cand, 70)
        self.assertEqual(len(rows) - 1 - n_cand, 24)


def csv_reader(f):
    import csv
    return csv.reader(f)


if __name__ == "__main__":
    unittest.main()
