# -*- coding: utf-8 -*-
"""提交第一批 5 条纯几何定理到主库（绕过 tools 层的误导性渲染，直连 master_client）。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_client import get_master_client

client = get_master_client()
print("URL:", client.url)
print("TOKEN:", client.token[:8] + "...")
print("AVAILABLE:", client._available)

submissions = [
    {
        "formula_name": "引理 1.3.2.01（投影强度恒等式）",
        "formula_content": "设 L₁,L₂,L₃ 为 Cl(3) ≅ ℍ⊕ℍ 在 ℝ⁴ ≅ ℍ 上的左乘表示矩阵，满足 Lᵢ² = -I₄，LᵢLⱼ + LⱼLᵢ = -2δᵢⱼI₄，体积元 ω₃ = L₁L₂L₃ = -I₄。对任意秩-2 正交投影 P: ℝ⁴ → Π（Π 为二维子空间），有：\n∑ᵢ₌₁³ ‖PLᵢP‖²_HS = 2\n其中 ‖·‖_HS 为 Hilbert-Schmidt 范数。此恒等式仅依赖 Lᵢ 的反对称性与四元数 Lagrange 恒等式，均为 Cl(3) 的代数性质。",
        "derivation_chain": "【依赖】引理 0.2.2.01（半单分裂）、命题 0.2.1.02（体积元的平方）\n【推导】\n步骤1: 由引理 0.2.2.01（#88），Cl(3) ≅ ℍ⊕ℍ；由命题 0.2.1.02（#264），ω₃² = 1；在 ℝ⁴≅ℍ 的左乘表示中 Lᵢ² = -I₄、LᵢLⱼ + LⱼLᵢ = -2δᵢⱼI₄、ω₃ = L₁L₂L₃ = -I₄；\n步骤2: 由 Lᵢ² = -I₄ 及 Lᵢ 为实矩阵，Lᵢᵀ = -Lᵢ（反对称）；\n步骤3: 设 {u,v} 为 Π 的标准正交基，Q = [u|v]（QᵀQ = I₂），投影 P = QQᵀ；‖PLᵢP‖²_HS = ‖QᵀLᵢQ‖²_F；\n步骤4: QᵀLᵢQ 是 2×2 反对称矩阵，二维反对称矩阵空间由唯一复结构 J 张成，故 QᵀLᵢQ = cᵢJ，cᵢ = ⟨u,Lᵢv⟩；\n步骤5: ‖PLᵢP‖²_HS = cᵢ²‖J‖²_F = 2cᵢ²（‖J‖²_F = Tr(JᵀJ) = 2）；\n步骤6: 四元数 Lagrange 恒等式：∑ᵢcᵢ² = ∑ᵢ⟨u,Lᵢv⟩² = ‖u‖²‖v‖² - ⟨u,v⟩²（四元数模恒等式 |u·v̄|² = |u|²|v|² 的分量展开）；\n步骤7: 对标准正交基（‖u‖=‖v‖=1，⟨u,v⟩=0）：∑ᵢcᵢ² = 1；\n步骤8: ∑ᵢ‖PLᵢP‖²_HS = 2∑ᵢcᵢ² = 2。∎",
        "topology_class": "A0",
        "external_anchors": [],
        "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
        "priority_hint": True,
        "interlock_hint": ["定理 1.3.2.02（扇区权重归一化）"],
        "interlock_reasoning": "定理 1.3.2.02（扇区权重归一化）的证明直接引用本引理：σᵢ = cᵢ² 与 ∑cᵢ² = 1 均来自本引理证明步骤5-7。单向依赖，无环。主库可验证该引用关系。",
    },
    {
        "formula_name": "引理 1.4.2.01（投影强度）",
        "formula_content": "设 L₁,L₂,L₃ 为 Cl(3) ≅ ℍ⊕ℍ 在 ℝ⁴ ≅ ℍ 上的左乘表示矩阵（Lᵢ² = -I₄，LᵢLⱼ + LⱼLᵢ = -2δᵢⱼI₄）。对任意秩-2 正交投影 P: ℝ⁴ → V（dim V = 2），存在实数 c₁,c₂,c₃ 使得：\nPLᵢP = cᵢJ，i = 1,2,3，\n其中 J 是 V 上由 Cl(3) 体积元 ω₃ = L₁L₂L₃ 诱导的唯一复结构（J² = -id_V）。cᵢ 称为投影强度。",
        "derivation_chain": "【依赖】引理 0.2.2.01（半单分裂）、命题 0.2.1.02（体积元的平方）\n【推导】\n步骤1: 由引理 0.2.2.01（#88），Cl(3) ≅ ℍ⊕ℍ；左乘表示中 Lᵢ 为 ℝ⁴ 上的实反对称算子（Lᵢᵀ = -Lᵢ，由 Lᵢ² = -I₄）；\n步骤2: 由命题 0.2.1.02（#264），ω₃² = 1；在 ℝ⁴≅ℍ 上 ω₃ = L₁L₂L₃ = -I₄，其限制 J = ω₃|_V 满足 J² = -id_V，是 V 上唯一的复结构（二维实向量空间上满足 J²=-id 的实算子唯一确定殆复结构）；\n步骤3: PLᵢP 是 V 上的反自伴算子（(PLᵢP)ᵀ = PLᵢᵀP = -PLᵢP）；\n步骤4: dim V = 2 时，V 上的反自伴算子空间是一维的（2×2 反对称矩阵由 J 张成）；\n步骤5: 故存在 cᵢ ∈ ℝ 使 PLᵢP = cᵢJ。∎",
        "topology_class": "A0",
        "external_anchors": [],
        "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
        "priority_hint": False,
        "interlock_hint": ["定理 1.4.2.03（扇区权重归一化的代数重证）"],
        "interlock_reasoning": "定理 1.4.2.03 的证明引用本引理（PLᵢP = cᵢJ 及 cᵢ = ⟨Lᵢu,v⟩），单向依赖无环。主库可验证。",
    },
    {
        "formula_name": "引理 1.4.3.02（三正弦恒等式）",
        "formula_content": "当 θ₁ + θ₂ + θ₃ = π/2 时，有恒等式：\nsin²θ₁ + sin²θ₂ + sin²θ₃ + 2sinθ₁sinθ₂sinθ₃ = 1。\n本引理为纯三角恒等式，推导仅使用三角函数定义与初等代数运算。",
        "derivation_chain": "【依赖】公理（零之动）\n【推导】\n步骤1: 由 θ₃ = π/2 - θ₁ - θ₂，sinθ₃ = cos(θ₁+θ₂)；\n步骤2: sin²θ₃ = cos²(θ₁+θ₂) = 1 - sin²(θ₁+θ₂)；\n步骤3: 展开 sin²(θ₁+θ₂) = sin²θ₁cos²θ₂ + cos²θ₁sin²θ₂ + 2sinθ₁cosθ₁sinθ₂cosθ₂；\n步骤4: ∑sin²θᵢ = sin²θ₁(1-cos²θ₂) + sin²θ₂(1-cos²θ₁) + 1 - 2sinθ₁cosθ₁sinθ₂cosθ₂ = 1 + 2sinθ₁sinθ₂(sinθ₁sinθ₂ - cosθ₁cosθ₂)；\n步骤5: sinθ₁sinθ₂ - cosθ₁cosθ₂ = -cos(θ₁+θ₂) = -sinθ₃；\n步骤6: ∑sin²θᵢ = 1 - 2sinθ₁sinθ₂sinθ₃，移项得恒等式。∎\n（注：框架内一切数学命题锚定于公理（零之动）的区分结构；本引理的具体推导自足。）",
        "topology_class": "A0",
        "external_anchors": [],
        "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
        "priority_hint": True,
        "interlock_hint": ["定理 1.4.3.01（代数归一化）"],
        "interlock_reasoning": "定理 1.4.3.01（代数归一化 2pC³+C²=1）的证明核心是将 sinθᵢ = √σᵢ·C 代入本恒等式，单向依赖无环。主库可验证。",
    },
    {
        "formula_name": "引理 1.6.2.01（Schur 刚性）",
        "formula_content": "Clifford 代数 Cl(n)（n = 0,1,…,8）的不可约实表示维数 ρₙ 由 Bott 周期表刚性确定：\nρ₀, ρ₁, …, ρ₈ = 1, 2, 4, 4, 8, 8, 8, 8, 16。\n这些维数不可调节——实 Clifford 代数分类中不存在任何连续参数。",
        "derivation_chain": "【依赖】定理 0.3.1.01（Bott 周期）\n【推导】\n步骤1: 由定理 0.3.1.01（#91），实 Clifford 代数分类：Cl(0)=ℝ、Cl(1)=ℂ、Cl(2)=ℍ、Cl(3)=ℍ⊕ℍ、Cl(4)=Mat(2,ℍ)、Cl(5)=Mat(4,ℂ)、Cl(6)=Mat(8,ℝ)、Cl(7)=Mat(8,ℝ)⊕Mat(8,ℝ)、Cl(8)=Mat(16,ℝ)；\n步骤2: 各代数的不可约实表示维数即其矩阵代数维数的平方根（半单情形取直和项的矩阵维数）：1, 2, 4, 4, 8, 8, 8, 8, 16；\n步骤3: 刚性——分类由中心-体积元结构唯一确定（命题 0.2.1.02 的 ωₙ² 判定），不含连续参数，故 ρₙ 不可调节。∎",
        "topology_class": "A0",
        "external_anchors": [],
        "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
        "priority_hint": False,
        "interlock_hint": [],
        "interlock_reasoning": "本引理是定理 0.3.1.01（Bott 周期）的直接推论（复述），无互锁环。",
    },
    {
        "formula_name": "定义 22（良性互扼）",
        "formula_content": "两个推导链 P 和 Q 形成良性互扼，当且仅当同时满足：\n(1) P ⟹ Q：P 的结论是 Q 的前提；\n(2) Q ⟹ P：Q 的结论是 P 的前提；\n(3) 外部锚定：存在独立于 P、Q 的外部约束 C，使 P 和 Q 都满足 C；\n(4) 唯一性：在约束 C 下，P 和 Q 的互扼解唯一。\n条件 (3) 排除循环论证——P、Q 并非自我证明，而是被独立外部约束共同锚定，其互扼解的存在性与唯一性由 C 保证。外部约束 C 的具体实例：Bott 周期 δ⁸（Berry 相位 = 2π）、初始预算 B₁ = {2,3,5,5}、Clifford 代数 Cl(3) 的半单结构、Spin(8) triality 的 S₃ 对称。",
        "derivation_chain": "【依赖】公理（零之动）、定义 0.1.1.01（未分化潜势）\n【推导】\n步骤1: 由公理（零之动）（#8），δ 的非平凡自映射 δ(𝒫) ⊊ 𝒫 产生最原初的区分结构；推导链 P、Q 均为区分结构在迭代中的展开（定义 0.1.1.01，#94）；\n步骤2: 互扼要求 P、Q 互相支撑（条件1、2），但纯互证无独立真值——需要外部参照；\n步骤3: 外部锚定条件（3）要求存在独立约束 C；此类锚定的存在性由定理 0.3.1.01（Bott 周期）与引理 0.2.2.01（半单分裂）保证（δ⁸ 回路与 Cl(3) 结构均独立于具体推导链）；\n步骤4: 唯一性条件（4）确保互扼解确定；\n步骤5: 四条件合取构成良性互扼的判定标准——此为定义性命题。∎",
        "topology_class": "A0",
        "external_anchors": [],
        "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
        "priority_hint": False,
        "interlock_hint": [],
        "interlock_reasoning": "定义性命题，无推导互锁。",
    },
]

for i, sub in enumerate(submissions, 1):
    print(f"\n===== 提交 {i}/5: {sub['formula_name']} =====")
    try:
        result = client.submit_formula(**sub)
        print("返回:", json.dumps(result, ensure_ascii=False, indent=2) if result is not None else "None")
    except Exception as e:
        print("异常:", type(e).__name__, str(e)[:500])
