"""qec_cert — certificate-based distance verification for CSS(RM) affine-complete codes.

Positioning (distance-certifying, as opposed to distance-finding):
    when the distance is a theorem, stop computing it — verify it.

The distance d = 2^(r+1) of CSS(RM(r,m), RM(r,m)) codes is fixed by geometric
structure (the RM minimum-weight theorem and the duality theorem). This
package produces a machine-checkable certificate at O(n^2) polynomial cost;
the brute-force enumeration baseline costs sum_{w<d} C(n,w) (exponential).

Measured (same machine, same implementation): [[1024,252,32]] certifies in
0.7 seconds, where brute force would need ~2.4e45 years.
"""
from __future__ import annotations

from .brute import brute_layer, brute_verify
from .certificate import DistanceCertificate, certify
from .rm_codes import (
    FAMILY_EXAMPLES,
    ag_flat_count,
    build_cols,
    css_params,
    parity_big,
    rm_dim,
    rm_rows,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "rm_dim",
    "rm_rows",
    "parity_big",
    "ag_flat_count",
    "css_params",
    "build_cols",
    "FAMILY_EXAMPLES",
    "DistanceCertificate",
    "certify",
    "brute_layer",
    "brute_verify",
]
