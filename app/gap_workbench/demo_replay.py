#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回放演示：用两个真实跑过的缺口（χ_L 悬挂量 / $(d/2)^{-d/2}$ 幻觉）
端到端验证 gap_workbench 全流程：建台 → 模板建线 → 推进 → 死胡同/闭合 →
收敛判据 → 反向审计 → 报告。

运行：python3 tools/gap_workbench/demo_replay.py
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gap_workbench import Workbench, suggest_lines  # noqa: E402
from gap_workbench.models import EV_VERIFIED, EV_FLAGGED, EV_OUTSCOPE  # noqa: E402
from gap_workbench.report import build_report  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def build_chiL() -> Workbench:
    """缺口 A：χ_L（Born法则长度基底）的定义与推导链"""
    wb = Workbench.create(
        gap_id="chiL",
        title="χ_L（Born法则长度基底）的定义与推导链",
        anchors=[
            "χ_L = 1.509e-10 m（χ_L² = 2.277e-20 m²，10.8 构造 8.1 直接使用）",
            "χ_T = 3.616e-17 s（术语表：Born法则时间基底）",
            "术语表：χ_L = Born法则长度基底 = 1.509e-10 m（仅名称+数值，无推导）",
        ],
        target="找到 χ_L 的正式定义定理（含推导链），或确认其为'悬挂量'（推导链断裂）",
        gap_type="NUMERIC",
    )
    wb.add_lines_from_template(suggest_lines("NUMERIC"))

    # 线1 结构/来源检索：1.x 系列
    wb.push_result("线1", "1.3 定理索引+§7 核实：无 χ_L（1.3.4.01 = Born法则 Δλ∝√σ，不含长度）",
                   "1.3 定理索引 view_article 核实")
    wb.push_result("线1", "1.5 为作用量文章（S(σ) 定义），无 χ_L；5.10 的 ℓ_mfp=0.0506 是几何单位，非 χ_L",
                   "1.5 目录 view + 5.10 原文核实")
    wb.mark_dead_end("线1", "排除 1.3/1.5/5.10 作为 χ_L 定义出处")

    # 线2 机制：0.x/2.x 候选
    wb.push_result("线2", "0.3 为 Bott周期文章；0.3.1'量纲桥'文章已不存在（file_list/list_articles 核实）——候选载体消失",
                   "file_list '*量纲*' + list_articles '0.3'",
                   status=EV_FLAGGED,
                   note="0.3 内容未详查；0.3.1 是否曾存在仅能确认当前不存在")
    wb.partial_line("线2", "候选载体 0.3.1 消失，标注待查")

    # 线3 锚定/归因：幽灵引用
    wb.push_result("线3", "10.10 §2.1 把 (K,χ_L,χ_T,λ₁,λ₂) 归因'谱展开/Born法则（定理 1.3.4.01）参数'；"
                          "但 1.3 定理索引核实 1.3.4.01 = Born法则 Δλ∝√σ，不含 χ_L → 幽灵引用确认",
                   "10.10 §2.1 view + 1.3 定理索引 view")
    wb.close_line("线3", "χ_L 的归因引用（定理 1.3.4.01）是幽灵引用：被引定理不含该量")

    # 线4 数值反推
    wb.push_result("线4", "χ_L·v_geo^eff/χ_T = 1.509e-10×71.5609/3.616e-17 = 2.9866e8 vs c = 2.9979e8，差 0.38%",
                   "本地数值重算（v_geo^eff=71.56 来自 10.8 构造 3.1）",
                   status=EV_FLAGGED, note="0.38% 接近但不精确，不采信为闭式")
    wb.push_result("线4", "χ_L/√μ_Cl = 276.3 pm = 水 O···O 距离（10.8 构造 8.1' 与 10.10 表4 的 276 pm 一致，差 0.1%）",
                   "10.8 构造 8.1' 原文 + 10.10 表4 原文")
    wb.partial_line("线4", "物理身份锚定成立（分子尺度），数值闭式未找到")

    # 线5 一致性：物理锚定
    wb.push_result("线5", "χ_L ≈ 0.15 nm 为原子/分子联合截面尺度；χ_L ≈ 2.85 a₀（玻尔半径）；"
                          "d_water = χ_L/√μ_Cl = 276.3 pm 与实验 O···O 距离一致",
                   "数值对照（a₀=5.29e-11 m 物理常数）")
    wb.close_line("线5", "χ_L 物理身份 = 分子尺度联合截面（0.15 nm），但无几何推导链")

    # 收敛
    conclusion = ("χ_L 是悬挂量：术语表仅给名称+数值（Born法则长度基底=1.509e-10 m），无推导链；"
                  "10.10 归因定理 1.3.4.01 为幽灵引用；候选载体 0.3.1 量纲桥文章已消失")
    check = wb.converge(conclusion, ["E1", "E4", "E7", "E6"], support=["线3", "线5"])
    assert check["ok"], f"χ_L 应收敛，实际未收敛：{check['reason']}"
    return wb


def build_dhalf() -> Workbench:
    """缺口 B：$(d/2)^{-d/2}$ 精确形式验证（幻觉判定）"""
    wb = Workbench.create(
        gap_id="dhalf",
        title="$(d/2)^{-d/2}$ 精确形式验证",
        anchors=[
            "压力测试 T6 声称：'$(d/2)^{-d/2}$ 的精确形式【未验证】——需类大小闭式与噪声模型联合推导'",
            "真实闭式：c_d = C(n,w₀)P(w₀)fail(w₀)2^{-2w₀}（QEC paper 定理 16、10.35 定理 10.35.1.01）",
            "10.31：loss ~ θ_max^{2⌈d/2⌉}（指数形式）",
        ],
        target="确认库内是否存在 $(d/2)^{-d/2}$；若不存在则判定其性质（幻觉/近似/等价）",
        gap_type="FORMULA",
    )
    wb.add_lines_from_template(suggest_lines("FORMULA"))

    # 线1 存在性：全文检索
    wb.push_result("线1", "10.31/10.32/10.33/10.35/QEC paper 检索与原文核实：均无 $(d/2)^{-d/2}$ 或等价写法",
                   "vector_search + view_article 多轮核实")
    wb.mark_dead_end("线1", "库内不存在该形式")

    # 线2 数学化简
    wb.push_result("线2", "渐近结构不符：真实 c_d 指数 = w₀(m−2)−(w₀−r−2)(m−r−1)（2 的线性指数）；"
                          "$(d/2)^{-d/2}$ = 2^{−w₀·log₂w₀}（对数指数）——连渐近结构都不同",
                   "代数化简（对 RM(r,m) 族展开 c_d 闭式）")
    wb.mark_dead_end("线2", "结构不符：不可能是 c_d 的闭式或渐近")

    # 线3 数值对照
    wb.push_result("线3", "d=8：$(d/2)^{-d/2}$ = (4)^{-4} = 3.9e-3 vs [[64,20,8]] 实测斜率 7.96——差 2000 倍",
                   "本地数值重算 vs 10.31 实测数据")
    wb.mark_dead_end("线3", "数值差 3 个数量级，排除")

    # 线4 邻近闭式检查
    wb.push_result("线4", "10.32 闭式 P_r(m) ≈ 2^{−(2^r−r−2)(m−r−1)}（简并比例）；10.33 c_d = 权重 d/2 层失败率——均无 $(d/2)^{-d/2}$ 结构",
                   "10.32 摘要 + 10.33 原文核实")
    wb.mark_dead_end("线4", "邻近闭式无类似形式")

    # 线5 结论线：真实链条
    wb.push_result("线5", "真实闭式链完整闭合：10.31（θ^d 指数）→ 10.32（P_r(m) 闭式）→ 10.33（c_d=权重d/2层失败率）→ 10.35/QEC paper 定理16（c_d 精确闭式）",
                   "四篇文章原文交叉核实")
    wb.close_line("线5", "损失标度闭式链条完整，无需 $(d/2)^{-d/2}$")

    # 收敛
    conclusion = ("$(d/2)^{-d/2}$ 是幻觉（压力测试 LLM 生成的形式）：库内无此形式、"
                  "数值差 2000 倍、渐近结构不符；真实闭式链（10.31→10.32→10.33→10.35 定理16）完整闭合")
    check = wb.converge(conclusion, ["E1", "E3", "E2", "E5"], support=["线5"])
    assert check["ok"], f"dhalf 应收敛，实际未收敛：{check['reason']}"
    return wb


def run_gap(wb: Workbench, name: str) -> None:
    items, stats = wb.audit()
    md = build_report(wb.gap, stats)
    path = os.path.join(OUT_DIR, f"{wb.gap.id}.md")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"===== {name} =====")
    print(f"收敛：{'✅' if wb.gap.converged else '❌'} {wb.gap.converged_note}")
    for l in wb.gap.lines:
        print(f"  {l.id}【{l.hypothesis}】{l.status}" +
              (f"：{l.note[:60]}" if l.note else ""))
    print(f"审计：✅ {stats['verified']} ｜ ⚠️ {stats['flagged']} ｜ "
          f"❌ {stats['failed']} ｜ 📌 {stats['outscope']}")
    assert stats["failed"] == 0, f"{name} 审计不应有 ❌"
    print(f"报告：{path}")
    print()


def main() -> None:
    chiL = build_chiL()
    dhalf = build_dhalf()
    run_gap(chiL, "缺口 A：χ_L（悬挂量）")
    run_gap(dhalf, "缺口 B：$(d/2)^{-d/2}$（幻觉）")
    # 持久化 JSON 验证
    p1 = os.path.join(OUT_DIR, "chiL.json")
    p2 = os.path.join(OUT_DIR, "dhalf.json")
    chiL.save(p1)
    dhalf.save(p2)
    wb2 = Workbench.load(p2)
    assert wb2.gap.id == "dhalf" and wb2.gap.converged, "JSON 往返失败"
    print(f"✅ 端到端验证通过：状态持久化（JSON 往返）正常，报告已生成")
    print(f"   {p1}\n   {p2}")


if __name__ == "__main__":
    main()
