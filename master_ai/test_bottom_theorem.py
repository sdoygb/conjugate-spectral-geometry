"""
test_bottom_theorem.py — 用底层定理测试三重检查

测试定理: 30° 背景的全局极小定理 (0.1.1 命题1.3 / 0.0.6 定理4.4)

定理内容:
  在约束流 D_θ = {(θ_M, θ_C, θ_I) | θ_M+θ_C+θ_I=90°} 上，
  六项作用量 S 的唯一全局严格极小值点为 θ_M=θ_C=θ_I=30°，
  最小值 S_min = 24。

依赖: 仅公理 I（完备性约束）+ 公理 II（六项作用量）
  - 公理 I: θ_M + θ_C + θ_I = 90°
  - 公理 II: S = Σ 1/sin²θ_i + Σ 1/(sinθ_i·sinθ_j)

推导:
  1. 由 S₃ 对称性，极值点满足 θ_M=θ_C=θ_I
  2. 代入公理 I: 3θ = 90° → θ = 30°
  3. 计算 S(30°,30°,30°) = 3×(1/sin²30°) + 3×(1/(sin30°·sin30°))
     = 3×4 + 3×4 = 12 + 12 = 24
  4. Hessian 在约束切空间上正定 → 严格极小

这个定理应该能通过三重检查:
  - Berry回路闭合: 30°背景 → 探索约束面 → 回到30° (闭合)
  - 证伪条件: 不涉及 S_e/r_core/信息熵（自动跳过）
  - 独立推导: LLM 从公理 I+II 应该能复现 S_min=24
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


# ==================== 定理内容 ====================

FORMULA_CONTENT = """
30°背景的全局极小定理 (0.1.1 命题1.3 / 0.0.6 定理4.4)

定理陈述:
  在约束流 D_θ = {(θ_M, θ_C, θ_I) ∈ R³⁺ | θ_M+θ_C+θ_I=90°} 上，
  六项作用量 S 的唯一全局严格极小值点为 θ_M=θ_C=θ_I=30°，
  最小值 S_min = 24。

六项作用量定义 (公理 II):
  S(θ_M, θ_C, θ_I) = 1/sin²θ_M + 1/sin²θ_C + 1/sin²θ_I
                    + 1/(sinθ_M·sinθ_C) + 1/(sinθ_M·sinθ_I) + 1/(sinθ_C·sinθ_I)

证明:
  步骤1: 由 S₃ 对称性 (命题1.1)，S 在指标置换下不变，
         故极值点满足 θ_M = θ_C = θ_I。
  步骤2: 代入公理 I (θ_M+θ_C+θ_I=90°): 3θ = 90° → θ = 30°。
  步骤3: 计算 S(30°,30°,30°):
         sin30° = 1/2, sin²30° = 1/4, 1/sin²30° = 4
         S = 3×4 + 3×4 = 12 + 12 = 24。
  步骤4: 约束切空间上的 Hessian 正定 → 严格全局极小。

关键数值:
  S_min = 24 (30°背景作用量)
  sin30° = 0.5
  极小点: (30°, 30°, 30°)

依赖: 公理 I (完备性约束) + 公理 II (六项作用量)
不依赖: 质量映射、S_e识别、量纲桥、结构假设
"""

DERIVATION_CHAIN = """
步骤1: 从公理I出发，完备性约束 θ_M+θ_C+θ_I=90°，背景点 θ_M=30°, θ_C=30°, θ_I=30°（S₃不动点）
步骤2: 公理II给出六项作用量 S = Σ 1/sin²θ_i + Σ 1/(sinθ_i·sinθ_j)，在30°处 S=24
步骤3: 由S₃对称性，极值点满足 θ_M=θ_C=θ_I，代入公理I得 θ=30°，θ_M=30°, θ_C=30°, θ_I=30°
步骤4: 计算 S(30°) = 3×(1/sin²30°) + 3×(1/sin30°·sin30°) = 3×4+3×4 = 24
步骤5: 为验证全局极小性，扰动到 θ_I=33°（θ_M=28.5°, θ_C=28.5°），计算 S > 24
步骤6: Hessian在约束切空间正定，确认30°为严格全局极小，θ_M=30°, θ_C=30°, θ_I=30°
步骤7: 回到背景点，θ_M=30°, θ_C=30°, θ_I=30°（闭合验证）
"""


def main():
    print("\n" + "#" * 70)
    print("#  底层定理验证测试: 30°背景全局极小定理")
    print("#" * 70)

    print(f"\n定理: S(30°,30°,30°) = 24 是全局严格极小值")
    print(f"依赖: 公理 I + 公理 II (仅)")
    print(f"推导链: {len(DERIVATION_CHAIN.strip().split('步骤')) - 1} 步")

    # ==================== 阶段1: Berry回路闭合检测 ====================
    print("\n" + "=" * 70)
    print("阶段1: Berry回路闭合检测")
    print("=" * 70)

    checker = BerryPhaseChecker()
    berry_result = checker.verify(
        derivation_chain=DERIVATION_CHAIN,
        formula_content=FORMULA_CONTENT,
    )

    print(f"\n  路径点数: {len(berry_result.path_points)}")
    if berry_result.path_points:
        print(f"  参数空间路径:")
        for i, (tm, tc, ti) in enumerate(berry_result.path_points):
            print(f"    点{i+1}: θ_M={tm}°, θ_C={tc}°, θ_I={ti}°")

    print(f"\n  Berry相位: {berry_result.berry_phase:.6f} rad")
    print(f"  2π倍数: {berry_result.berry_phase / (2 * math.pi):.6f}")
    print(f"  最近整数 n: {berry_result.n_value}")
    print(f"  闭合误差: {berry_result.closure_error:.6f} rad (容差: {checker.tol})")
    print(f"  路径闭合: {berry_result.path_closed}")
    print(f"  圆满级别: {berry_result.consummation_level}")
    print(f"  是否圆满: {'✓ 是' if berry_result.is_consummated else '✗ 否'}")
    print(f"\n  详情: {berry_result.detail}")

    if not berry_result.is_consummated:
        print("\n  ⚠ 阶段1未通过 — Berry回路未闭合")
        _print_summary("Berry回路未闭合", False)
        return

    print(f"\n  ✓ 阶段1通过 — Berry回路闭合 (n={berry_result.n_value}, {berry_result.consummation_level})")

    # ==================== 阶段2: §9.6 证伪条件检查 ====================
    print("\n" + "=" * 70)
    print("阶段2: §9.6 证伪条件检查")
    print("=" * 70)

    berry_dict = checker.result_to_dict(berry_result)
    fc = FalsificationChecker()
    falsify_result = fc.run_all_checks(
        formula_content=FORMULA_CONTENT,
        derivation_chain=DERIVATION_CHAIN,
        berry_result=berry_dict,
    )

    print(f"\n  全部通过: {'✓ 是' if falsify_result['all_passed'] else '✗ 否'}")
    print()
    for check in falsify_result["checks"]:
        status = "✓" if check["passed"] else "✗"
        print(f"  {status} [{check['check_id']}] {check['check_name']}")
        print(f"    详情: {check['detail']}")
        print()

    if not falsify_result["all_passed"]:
        print(f"  ⚠ 阶段2未通过")
        _print_summary(f"证伪条件未通过: {falsify_result['rejection_reason']}", False)
        return

    print(f"  ✓ 阶段2通过 — 全部 {len(falsify_result['checks'])} 条证伪检查通过")

    # ==================== 阶段3: 独立推导复现 ====================
    print("\n" + "=" * 70)
    print("阶段3: 独立推导复现 (LLM)")
    print("=" * 70)

    verifier = MasterVerifier()
    if not verifier._llm_client:
        print("\n  LLM 不可用，跳过")
        _print_summary("LLM不可用", skipped=True)
        return

    print(f"\n  模型: {verifier._llm_client}")
    print("  启动独立推导复现...\n")

    derivation_result = verifier._independent_derivation(
        formula_name="30°背景全局极小定理 (0.1.1 命题1.3)",
        formula_content=FORMULA_CONTENT,
    )

    # 打印完整推导
    print("  --- LLM 推导回复 ---")
    print(derivation_result.get("derivation", ""))
    print("  --- 推导回复结束 ---\n")

    if derivation_result.get("reproduced"):
        print("  ✓ 阶段3通过 — LLM独立推导复现成功")
        _print_summary("", True)
    else:
        print(f"  ⚠ 阶段3未通过 — LLM独立推导复现失败")
        print(f"  原因: {derivation_result.get('reason', '未知')}")
        _print_summary(f"独立推导复现失败: {derivation_result.get('reason', '')}", False)


def _print_summary(reason: str, passed: bool = False, skipped: bool = False):
    print("\n" + "=" * 70)
    print("验证结果汇总")
    print("=" * 70)

    if passed:
        print("""
  ╔═══════════════════════════════════════════════════════╗
  ║  ✓ 三重检查全部通过                                    ║
  ║                                                       ║
  ║  定理: 30°背景全局极小定理 (0.1.1 命题1.3)             ║
  ║  判定: 圆满 — 可入库主库                               ║
  ║  意义: 自举螺旋第1圈成功                               ║
  ╚═══════════════════════════════════════════════════════╝
""")
    elif skipped:
        print("""
  ╔═══════════════════════════════════════════════════════╗
  ║  ⊙ 阶段3跳过 (LLM不可用)                              ║
  ║  阶段1+2 通过                                          ║
  ╚═══════════════════════════════════════════════════════╝
""")
    else:
        print(f"""
  ╔═══════════════════════════════════════════════════════╗
  ║  ✗ 验证未通过                                          ║
  ║                                                       ║
  ║  定理: 30°背景全局极小定理                             ║
  ║  驳回理由: {reason[:45]:<45}║
  ╚═══════════════════════════════════════════════════════╝
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
