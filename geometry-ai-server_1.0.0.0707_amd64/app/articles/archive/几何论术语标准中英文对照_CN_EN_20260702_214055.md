# 几何论术语标准中英文对照

> **版本**：260702.4  
> **用途**：几何论全部术语在此统一。任何新文章引入术语前必须先在本表登记。  
> **语言**：中文 / English  
> **更新规则**：见 §11 维护规则  
> **本次更新**：自洽性审计修正——拆分 Hopf 定理/假设、修正质量-角度耦合推导标注、去九素互扼措辞矛盾、合并 C_geo 重复条目、新增 0.0.7 旧公理编号冲突记录

---

## §1 公理体系

> 公理 = 理论的全部自由输入。几何论有三条公理，无第四条。
>
> **⚠️ 注意**：早期文章 0.0.7（十方几何空间）使用旧公理编号：公理1=角度和 θ_M+θ_C+θ_I=90°、公理2=作用量和 S=Σ1/sin²θ_i+…。旧编号与下表不兼容。阅读 0.0.7 时请将「公理1」理解为「公理3 完备性约束」、「公理2」理解为「作用量定义」。0.0.7 修订版将统一编号。

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 公理1（圆拓扑） | Axiom 1 (Circle Topology) | $D = S^1 \setminus \{p_0, p_*\}$，激发态参数空间由圆去掉真空点 $p_0$ 与退化点 $p_*$ 得到，含两个开区间分支 $D_\pm$ | 0.0.3 §2.1 |
| 公理2（边界极限） | Axiom 2 (Boundary Limit) | $S: D \to (0,+\infty)$ 在每个分支 $D_\pm$ 上连续，$\lim_{x\to p_0}S(x)=0$（真空极限），$\lim_{x\to p_*}S(x)=+\infty$（退化极限） | 0.0.3 §2.2 |
| 公理3（全息屏编码条件） | Axiom 3 (Holographic Screen Encoding Condition) | 在三分切丛 $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ 的每个 $\mathbb{R}^9$ 纤维中，存在二维全息屏 $\Sigma$，三个扇区投影强度角 $\theta_1,\theta_2,\theta_3\in(0^\circ,90^\circ)$ 满足 $\theta_1+\theta_2+\theta_3=90^\circ$ | 0.0.6 §3.1 |

---

## §2 场与空间

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 信息场 | Information Field $\mathcal{I}$ | $\mathcal{I}(x,t)$，满足热方程 | 0.4 §2 |
| 因果场 | Causal Field $\mathcal{C}$ | 动力学变量，与 $\mathcal{I}$ 耦合 | 0.5 §3 |
| 物质场 | Matter Field $\mathcal{M}$ | 激发态在切丛上的表示 | 0.0.5 §3 |
| 约束乘积球面 | Constrained Product Spheres | $M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$ | 0.0.5 定义3.1 |
| 10方几何空间 | 10-direction Geometric Space $\mathcal{T}$ | 具有三分切丛结构、全息屏编码、谱刚性的约束乘积球面族 | 0.0.7 §5.4 |
| 全息屏 | Holographic Screen $\Sigma$ | 能量-信息编码边界，公理3中定义的二维定向子空间 | 0.0.6 §3 |
| 三分切丛 | Tripartite Tangent Bundle | $T\mathcal{T} = T\mathcal{M} \oplus T\mathcal{C} \oplus T\mathcal{I}$ | 0.0.6 §2 |
| 谱三元组 | Spectral Triple | $(\mathcal{A}, \mathcal{H}, D)$，非交换几何构造 | 0.0.5 §7 |
| 上同调层 | Cohomological Layer | $H^k$ 隐喻，区分严格数学与识别层 | 0.0.6 §5 |
| 三对偶几何空间 | Tri-Dual Geometric Space | 物质扇区 $\mathcal{M}$、因果扇区 $\mathcal{C}$、信息扇区 $\mathcal{I}$ 的对偶耦合几何空间，通过跨扇区耦合 $H^W$ 连接 | 0.1.1 §1 |
| 跨扇区耦合 $H^W$ | Cross-Sector Coupling $H^W$ | 三扇区之间的相互作用哈密顿量，前置因子由 $\mathrm{SU}(3)$ 代数结构决定 | 0.1.1 §2, 0.1.2 §1 |
| 联合截面 | Joint Cross-Section | 三扇区在约束截面上的联合谱结构，由 ℰ 映射统一提升 | 0.3.5 §1, 0.3.9 §1 |
| 约束截面 | Constrained Cross-Section | 参数空间中的几何约束子流形，用于物理态的约化描述 | 0.2.1 §1 |
| 层级约束截面 | Hierarchical Constrained Cross-Section | 多尺度标度下的嵌套约束截面结构 | 0.3.1.1 §1 |
| 全息宇宙 | Holographic Universe | 约束截面框架下的宇宙学全息描述，将宇宙演化映射为信息场动力学 | 0.2.2 §1 |
| 渗透函数 | Percolation Function | 约束截面之间的信息渗透强度函数，控制跨层级耦合 | 0.2.1.1 §1 |
| M场法向几何结构 | M-Field Normal Geometry | M场在三分切丛法向子丛上的几何构造，定义质量生成的几何基础 | 0.6.1 §1 |
| M场呼吸模式 | M-Field Breathing Mode | M场的径向振荡模式，对应 Higgs 粒子的几何起源 | 0.6.5 §1, 4号 §2 |
| M-C腰边耦合 | M-C Waist-Edge Coupling | 物质场与因果场在约束截面边缘的耦合结构 | 0.6.3 §1 |
| M-I耦合 | M-I Coupling | 物质场与信息场的耦合，含 $\mathcal{C}_n$ 方案 | 0.6.4 §1 |
| 三场完全耦合 M-C-I | Complete M-C-I Coupling | 物质-因果-信息三场的完整耦合框架 | 0.6.9 §1 |
| 因果对称性破缺 | Causal Symmetry Breaking | 因果场在信息势驱动下的对称性破缺结构 | 0.5.6 §1 |
| 信息场硬模 | Information Field Hard Mode | 信息场的高频振荡模式，宇宙学残余背景 | 20号 §2 |
| 信息场软模 | Information Field Soft Mode | 信息场的低频集体模式 | 20号 §2, 0.4.4 |
| 三分切丛子结构组合数学 | Tripartite Bundle Substructure Combinatorics | 三分切丛子丛结构的组合分类 | 0.4.3 §1 |
| 几何分子结构 | Geometric Molecular Structure | 基于约束截面的分子几何描述框架 | 0.7 §1 |
| 化学映射 | Chemical Mapping | 约束截面框架到化学元素周期律的几何映射 | 0.2.4 §1 |
| 扩展相空间 | Extended Phase Space | M场量子化的辛相空间扩展，含法向辛结构 | 0.8.1 §1 |
| 夸克扇区 | Quark Sector | 夸克在约束乘积球面上的几何表示，含量子化方案 | 0.8.6 §1 |
| 弯曲结构量子化 | Curved Structure Quantization | 约束截面的弯曲几何形变量子化框架 | 0.2.3 §1 |
| 几何自旋-轨道耦合 | Geometric Spin-Orbit Coupling | 弯曲约束截面中的几何自旋-轨道耦合效应 | 0.2.3 §2 |
| 倒伏相截断 | Lodging Phase Cutoff | 中微子质量谱的高端截断机制，由因果场几何约束决定 | 7号 §3 |

---

## §3 核心映射 ℰ

> ℰ 是几何论物理识别的唯一锚点。质量、光速等均为其导出项，不是第四条公理。

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| ℰ 映射（量纲桥） | ℰ-map (Dimensional Bridge) | $\mathcal{E}: \text{几何量} \to \text{物理量}$ | 0.3.1 §4 |
| ℰ 映射锚点 | ℰ-map Anchor | ℰ 映射的固定点：$c = 2.99792458 \times 10^8$ m/s 为几何论与 SI 单位制之间的**唯一外部物理锚点**（经由 ℰ 映射量纲桥实现） | 0.3.1 §4 |
| 物理特征长度 $\chi_L$ | Physical Characteristic Length | $\chi_L = 1.509 \times 10^{-10}$ m（由几何 $\chi_L(\ell_0) \approx 1.983$ 经 ℰ 映射量纲桥转换） | 0.3.1 §4, 0.0.7 §7.3 |
| 物理特征时间 $\chi_T$ | Physical Characteristic Time | $\chi_T = 3.616 \times 10^{-17}$ s | 0.3.1 §4 |
| ℰ 映射的三扇区联合提升 | ℰ-map Tri-Sector Joint Lift | 将物质、因果、信息三扇区的独立映射统一提升为联合截面谱 | 0.3.5 §2 |
| 谱三元组到密度Liouville的桥接 | Spectral Triple to Density Liouville Bridge | 从谱三元组 $(\mathcal{A},\mathcal{H},D)$ 到因果场密度矩阵 Liouville 描述的桥接映射 | 0.5.6 §1 |
| $\hbar_{\text{eff}}$ 桥接 | $\hbar_{\text{eff}}$ Bridge | 几何论中 $\hbar$ 作为导出量的有效桥接，含三路交叉验证 | 0.8.4 §1 |
| $C_m$ 第一原理计算 | $C_m$ First-Principles Calculation | 约束截面中 $C_m$ 参数的谱几何第一原理推导 | 0.3.3 §1 |

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
| 质量-角度耦合定理 | Mass-Angle Coupling Theorem | $m = K \sin^3\theta_M$（由公理1–3及约束乘积球面构造导出，非公理） | 0.1 §2.2.2, 0.0.3 §5 |
| 光子零质量定理 | Photon Zero Mass Theorem | $m_\gamma = K \sin^3(0^\circ) = 0$，光子零质量是质量映射定理在 $\theta_M=0^\circ$ 的直接推论 | 0.6.8 §2 |
| Hopf纤维化定理（拓扑部分） | Hopf Fibration Theorem (Topological) | 公理3的三分切丛结构可提升为 $S^3 \to S^2$ Hopf纤维化的完整拓扑描述（0.3.6 定理4.3）。**注意**：度量等价 $r_{\mathcal{M}} = r_\Sigma$ 部分仍为假设（见 §9 Hopf假设） | 0.3.6 §2–§4 |
| 扇区约化定理 | Sector Reduction Theorem | 三扇区耦合在约束截面上可约化为低维有效描述 | 0.3.7 定理9.5 |
| G1定理 | G1 Theorem | 因果场第一几何不变量 $G_1$ 的系统性诊断与闭合 | 0.3.7 §4 |
| $C_K$ 谱几何闭合定理 | $C_K$ Spectral Geometry Closure Theorem | $C_K$ 参数的谱几何无条件定理化，三维标度完全闭合 | 0.3.7 定理9.5 |
| 因果密度 Liouville 提升与熵单调性定理 | Causal Density Liouville Lift & Entropy Monotonicity Theorem | 因果场密度矩阵的 Liouville 提升保持熵单调递减 | 0.5.1 定理 |
| C-I 联合 H-定理 | C-I Joint H-Theorem | 因果场与信息场交互自由能的显式构造与联合 H-定理 | 0.5.2 定理 |
| 联合稳态 $\rho_{CI}^*$ 定理 | Joint Steady State $\rho_{CI}^*$ Theorem | C-I 耦合系统存在唯一联合稳态，含弱耦合求解（0.5.3）和非摄动平均场自洽求解（0.5.4） | 0.5.3, 0.5.4 |
| 一阶耦合遍历平均抵消定理 | First-Order Coupling Ergodic Averaging Cancellation Theorem | $\delta L_I^{(0)}$ 的 Fredholm 约束与结构抑制导致一阶耦合遍历平均抵消 | 0.5.5 定理 |
| 谱三元组-密度 Liouville 桥接定理 | Spectral Triple to Density Liouville Bridge Theorem | 谱三元组与因果场密度 Liouville 描述之间的严格桥接 | 0.5.6 定理 |
| C-I 双场耦合桥接定理 | C-I Dual Field Coupling Bridge Theorem | 因果场与信息场双场耦合的完整桥接与联合演化 | 0.5.7 定理 |
| 信息场统一动力学方程 | Information Field Unified Dynamics Equation | 信息场三层封闭体系的统一动力学方程 | 0.4.4 定理 |
| 信息场观测映射链 | Information Field Observation Mapping Chain | 从谱解码到物理预言的完整观测映射链 | 0.4.5 定理 |
| 联合截面谱定理 | Joint Cross-Section Spectrum Theorem | 三扇区联合截面谱的完整数学结构 | 0.3.9 定理 |
| 量子纠缠与 Tsirelson 界定理 | Quantum Entanglement & Tsirelson Bound Theorem | Tsirelson 界 $2\sqrt{2}$ 作为几何约束截面的直接推论 | 3号 §2 |
| 人体三界不可约定理 | Human Three-Realm Irreducibility Theorem | 人体物质界-中间界-信息界三界不可互相归约 | 21号 §1 |
| 因果场相位节点漂移定理 | Causal Field Phase Node Drift Theorem | 因果场相位节点在生物体表面曲率微扰下的漂移规律 | 41号 §1 |

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
| 几何因子 $C_{\text{geo}}$ | Geometric Factor $C_{\text{geo}}$ | 信息场与几何结构耦合的无量纲因子，由约束截面谱决定 | 0.4.6 §1 |
| $\hbar_{\text{eff}}$ | Effective $\hbar$ | 几何论中 $\hbar$ 作为导出值，含三路交叉验证（Wodzicki留数/ℰ映射/C_m） | 0.8.4 §2 |
| 退化时间 $\tau_{\text{dec}}$ | Decay Time | $\tau_{\text{dec}} \sim 7.28$ 日（中子衰变的几何特征时间） | 0.0.3 §5, 25号 |

---

## §6 粒子与扇区

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质扇区 | Matter Sector ($M$) | $\theta_M$ 主导，带电轻子质量层级 | 0.0.6 §3.3 |
| 因果扇区 | Causal Sector ($C$) | $\theta_C$ 主导，中微子质量与振荡 | 0.0.6 §3.3, 7 |
| 信息扇区 | Information Sector ($I$) | $\theta_I$ 主导，场动力学 | 0.0.6 §3.3, 0.4 |
| 夸克扇区 | Quark Sector | 夸克在约束乘积球面上的几何表示，含量子化方案（0.8.6）和 CKM 混合（8号） | 0.8.6, 8号 |
| 角度锁定 | Angle Locking | $\theta_M=30^\circ, \theta_C=30^\circ, \theta_I=30^\circ$（对称点，公理3的直接推论） | 0.0.6 §3.1 |
| 上饱和稳态 | Upper Saturation Steady State | $\theta_I \approx 72.53^\circ$（信息场演化终态） | 0.4.1 |
| 倒伏相 | Lodging Phase | 中微子质量谱的高端截断相，由因果场几何约束决定 | 7号 §3 |
| 三阶段相变 | Three-Stage Phase Transition | 信息场编码的物质界-中间界-信息界三阶段循环相变 | 31号 §1 |
| 物质界收缩时间 | Material Realm Contraction Time | 宇宙物质界的几何收缩时间尺度 | 46号 §1 |

---

## §7 角度与几何量

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质角 $\theta_M$ | Matter Angle | 公理3中物质扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 因果角 $\theta_C$ | Causal Angle | 公理3中因果扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 信息角 $\theta_I$ | Information Angle | 公理3中信息扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| eta 参数 | Eta Parameter | $\eta = 51.27^\circ$，当前演化状态 | 0.4.1 |
| 投影强度 2-形式 | Projection Intensity 2-Form | 扇区向全息屏投影的微分几何描述 | 0.0.6 §3 |

---

## §8 概念名称（非定理）

> 以下为概念名称，不加"定理"后缀。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 九素互扼 | Nine-Element Mutual Constraint | 公理—常数—工具层之间的超定锁定结构，涉及公理1–3、谱刚性定理、互锁常数唯一性定理、自举封闭定理的交叉约束。属超定锁定结构，非独立定理 | 0.0.7 §6.2 |
| 全息屏编码条件 | Holographic Encoding Condition | 公理3的简称：三分切丛 TM(a)=ℳ⊕𝒞⊕ℐ，存在二维全息屏 Σ，θ₁+θ₂+θ₃=90° | 0.0.6 §3 |
| CIM 相 | CIM Phase | 标准模型/广义相对论/弦论作为低能有效场论近似 | 0.2 §1 |
| 三对偶耦合 | Tri-Dual Coupling | 物质-因果-信息三扇区之间的对偶耦合结构 | 0.1.1 §2 |
| 信息场三层封闭体系 | Information Field Three-Layer Closed System | 信息场动力学的软模-硬模-饱和三层封闭描述 | 0.4.4 §1 |
| 三路交叉验证 | Three-Way Cross Validation | $\hbar_{\text{eff}}$ 的 Wodzicki 留数 / ℰ 映射 / $C_m$ 三路独立验证 | 0.8.4 §3 |
| 相位标记与集体锁定 | Phase Marking & Collective Locking | 信息场饱和稳态的相位标记机制与集体锁定现象 | 48号 §1 |
| 信息场编码 | Information Field Encoding | 信息场对物质界结构的编码机制 | 31号 §2 |
| 谱解码 | Spectral Decoding | 从谱三元组解码物理参数的观测映射 | 0.4.5 §1 |
| 几何梯度 | Geometric Gradient | 核子数梯度作为引力起源的几何表述 | 10号 §2 |
| 信息场硬模宇宙学残余背景 | Information Field Hard Mode Cosmological Residual Background | 暗能量的几何论替代——信息场硬模残余背景导致宇宙加速膨胀 | 20号 §2 |
| 分形层级 | Fractal Hierarchy | 宇宙从微观到宏观的分形层级几何结构 | 15号 §1 |
| 圆满 | Completion / Perfection | 信息场演化终态的哲学-几何概念 | 32号 §1 |
| 劫 | Kalpa | 宇宙循环周期的几何论诠释 | 45号 §1 |
| 中阴身 | Bardo / Intermediate State | 信息场与因果场的过渡态几何结构 | 44号 §1 |
| 时间熵 | Temporal Entropy | 时间方向的几何熵描述 | 47号 §1 |
| 时间纠缠 | Temporal Entanglement | 时间维度的几何纠缠结构 | 47号 §2 |
| 物质界-中间界-信息界 | Material-Intermediate-Information Realms | 宇宙三界的基本分类框架 | 31号, 21号 |
| 第八级不可计算自由度 | Eighth-Level Uncomputable Degrees of Freedom | 七层截断之外的不可预测自由度 | 49号 §1 |

---

## §9 构造性概念（诚实标注）

> 以下为构造性概念，非严格定理。在文章中使用时必须加「诚实标注」。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 桥接函数标准形（定义5.2） | Bridging Function Standard Form | 原称"桥接公理"，但非公理（几何论只有三条公理）。标准化为 $S=12(a^2/\ell_0^2+\ell_0^2/a^2)$，归一化条件为构造性假设 | 0.0.7 定义5.2, 5.2' |
| $\ell_0$ 的物理涌现 | Emergence of $\ell_0$ | $\ell_0$ 是谱几何单位锚点，与实验长度尺度的匹配属于条件性命题层 | 0.0.7 §7.3 |
| $\hbar$ 数值涌现 | Emergence of $\hbar$ | $\hbar$ 作为几何量的导出值，非基本常数 | 0.3.1 §5 |
| Hopf 假设（度量等价部分） | Hopf Hypothesis (Metric Equivalence) | 公理3的三分切丛结构中，Hopf纤维化的**度量等价** $r_{\mathcal{M}} = r_\Sigma$ 部分仍为假设（0.3.6 假设4.0）。拓扑部分已升级为定理（见 §4 Hopf纤维化定理（拓扑部分）） | 0.3.6 假设4.0, 0.3.8 §1 |
| M 场量子化框架 | M-Field Quantization Framework | M 场量子化的完整构造框架（0.8.0–0.8.6），含 Dirac 约束量子化、形变量子化等，属构造性方案 | 0.8.0–0.8.6 |
| Dirac 约束量子化方案 | Dirac Constraint Quantization Scheme | 未约化相空间中的约束代数与动量映射，属构造性方案 | 0.8.2 §1 |
| 形变量子化方案 | Deformation Quantization Scheme | M场量子谱与梯度流桥接的形变量子化构造 | 0.8.3 §1 |
| 核幻数几何框架 | Nuclear Magic Number Geometric Framework | 约束截面弯曲结构下核幻数的几何解释，属研究框架 | 0.2.3 §3 |
| 联合稳态非摄动求解 | Joint Steady State Non-Perturbative Solution | 时间尺度分离与平均场自洽的非摄动求解方案 | 0.5.4 §1 |

---

## §10 禁用词清单

> 以下词语在几何论文章中禁止使用，违者退回修改。

| 禁用词 | 原因 | 替代方案 |
|---|---|---|
| 第四公理 | 几何论只有三条公理 | 使用"构造性假设""定义"或"定理" |
| 桥接公理 | 桥接函数标准形是定义，非公理 | 使用"桥接函数标准形（定义5.2）" |
| 时空 | 几何论中空间是导出概念，非基本 | 使用"10方几何空间""几何空间""参数空间" |
| 量子场论 | 容易与标准模型混淆 | 使用"CIM 相"或"信息场动力学" |
| 规范场 | 几何论中联络结构不同 | 使用"投影强度 2-形式""联络形式"明确几何论语境 |
| 质量映射公理 | m=K sin³θ_M 是定理，非公理 | 使用"质量-角度耦合定理" |

---

## §11 维护规则

### §11.1 新增术语

1. 任何新文章引入新术语前，必须先在本表登记。
2. 登记时需提供：中文名、英文名、公式/陈述、出处（文章编号+章节）。
3. 术语不得与已有术语冲突。如必须冲突，需先在 §11.2 中解决。

### §11.2 术语冲突解决

1. 如新术语与已有术语矛盾，需在本节记录冲突及解决方案。
2. 解决方案可以是：废弃旧术语、重新定义新术语、或明确适用范围。
3. 冲突记录格式：`[日期] 冲突描述 → 解决方案`

**已有冲突记录**：

- `[260702]` **0.0.7 旧公理编号与术语表 §1 不兼容**：0.0.7（十方几何空间）使用旧编号——公理1=角度和、公理2=作用量和，而术语表 §1 标准公理体系为公理1=圆拓扑、公理2=边界极限、公理3=全息屏编码条件。→ 已在 §1 添加醒目标注；0.0.7 修订版将统一编号。阅读 0.0.7 时：旧「公理1」→ 标准「公理3 完备性约束」；旧「公理2」→ 标准「作用量定义」。

- `[260702]` **Hopf 纤维化定理/假设分裂**：此前 §4 和 §9 对同一概念给出矛盾的定理/非定理标签。→ 已拆分为：拓扑部分为定理（§4 Hopf纤维化定理（拓扑部分），0.3.6 定理4.3），度量等价 $r_{\mathcal{M}} = r_\Sigma$ 部分为假设（§9 Hopf假设（度量等价部分），0.3.6 假设4.0）。

- `[260702]` **$C_{\text{geo}}$ 三次重复**：此前 §2、§5、§7 各出现一次 $C_{\text{geo}}$ 条目，内容相同。→ 已合并至 §5（常数与参数）作为唯一条目，§2 和 §7 中删除。

### §11.3 定理标签使用

1. "定理"标签只能用于从公理严格推导出的命题。
2. "定义"标签用于构造性概念。
3. "命题"标签用于有待严格化但方向明确的结论。
4. 所有文章必须遵守标签使用规则。

### §11.4 禁用词执法

1. §10 列出的禁用词在任何新文章中不得出现。
2. 旧文章中出现禁用词的，应在修订时逐步替换。
3. 如确需使用禁用词（如引用外部文献），需加引号并注明语境。

### §11.5 版本号

版本号格式：`YYMMDD.N`（年份后两位 + 月份 + 日期 + 当日修订序号）。每次修改必须递增修订序号。

### §11.6 文章写作原则

1. 未知即说未知——不要编造。
2. 公理、定理、定义、命题、猜测严格区分。
3. 数值必须标注来源。
4. 超出几何论框架的结论必须诚实标注。
5. 唯一外部物理锚点：真空光速 $c$（详见 §3 ℰ 映射锚点）。
