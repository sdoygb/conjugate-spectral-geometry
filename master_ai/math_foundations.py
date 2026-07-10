"""
math_foundations.py — 标准数学公理基座（Layer 0）

定义主库AI独立推导时可自由使用的标准数学工具。
这些是数学界已确立的定理和事实，不需要从几何论公理推导。

分层公理体系：
  L0: 标准数学基座（本文件） — 无需验证，直接接受
  L1: 几何论三公理 — 推导的唯一理论起点
  L2: 桥接假设 — 子AI显式声明的外部物理锚点
  L3: 已验证定理 — 主库中已通过验证的公式

设计原则：
1. 只收录数学界公认的、有严格证明的标准结果
2. 按领域分类，便于LLM检索和使用
3. 每条事实包含名称、公式、简要说明，便于LLM引用
"""

from typing import Dict, List, Any


# ==================== 标准数学事实 ====================

MATH_FOUNDATIONS: Dict[str, Dict[str, Any]] = {
    "differential_geometry": {
        "name": "微分几何",
        "description": "外微分、微分形式、流形上的微积分",
        "facts": [
            {
                "id": "DG-01",
                "name": "外微分幂零性",
                "formula": "d² = 0, ∂² = 0",
                "description": "外微分的二次作用恒为零。这是de Rham上同调的基石。",
            },
            {
                "id": "DG-02",
                "name": "广义Stokes定理",
                "formula": "∫_M dω = ∫_{∂M} ω",
                "description": "微分流形上微分形式的积分定理，统一了牛顿-莱布尼茨、格林、高斯、斯托克斯公式。",
            },
            {
                "id": "DG-03",
                "name": "de Rham上同调",
                "formula": "H^k_dR(M) = ker(d_k) / im(d_{k-1})",
                "description": "闭形式模恰当形式，d²=0保证此定义良定性。",
            },
            {
                "id": "DG-04",
                "name": "闭形式与恰当形式",
                "formula": "dω=0 ⟹ ω闭; ω=dα ⟹ ω恰当",
                "description": "恰当形式必为闭形式（因d²=0），反之不一定（取决于拓扑）。",
            },
            {
                "id": "DG-05",
                "name": "Berry联络与曲率",
                "formula": "A = i⟨ψ|∂ψ⟩, F = dA",
                "description": "量子态参数空间上的几何联络，曲率为联络的外微分。",
            },
            {
                "id": "DG-06",
                "name": "散度定理（高斯定理）",
                "formula": "∫_V ∇·F dV = ∮_{∂V} F·dS",
                "description": "向量场散度的体积分等于穿过边界的通量。∇·B=0是其直接推论。",
            },
            {
                "id": "DG-07",
                "name": "Poincaré引理",
                "formula": "d²=0 ⟹ 局部上闭=恰当",
                "description": "在可缩开集上，每个闭形式都是恰当形式。",
            },
        ],
    },

    "topology": {
        "name": "拓扑学",
        "description": "单形、同胚、同伦、复形",
        "facts": [
            {
                "id": "TP-01",
                "name": "标准单形",
                "formula": "Δⁿ = {x ∈ ℝⁿ⁺¹ | x_i ≥ 0, Σx_i = 1}",
                "description": "n维标准单形是ℝⁿ⁺¹中的凸包。Δ⁰=点, Δ¹=线段, Δ²=三角形, Δ³=四面体。",
            },
            {
                "id": "TP-02",
                "name": "单形同胚于圆盘",
                "formula": "Δⁿ ≅ Dⁿ",
                "description": "n维标准单形同胚于n维闭圆盘。这是凸几何的标准结论。",
            },
            {
                "id": "TP-03",
                "name": "同胚保持拓扑性质",
                "formula": "X ≅ Y ⟹ π₁(X) ≅ π₁(Y), H_*(X) ≅ H_*(Y)",
                "description": "同胚空间具有相同的基本群、同调群、上同调环等所有拓扑不变量。",
            },
            {
                "id": "TP-04",
                "name": "同伦等价弱于同胚",
                "formula": "X ≃ Y ⟹ H_*(X) ≅ H_*(Y) 但 X ≄ Y",
                "description": "同伦等价保持同调但不保证同胚。可缩空间同伦等价于点。",
            },
            {
                "id": "TP-05",
                "name": "单纯复形",
                "formula": "K = ∪ Δⁿ_α",
                "description": "单形的并集，满足交为公共面。是计算同调的标准工具。",
            },
        ],
    },

    "algebra": {
        "name": "代数",
        "description": "群论、线性代数、表示论",
        "facts": [
            {
                "id": "AL-01",
                "name": "群表示",
                "formula": "ρ: G → GL(V)",
                "description": "群到向量空间自同构群的同态。不可约表示是基本构件。",
            },
            {
                "id": "AL-02",
                "name": "特征标正交性",
                "formula": "⟨χ_i, χ_j⟩ = (1/|G|) Σ χ_i(g)χ_j(g)* = δ_ij",
                "description": "有限群不可约表示的特征标在类函数空间中正交。",
            },
            {
                "id": "AL-03",
                "name": "线性算子谱定理",
                "formula": "A = Σ λ_i |v_i⟩⟨v_i|",
                "description": "自伴算子可对角化，本征值实数，本征向量正交完备。",
            },
            {
                "id": "AL-04",
                "name": "张量积",
                "formula": "V ⊗ W",
                "description": "向量空间的张量积。量子复合系统的态空间为子系统张量积。",
            },
        ],
    },

    "analysis": {
        "name": "分析",
        "description": "微积分、变分法、谱理论",
        "facts": [
            {
                "id": "AN-01",
                "name": "变分原理",
                "formula": "δS = 0 ⟹ 运动方程",
                "description": "作用量取极值给出系统的运动方程（Euler-Lagrange方程）。",
            },
            {
                "id": "AN-02",
                "name": "傅里叶分析",
                "formula": "f(x) = Σ c_n e^{inx}",
                "description": "周期函数可展开为复指数的叠加。Parseval恒等式保持范数。",
            },
            {
                "id": "AN-03",
                "name": "Cauchy-Schwarz不等式",
                "formula": "|⟨u,v⟩|² ≤ ⟨u,u⟩⟨v,v⟩",
                "description": "内积空间的基本不等式。等号当且仅当线性相关。",
            },
        ],
    },

    "quantum_formalism": {
        "name": "量子力学形式体系",
        "description": "Hilbert空间框架（不含测量公理/Born规则，那属于L2桥接假设）",
        "facts": [
            {
                "id": "QF-01",
                "name": "Hilbert空间",
                "formula": "ℋ: 完备内积空间",
                "description": "量子态为Hilbert空间中的向量。可观测量为自伴算子。",
            },
            {
                "id": "QF-02",
                "name": "密度矩阵",
                "formula": "ρ = Σ p_i |ψ_i⟩⟨ψ_i|, Tr(ρ)=1",
                "description": "混合态的描述。纯态ρ=|ψ⟩⟨ψ|。",
            },
            {
                "id": "QF-03",
                "name": "纠缠态",
                "formula": "|Ψ⟩ ≠ |a⟩⊗|b⟩",
                "description": "不可分解为子系统态张量积的态。最大纠缠态包括Bell态。",
            },
            {
                "id": "QF-04",
                "name": "Tsirelson不等式的数学结构",
                "formula": "S = |⟨AB⟩+⟨A'B⟩+⟨AB'⟩-⟨A'B'⟩|",
                "description": "CHSH关联函数的上界。经典≤2, 量子≤2√2, 后者由半正定规划给出。",
            },
        ],
    },
}


# ==================== 物理映射已封禁 ====================
# 主库只接受纯几何数学公式。物理映射（ℰ）和所有物理概念
# 不再入库，物理推导在子AI本地完成。
# 以下保留为空列表，保持接口兼容但不再提供任何物理桥接。

BRIDGE_HYPOTHESES: Dict[str, Dict[str, str]] = {}

PENDING_PHYSICS_DERIVATIONS: List[Dict[str, str]] = []


# ==================== 工具函数 ====================

def get_foundations_text() -> str:
    """构建L0数学基座文本（供LLM提示词使用）"""
    lines = ["【L0: 标准数学公理基座 — 可自由使用，无需从几何论公理推导】\n"]
    for category_key, category in MATH_FOUNDATIONS.items():
        lines.append(f"\n▼ {category['name']}（{category['description']}）")
        for fact in category["facts"]:
            lines.append(f"  [{fact['id']}] {fact['name']}: {fact['formula']}")
            lines.append(f"      {fact['description']}")
    return "\n".join(lines)


def get_bridge_hypothesis_text(declared_anchors: List[str]) -> str:
    """
    构建L2桥接假设文本（仅包含子AI声明且在白名单中的锚点）

    Args:
        declared_anchors: 子AI在提交时声明的外部锚点列表

    Returns:
        桥接假设文本，以及未识别的锚点列表
    """
    if not declared_anchors:
        return "", []

    lines = ["\n【L2: 桥接假设 — 本次推导的附加前提（子AI已声明）】\n"]
    unrecognized = []
    found_any = False

    for anchor in declared_anchors:
        anchor_lower = anchor.lower().strip()
        matched = False
        for key, hyp in BRIDGE_HYPOTHESES.items():
            # 模糊匹配：名称、key、或描述中的关键词
            if (key.lower() in anchor_lower or
                hyp["name"].lower() in anchor_lower or
                anchor_lower in hyp["name"].lower()):
                lines.append(f"  ◆ {hyp['name']}")
                lines.append(f"      {hyp['description']}")
                lines.append(f"      用途: {hyp['usage']}\n")
                matched = True
                found_any = True
                break
        if not matched:
            unrecognized.append(anchor)

    if not found_any:
        return "", unrecognized

    return "\n".join(lines), unrecognized


def validate_anchors(declared_anchors: List[str]) -> Dict[str, Any]:
    """
    验证子AI声明的外部锚点。

    单一ℰ原则下：
    - ℰ 是唯一合法的L2桥接假设
    - Born规则、物理识别等不再是L2，而是待推导的L3定理
    - 如果子AI声明了这些，返回"需要先推导"的依赖缺口

    Returns:
        {
            "valid": List[str],  # 已识别为合法L2（只有ℰ）
            "invalid": List[str],  # 未识别
            "needs_derivation": List[Dict],  # 需要先从ℰ推导的物理概念
            "all_valid": bool,
        }
    """
    valid = []
    invalid = []
    needs_derivation = []

    for anchor in declared_anchors:
        anchor_lower = anchor.lower().strip()
        matched = False

        # 检查是否是ℰ
        for key, hyp in BRIDGE_HYPOTHESES.items():
            if (key.lower() in anchor_lower or
                hyp["name"].lower() in anchor_lower or
                "ε" in anchor or "epsilon" in anchor_lower or
                "ℰ" in anchor):
                valid.append(hyp["name"])
                matched = True
                break

        if not matched:
            # 检查是否是待推导的物理概念
            for pending in PENDING_PHYSICS_DERIVATIONS:
                name_lower = pending["name"].lower()
                if (name_lower in anchor_lower or
                    anchor_lower in name_lower):
                    needs_derivation.append(pending)
                    matched = True
                    break

        if not matched:
            invalid.append(anchor)

    return {
        "valid": valid,
        "invalid": invalid,
        "needs_derivation": needs_derivation,
        "all_valid": len(invalid) == 0 and len(needs_derivation) == 0,
    }


def get_pending_derivations_text() -> str:
    """构建待推导物理定理文本（供LLM和子AI参考）"""
    lines = ["\n【待推导物理定理 — 必须从ℰ推导后入库才能使用】\n"]
    for item in PENDING_PHYSICS_DERIVATIONS:
        lines.append(f"  ⚠ {item['name']}: {item['target']}")
        lines.append(f"      {item['description']}")
        lines.append(f"      推导路径: {item['dependency']}\n")
    return "\n".join(lines)
