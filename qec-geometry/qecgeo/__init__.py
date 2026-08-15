"""qecgeo —— 量子纠错码几何诊断工具包（qec-geometry）

把几何论 QEC 框架（文章 10.27/10.28/10.43/10.44/10.54）落地为可复现工具：

  1. 码构造与稳定子框架    qecgeo.codes / qecgeo.stabilizer / qecgeo.pauli
  2. 容错阈值闭式          qecgeo.threshold   （p_L ≈ A·p²，p_th = 1/A）
  3. 任意子类型判定        qecgeo.anyon       （Ising/Majorana 型）
  4. 错误模式几何分类      qecgeo.error_geometry（A0 局域 / A1 非平凡拓扑）

依赖：numpy（必需）；stim + pymatching（仅 error_geometry 的 surface
code 演示需要）。
"""
from .pauli import Pauli
from .stabilizer import StabilizerCode
from .codes import (five_qubit_code, steane_code, shor_code,
                    rm_code_15_7_3, ALL)
from .threshold import (analyze_eta, monte_carlo, verify_quadratic,
                        concatenation_sequence)
from .anyon import (delta_phase_analysis, is_ising_statistics,
                    verify_delta8_berry_consistency)

__version__ = "0.1.0"
