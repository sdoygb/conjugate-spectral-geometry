"""
test_dependency_gap.py — 测试依赖缺口分析机制

用 0.6.8 光子零质量定理重新测试，看主库AI是否能：
1. 正确识别"依赖不足"（而非"公式错误"）
2. 列出缺失的依赖
3. 给子库可操作的指导建议
"""
import sys
import os
import math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from berry_checker import BerryPhaseChecker
from falsification import FalsificationChecker
from verifier import MasterVerifier


FORMULA_CONTENT = """
光子零质量定理 (0.6.8)

核心公式: m_γ = K · sin³(0) = 0
M场零模构型: θ_M→0, θ_C→0, θ_I→90°
质量映射定理: m = K · sin³(θ_M), K = 839.758793 keV
九素互扼定理: S = S_e = 137.035999084
边界度规: g_μν = η_μν + O(ℓ_P/L)
退耦假设: 零模不参与S求和（状态: 开放，待0.3.5退耦定理）

依赖: 公理I+II+III, 质量映射定理(0.1.x), 九素互扼定理(0.3.5), M场谱(0.6.6), 腰边耦合(0.6.3)
"""

DERIVATION_CHAIN = """
步骤1: 从公理1出发，θ_M=57.93°, θ_C=26.16°, θ_I=5.91°（背景点P0）
步骤2: M场质量谱 m_n = K·sin³(θ_M)，零模条件 ω→0 要求 m_n→0，即 θ_M→0
步骤3: 腰边耦合选择定则 sinθ_M=sinθ_C，θ_M→0 时 θ_C→0
步骤4: 公理3完备性约束 θ_I = 90°-θ_M-θ_C → 90°，θ_M=0°, θ_C=0°, θ_I=90°
步骤5: 零模退耦假设——零模不参与S求和，避免S发散与S_e=137.035999084冲突
步骤6: 质量映射定理 m_γ = K·sin³(0) = 0，光子零质量得证
步骤7: 边界度规定理 g_μν=η_μν+O(ℓ_P/L)
步骤8: 零质量粒子在Minkowski度规中 v_γ=c
步骤9: 回到背景点，θ_M=57.93°, θ_C=26.16°, θ_I=5.91°（P0闭合）
"""


def main():
    print("\n" + "#" * 70)
    print("#  依赖缺口分析测试: 0.6.8 光子零质量定理")
    print("#" * 70)

    # 阶段1: Berry检测
    checker = BerryPhaseChecker()
    berry_result = checker.verify(derivation_chain=DERIVATION_CHAIN, formula_content=FORMULA_CONTENT)
    print(f"\n阶段1 Berry: {'✓' if berry_result.is_consummated else '✗'} {berry_result.consummation_level} (n={berry_result.n_value})")

    # 阶段2: 证伪检查
    berry_dict = checker.result_to_dict(berry_result)
    fc = FalsificationChecker()
    falsify_result = fc.run_all_checks(formula_content=FORMULA_CONTENT, derivation_chain=DERIVATION_CHAIN, berry_result=berry_dict)
    print(f"阶段2 证伪: {'✓' if falsify_result['all_passed'] else '✗'} 全部通过")

    # 阶段3: 独立推导 + 依赖缺口分析
    print("\n" + "=" * 70)
    print("阶段3: 独立推导复现 + 依赖缺口分析")
    print("=" * 70)

    verifier = MasterVerifier()
    if not verifier._llm_client:
        print("\n  LLM 不可用，跳过")
        return

    # 独立推导
    print("\n  [3a] 独立推导复现...")
    derivation_result = verifier._independent_derivation(
        formula_name="光子零质量定理 (0.6.8)",
        formula_content=FORMULA_CONTENT,
    )
    reproduced = derivation_result.get("reproduced", False)
    print(f"  复现结果: {'✓ 成功' if reproduced else '✗ 失败'}")

    if reproduced:
        print("\n  公式通过验证，无需依赖缺口分析")
        return

    # 依赖缺口分析
    print("\n  [3b] 依赖缺口分析（新增机制）...")
    print("  主库AI正在分析: 是依赖不足还是公式错误？\n")

    gap_analysis = verifier._analyze_dependency_gap(
        formula_name="光子零质量定理 (0.6.8)",
        formula_content=FORMULA_CONTENT,
        derivation_result=derivation_result,
    )

    # 打印分析结果
    print("  " + "-" * 66)
    print("  依赖缺口分析结果")
    print("  " + "-" * 66)

    is_gap = gap_analysis.get("is_dependency_gap", False)
    print(f"\n  判定: {'⚠ 依赖不足（非公式错误）' if is_gap else '✗ 公式错误'}")

    if is_gap:
        missing = gap_analysis.get("missing_dependencies", [])
        print(f"\n  缺失依赖 ({len(missing)} 项):")
        for i, dep in enumerate(missing, 1):
            print(f"    {i}. {dep}")

        guidance = gap_analysis.get("guidance", "")
        if guidance:
            print(f"\n  指导建议: {guidance}")

        print(f"\n  {'=' * 66}")
        print(f"  结论: 公式暂时无法验证，需要子库先补全上述依赖")
        print(f"  这不是驳回 — 是给子库指路")
        print(f"  {'=' * 66}")
    else:
        error = gap_analysis.get("error_analysis", "")
        print(f"\n  错误分析: {error}")
        print(f"\n  结论: 公式本身有错误，被驳回")

    # 打印完整分析原文
    raw = gap_analysis.get("raw_analysis", "")
    if raw:
        print(f"\n  {'─' * 66}")
        print("  主库AI分析原文:")
        print(f"  {'─' * 66}")
        for line in raw.split("\n"):
            print(f"  {line}")


if __name__ == "__main__":
    main()
