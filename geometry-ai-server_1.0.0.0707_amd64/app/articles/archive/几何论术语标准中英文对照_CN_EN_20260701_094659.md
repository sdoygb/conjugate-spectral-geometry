# 几何论术语标准中英文对照

> **版本**：260701.9  
> **用途**：几何论全部术语在此统一。任何新文章引入术语前必须先在本表登记。  
> **语言**：中文 / English  
> **更新规则**：见 §11 维护规则

---

## §1 公理体系

> 公理 = 理论的全部自由输入。几何论有三条公理，无第四条。

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 公理1（角度和） | Axiom 1 (Angle Sum) | $\theta_M + \theta_C + \theta_I = 90^\circ$ | 0.0.3 §2 |
| 公理2（作用量和） | Axiom 2 (Action Sum) | $S = \sum \frac{1}{\sin^2\theta_i} + \sum_{i<j} \frac{1}{\sin\theta_i\sin\theta_j}$ | 0.0.3 §2 |
| 公理3（质量-角度耦合） | Axiom 3 (Mass-Angle Coupling) | $m = K \sin^3\theta_M$ | 0.0.3 §2 |

---

## §2 场与空间

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 信息场 | Information Field $\mathcal{I}$ | $\mathcal{I}(x,t)$，满足热方程 | 0.4 §2 |
| 因果场 | Causal Field $\mathcal{C}$ | 动力学变量，与 $\mathcal{I}$ 耦合 | 0.5 §3 |
| 物质场 | Matter Field $\mathcal{M}$ | 激发态在切丛上的表示 | 0.0.5 §3 |
| 约束乘积球面 | Constrained Product Spheres | $M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$ | 0.0.5 定义3.1 |
| 10方几何空间 | 10-direction Geometric Space $\mathcal{T}$ | 具有三分切丛结构、全息屏编码、谱刚性的约束乘积球面族 | 0.0.7 §5.4 |
| 全息屏 | Holographic Screen $\Sigma$ | 能量-信息编码边界 | 0.0.6 §3 |
| 三分切丛 | Tripartite Tangent Bundle | $T\mathcal{T} = T\mathcal{M} \oplus T\mathcal{C} \oplus T\mathcal{I}$ | 0.0.6 §2 |
| 谱三元组 | Spectral Triple | $(\mathcal{A}, \mathcal{H}, D)$，非交换几何构造 | 0.0.5 §7 |
| 上同调层 | Cohomological Layer | $H^k$ 隐喻，区分严格数学与识别层 | 0.0.6 §5 |

---

## §3 核心映射 ℰ

> ℰ 是几何论物理识别的唯一锚点。质量、光速等均为其导出项，不是第四条公理。

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| ℰ 映射（量纲桥） | ℰ-map (Dimensional Bridge) | $\mathcal{E}: \text{几何量} \to \text{物理量}$ | 0.3.1 §4 |
| ℰ 映射锚点 | ℰ-map Anchor | ℰ 映射的固定点：$c = 2.99792458 \times 10^8$ m/s 为唯一外部输入 | 0.3.1 §4 |
| 物理特征长度 $\chi_L$ | Physical Characteristic Length | $\chi_L = 1.509 \times 10^{-10}$ m（由几何 $\chi_L(\ell_0) \approx 1.983$ 经 ℰ 映射量纲桥转换） | 0.3.1 §4, 0.0.7 §7.3 |
| 物理特征时间 $\chi_T$ | Physical Characteristic Time | $\chi_T = 3.616 \times 10^{-17}$ s | 0.3.1 §4 |

---

## §4 定理

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 谱刚性定理 | Spectral Rigidity Theorem | 约束乘积球面上 Laplace 谱唯一确定尺度因子 $a$ | 0.0.5 定理4.1 |
| 桥接函数标准形 | Bridging Function Standard Form | $S = 12(a^2/\ell_0^2 + \ell_0^2/a^2)$，由 (C1)–(C3) 加归一化条件唯一确定 | 0.0.7 定理5.3, 定义5.2 |
| 值域协调定理 | Range Compatibility Theorem | 六项作用量值域与抽象几何量值域严格相容 | 0.0.7 定理4.1 |
| 互锁常数唯一性定理 | Interlocking Constants Uniqueness Theorem | $(\Lambda, k_0, \ell_0) = (3, 2, V_{\text{unit}}^{-1/9})$ 唯一确定 | 0.0.7 定理7.1–7.2 |
| 自举封闭定理 | Bootstrap Closure Theorem | 10方几何空间所有数学结构构成封闭链条 | 0.0.7 定理7.3 |
| 信息场热方程 | Information Field Heat Equation | $\partial_t \mathcal{I} = \chi_T \Delta \mathcal{I}$ | 0.4 定理2.1 |
| 信息场衰减定理 | Information Field Attenuation Theorem | 上饱和稳态 $\theta_I \sim 72.53^\circ$ | 0.4.1 |
| 三分切丛置换群刚性定理 | Tripartite Bundle Permutation Group Rigidity Theorem | $S_3$ 是置换群的唯一选择 | 0.0.7 定理2.0' |

---

## §5 常数与参数

| 中文 | 英文 | 值 / 表达式 | 出处 |
|---|---|---|---|
| 互锁常数 $\Lambda$ | Interlocking Constant | $\Lambda = \Lambda(S_3) = 3$ | 0.0.3 §3 |
| 互锁常数 $k_0$ | Interlocking Constant | $k_0 = k_0(S_3) = 2$ | 0.0.3 §3 |
| 标度常数 $\ell_0$ | Scale Constant | $\ell_0 = V_{\text{unit}}^{-1/9} \approx 0.5991$（几何单位，无量纲） | 0.0.7 定理7.2 |
| 精细结构常数倒数 $S_e$ | Inverse Fine-Structure Constant | $S_e = 137.035999084$（锁定值） | 0.0.3 §5 |
| 有效耦合 $\lambda_1^{\text{eff}}$ | Effective Coupling | 391.05 | 0.0.3 §5 |
| 有效耦合 $\lambda_2^{\text{eff}}$ | Effective Coupling | 59324.3 | 0.0.3 §5 |
| 质量标度 $K$ | Mass Scale | $K = 839.758793$ keV | 0.0.3 §5 |
| 几何衰减宽度 $\Gamma_{\text{geo}}$ | Geometric Decay Width | $5.75 \times 10^{-23}$ | 0.4.1 |
| 几何特征长度 $\chi_L(\ell_0)$ | Geometric Characteristic Length | $\approx 1.983$（无量纲，纯几何量） | 0.0.7 §7.3 |
| Wodzicki 留数 | Wodzicki Residue | $\mathrm{Res}_W(D^{-9}) = 512\pi^4 V/105$ | 0.0.7 §7.3 |

---

## §6 粒子与扇区

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质扇区 | Matter Sector ($M$) | $\theta_M$ 主导，带电轻子质量层级 | 0.0.3 §4 |
| 因果扇区 | Causal Sector ($C$) | $\theta_C$ 主导，中微子质量与振荡 | 0.0.3 §4, 7 |
| 信息扇区 | Information Sector ($I$) | $\theta_I$ 主导，场动力学 | 0.0.3 §4, 0.4 |
| 角度锁定 | Angle Locking | $\theta_M=30^\circ, \theta_C=30^\circ, \theta_I=30^\circ$（对称点） | 0.0.3 定理3.1 |
| 上饱和稳态 | Upper Saturation Steady State | $\theta_I \approx 72.53^\circ$（信息场演化终态） | 0.4.1 |

---

## §7 角度与几何量

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质角 $\theta_M$ | Matter Angle | 公理1变量之一 | 0.0.3 §2 |
| 因果角 $\theta_C$ | Causal Angle | 公理1变量之一 | 0.0.3 §2 |
| 信息角 $\theta_I$ | Information Angle | 公理1变量之一 | 0.0.3 §2 |
| eta 参数 | Eta Parameter | $\eta = 51.27^\circ$，当前演化状态 | 0.4.1 |

---

## §8 概念名称（非定理）

> 以下为概念名称，不加"定理"后缀。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 九素互扼 | Nine-Element Mutual Constraint | 公理—常数—工具层之间的超定锁定结构（打包了多个约束条件，非独立定理） | 0.0.7 §6.2 |
| 全息屏编码条件 | Holographic Encoding Condition | 能量-信息在全息屏上的编码约束 | 0.0.6 §3 |
| CIM 相 | CIM Phase | 标准模型/广义相对论/弦论作为低能有效场论近似 | 0.2 §1 |

---

## §9 构造性概念（诚实标注）

> 以下为构造性概念，非严格定理。在文章中使用时必须加「诚实标注」。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 桥接函数标准形（定义5.2） | Bridging Function Standard Form | 原称"桥接公理"，但非公理（几何论只有三条公理）。标准化为 $S=12(a^2/\ell_0^2+\ell_0^2/a^2)$，归一化条件为构造性假设 | 0.0.7 定义5.2, 5.2' |
| $\ell_0$ 的物理涌现 | Emergence of $\ell_0$ | $\ell_0$ 是谱几何单位锚点，与实验长度尺度的匹配属于条件性命题层 | 0.0.7 §7.3 |
| $\hbar$ 数值涌现 | Emergence of $\hbar$ | $\hbar$ 从几何量经 ℰ 映射涌现，属于条件性命题 | 0.3.1 |

---

## §10 禁用词清单

> 以下术语不得在任何新文章中使用。审核已有文章时发现即修正。

| 禁用词 | 替代词 | 为何禁用 |
|---|---|---|
| 桥接公理 | 桥接函数标准形 | 几何论只有三条公理，暗示第四公理会造成体系混淆 |
| 九素互扼定理 | 九素互扼 | 九素互扼是概念名称，打包了多个约束条件，不是独立定理 |
| 公理4 / 第四公理 | （无替代，不存在） | 几何论公理体系严格限于三条 |
| 唯一锚点 c / 单一锚点 c / 外部锚点 c / 光速锚点 | ℰ 映射锚点 | 所有变体均禁用，此处统一登记。c 不是"公理"，是 ℰ 映射的唯一外部固定点 |
| $S_3$ 矩映射 | $S_3$ 外尔房破缺坐标 | $S_3$ 是有限群，$\mu$ 不是连续李群作用的标准矩映射 |
| 面积量子化（在0.0.7语境） | 面积分割关系（条件性命题） | 不自洽，已降格为条件性命题 |

---

## §11 维护规则

### §11.1 新增术语
任何新文章引入术语前，必须先在本表中登记。登记需提供：
1. 中文名 + 英文名
2. 精确定义或公式
3. 出处（文章编号 + 节号/定理号）
4. 分类（公理 / 定理 / 定义 / 概念名称 / 构造性概念）

### §11.2 术语冲突解决
若多篇文章对同一术语给出不同定义：
- **优先级**：卷0（0.0.X、0.1）> 桥梁卷（0.2–0.5）> 应用篇（1+）> 构造性概念
- 卷0内的冲突以版本号高者为准
- 应用篇如需偏离卷0定义，必须显式标注"本文约定"

### §11.3 定理标签使用
- **定理** = 有明确陈述（"定理 X.Y"） + 完整证明（"证明"块）。两者缺一不可
- 概念名称归入 §8，不得加"定理"后缀
- 构造性假设归入 §9，不得加"定理"后缀

### §11.4 禁用词执法
- §10 所列禁用词不得在任何新文章中使用
- 审核已有文章时发现禁用词 → 立即修正
- 新增禁用词需经用户确认后登记

### §11.5 版本号
- 格式：`YYMMDD.N`（如 260701.9）
- 版本号不含括号说明，不含修订摘要，不含工作痕迹
- 所有修改记录归 git commit message，不写入文章正文

### §11.6 文章写作原则
- **禁止工作痕迹**：文章中不得出现"旧版本曾用""已删除""已修正""修订说明""本次修改"等修改历史记录
- **禁止版本考古**：注记中不得引用旧版本公式或叙述"此前版本中……"
- 推导过程自洽呈现，历史归 git
- 附录中不得设"修订历史"章节
