"""qutip-geometry: parameter-space Berry curvature and Chern number tools.

Reference implementation accompanying the feature request to the QuTiP
ecosystem (see proposals/qutip-berry-toolbox-issue.md).
"""

from .berry import berry_curvature, chern_number, nonabelian_chern_number

__all__ = ["berry_curvature", "chern_number", "nonabelian_chern_number"]
__version__ = "0.0.1"
