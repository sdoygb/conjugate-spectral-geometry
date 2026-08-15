# 空间群对称性拓扑超导筛选器

**零成本第一级筛选：哪些晶体结构可能承载拓扑超导？**

输入一个空间群号（1–230），本工具应用对称性判据回答一个问题：
*这种材料是否可能是拓扑超导候选？* 判定耗时约 1 微秒，无需任何电子结构计算。

- **判据**：共扼谱几何《超导几何理论》（欧阳国彬，2026；文章 9.1）定理 9.1.12.01
- **输入**：空间群号（或点群符号）
- **输出**：`CANDIDATE`（候选）/ `EXCLUDED`（排除），附可读解释
- **依赖**：无（纯 Python 标准库）

---

## 判据

拓扑超导的必要条件是晶体点群同时包含：

1. **C₃ 旋转**（三重轴）
2. **Z₂ 对称**（镜面反射或空间反演）

等价于格点对称群与 triality 置换对易：`[G_晶格, T] = 0`。

由此 32 个晶体点群缩减为 **11 个候选**：

```
D6h  D3h  D3d  Oh  Td  C3i  C3v  C3h  C6h  C6v  Th
```

对应 **230 个空间群中的 52 个（22.6%）**。

含 C₃ 但缺 Z₂ 的点群（C3, D3, C6, D6, T, O）被排除；所有无三重轴的点群
（如 D4h、D2h——大多数铜基、铁基超导体的点群）也被排除。

> **重要**：这是*必要条件*——第一级筛选。它本身**不预言超导**。
> 候选材料仍需通过完整三问判据（Q1 拓扑表面态 K̃⁰≠0；Q2 有效通道数
> N_eff≥3；Q3 磁性状态允许配对）。完整理论见文章 9.1 §11–§12。

---

## 快速开始

```bash
# Python 3.8+，无依赖
python screening.py 194          # CANDIDATE  (P6_3/mmc, D6h  -> UPt3)
python screening.py 139          # EXCLUDED   (I4/mmm, D4h    -> Sr2RuO4)
python screening.py 166          # CANDIDATE  (R-3m, D3d      -> Bi2Se3)
python screening.py 47           # EXCLUDED   (Pmmm, D2h      -> YBCO)

python screening.py --list       # 52 个候选空间群
python screening.py --selfcheck  # 内置回归测试（12/12）
```

库用法：

```python
from screening import is_candidate, sg_to_pointgroup, explain

is_candidate(194)      # True   (UPt3 型：D6h)
is_candidate(129)      # False  (FeSe 型：D4h)
sg_to_pointgroup(216)  # 'Td'   (半 Heusler)
print(explain(71))     # EXCLUDED -- 无 C₃ 旋转
```

---

## 验证结果

三层独立验证，全部通过。

### 第一层——94 种已知超导体（独立清单）

取自维基百科 *List of superconductors*（独立抓取，非几何论文章集）。

| 结果 | 数量 | 占比 |
|---|---|---|
| 候选空间群 | 70 | 74.5% |
| 排除 | 24 | 25.5% |

**被排除的 24 种全部可归因于非拓扑配对路径**——没有一种是公认的拓扑超导：

- 5 种 I 型 BCS 元素（Ga, In, Pa, Sn, U）——体 BCS（S1 路径）
- 6 种铜基（YBCO、BSCCO、HBCCO、214 等）——d 波，非拓扑
- 8 种铁基（1111、122、11 家族）——s± 自旋涨落
- 1 种镍基（La₃Ni₂O₇）——非拓扑
- FeB₄——弱耦合 BCS
- Sr₂RuO₄、UTe₂——**判据的排除预言**（Sr₂RuO₄ 与 2021–2024 实验一致；
  UTe₂ 仍在实验争论中）

**所有公认的拓扑超导候选 100% 通过**：Bi₂Se₃ 家族、Bi₂Te₃/Sb₂Te₃、
MnBi₂Te₄、SnTe（TCI）、YPtBi/LuPtBi/LaPtBi（半 Heusler）、UPt₃、
PrOs₄Sb₁₂、Bi₂Pd（γ 相 Fd-3m）。

### 第二层——Materials Project 全库（154,377 种材料）

MP API 查询（2026-08）：154,377 种材料中

- **41,077 种（26.61%）** 落在 52 个候选空间群
- **113,300 种（73.39%）** 在对称层面即被排除

即：第一级筛选在没有任何电子结构计算之前，就移除了约 3/4 的材料。

### 第三层——22 种关键材料 MP 独立确认

22 种地标材料经 Materials Project（独立 DFT 数据库）指派空间群后复核：
拓扑超导候选全部落在候选空间群（✅），铜基/铁基/镍基/Sr₂RuO₄/UTe₂
全部被排除（✅）。详见 `VALIDATION.md`。

---

## 诚实的局限

1. **必要不充分**。通过对称筛选 ≠ 会超导。大多数候选（fcc/hcp/bcc
   元素、A15、MgB₂…）是普通 BCS 超导，在 Q1（拓扑表面态）被排除。

2. **适用域**。判据针对 C₃ 保护的 Dirac 锥/螺旋态路径。拓扑性源于
   *其他*机制的材料（如 Weyl 型能带交叉的 2M-WS₂，C2/m (12)）在适用域
   之外——它们不是反例，但必须明确说明适用域。

3. **UTe₂ 是活的实验风险**。判据预言 UTe₂（Immm, D2h）非拓扑超导；
   但自 2019 年以来 UTe₂ 是最受争议的自旋三重态拓扑超导候选（2024 年
   有表面态观测报道）。这是判据面临的最重要公开实验问题。

4. **相鉴别**。判据作用于具体的超导相。多晶型可能落在不同侧
   （如 Bi₂Pd：γ-Fd-3m 是候选，MP 收录的 C2/m 和 I4/mmm 相不是）。
   必须对实验确定的超导相做筛选。

---

## 理论来源

判据是共扼谱几何《超导几何理论》（文章 9.1，欧阳国彬，2026）
**定理 9.1.12.01**：由谱几何框架推导 `[G_晶格, T] = 0`（T 为 triality
3-循环，Z₂ 对换）。完整三问判据（Q1 拓扑表面态 K̃⁰≠0；Q2 纳米线横截面
点群不可约表示给出 N_eff≥3；Q3 磁性相容）见文章 9.1 §11–§12。本工具
提取其中的纯对称性片段，以便独立验证与复用。

**引用建议**：

> 欧阳国彬，《超导几何理论》文章 9.1，定理 9.1.12.01（2026）。
> 拓扑超导候选的空间群对称性筛选判据。

---

## 仓库结构

```
screening.py              核心判据（空间群 → 判定），零依赖
data/materials_94.csv     第一层验证：94 种已知超导体
data/mp_sg_stats.json     每个候选空间群的 MP 材料数
data/mp_materials_check.json  22 种关键材料 MP 确认结果
scripts/validate_wiki.py  第一层复现脚本（需 spglib）
scripts/query_mp.py       第二/三层复现脚本（需 MP API key）
tests/test_screening.py   单元测试（unittest，零依赖）
VALIDATION.md             英文详细验证报告
VALIDATION_CN.md          中文详细验证报告
```

## 许可证

MIT
