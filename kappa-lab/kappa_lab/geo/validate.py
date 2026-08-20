"""几何预言三关审查器。

任何进入 kappa-lab 的"几何化"声称必须通过三关：
- C1 闭合性：推导链每步有定理/命题支撑，无"恰好 X 倍"后验因子
- C2 先验性：预言数值先于数据确定（不允许先看答案再选幂次/因子）
- C3 无循环：不允许用观测锚定反推再算回（η_K 教训）

已知反例库（禁止模式）来自教学反馈与 10.8 审计：
- η_K 循环：ε_geo 由 η_K≈1mm 观测锚定反推，再用 η_K^geo 算回 η_K
- St 涨落因子：√(N_info/N_dec)≈2.28 是"为命中 0.2 而乘的倍数"
- σ_n 巧合：sinθ_C/(√3·π²)=0.02580 vs 形状噪声 0.02582，实验参数构成，禁止声称
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 层级：T=定理级 / P=命题级（显式假设）/ C=构造级（构造输入）/ X=不可几何化
LEVELS = ("T", "P", "C", "X")

# 禁止模式关键词：出现即触发 C1 警报
FORBIDDEN_PATTERNS = [
    "恰好", "刚好", "正是所需的", "拉到位", "巧合地命中",
    "反推标定", "由观测锚定反推", "后验标定因子",
]

# 已知反例（审计记录），用于 C2/C3 的自动化对照
KNOWN_VIOLATIONS = [
    "η_K^geo=0.254 由 η_K≈1mm 标定 ε_geo 再算回 η_K",
    "√(N_info/N_dec) 涨落因子（Strouhal 后验标定）",
    "σ_n=0.0258 与 sinθ_C/(√3π²) 的 1.0009 数值巧合",
]


@dataclass
class GeoClaim:
    """一条几何预言声称。"""

    name: str
    value: float | None          # 预言数值（先于数据固定，C2）
    chain: list[str] = field(default_factory=list)   # 推导链：每步引用定理/命题
    inputs: list[str] = field(default_factory=list)  # 显式输入清单（实验锚定必须列出）
    level: str = "C"             # T / P / C / X
    status: str = "待检验"        # 待检验 / 命中 / 未命中 / 已关闭

    def __post_init__(self):
        assert self.level in LEVELS, f"非法层级 {self.level}"


@dataclass
class AuditReport:
    claim: GeoClaim
    checks: dict[str, list[str]]   # C1/C2/C3 -> 违规列表（空=通过）
    verdict: str                   # 通过 / 违规 / 不可几何化


def check_closure(claim: GeoClaim) -> list[str]:
    """C1 闭合性：推导链完整、无后验因子。"""
    issues = []
    if not claim.chain:
        issues.append("推导链为空")
    for step in claim.chain:
        for pat in FORBIDDEN_PATTERNS:
            if pat in step:
                issues.append(f"步骤含禁止模式'{pat}': {step[:80]}")
        if "假设" in step or "构造" in step and claim.level == "T":
            issues.append(f"定理级声称却含未证假设: {step[:80]}")
    return issues


def check_prior(claim: GeoClaim) -> list[str]:
    """C2 先验性：预言数值先于数据。"""
    issues = []
    if claim.value is None:
        issues.append("预言数值为空（不能后补）")
    for v in KNOWN_VIOLATIONS:
        if any(v.split("=")[0] in s for s in claim.chain) or v.split("=")[0] in claim.name:
            issues.append(f"与已知反例冲突: {v}")
    return issues


def check_noloop(claim: GeoClaim) -> list[str]:
    """C3 无循环：输入清单与预言目标不得重叠。"""
    issues = []
    for inp in claim.inputs:
        if inp.strip().startswith(claim.name.split(" ")[0]):
            issues.append(f"输入'{inp}'与预言目标同名（循环）")
    if claim.level == "X":
        issues.append("标记为不可几何化，仅作记录")
    return issues


def audit(claim: GeoClaim) -> AuditReport:
    c1 = check_closure(claim)
    c2 = check_prior(claim)
    c3 = check_noloop(claim)
    ok = not (c1 or c2 or c3)
    verdict = "通过" if ok else ("不可几何化" if claim.level == "X" else "违规")
    return AuditReport(claim, {"C1": c1, "C2": c2, "C3": c3}, verdict)


def register(claim: GeoClaim) -> AuditReport:
    """注册一条预言并执行三关审查（写入 geo 目录的注册表）。"""
    rep = audit(claim)
    return rep
