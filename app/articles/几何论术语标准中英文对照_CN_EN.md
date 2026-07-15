# 几何论术语标准中英文对照

> **版本**：260715.1  
> **用途**：几何论全部术语在此统一。任何新文章引入术语前必须先在本表登记。  
> **语言**：中文 / English  
> **更新规则**：见 §11 维护规则  
> **本次更新**：§4 定理——新增19条GT-Vault定理（几何速度代数、谱互锁、硬方向冻结、约束梯度流、M-C腰边耦合、M-I完备性耦合、谱互锁闭包、约束释放效应、多体截面、规范群几何根源、耦合常数Hessian谱统一、内禀膨胀率、差异量级函数、七级递推膨胀、几何CP破坏、质子衰变寿命、中微子Majorana本质、电荷量子化几何条件、拓扑超导材料筛选）；§5 常数——新增7条GT-Vault参数；§8 概念名称——新增8条GT-Vault概念（观测链、时间尺度硬化、稳态因果环流、ℰ映射函子、跨级渗透、几何引力起源、第八级不可控、谱互锁闭包闭包）；§9 构造性——新增3条构造性概念（量子化谱刚性适用、倒伏相截断闭包、spinfoam构造）；§11.2 新增GT-Vault术语冲突记录

---

## §1 公理体系

> 公理 = 理论的全部自由输入。几何论有且仅有**三条公理**，源于 0.0.3–0.0.7 并在 0.1（260710.3）中统一陈述。
> 
> **重要**：0.0.0《零与谱》为纯数学推演，提供 $S_3$ 谱权重 $6:2:1$，不作公理或定理界定。其"本体前提"、"结构公理"、"编码公理"命名是《零与谱》内部的术语，不改变几何论核心只有三条公理的事实。本体前提+结构公理+编码公理 ⇔ 公理1+公理2+公理3 是等价表述，但几何论核心标准命名以 0.1 为准。
>

### 0.0.0《零与谱》出发点

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 零维源点 S₃ 对称性（出发点） | Zero-Dimensional Source Point S₃ Symmetry (Starting Point) | 零维源点 $\mathcal Z$ 携带对称群 $S_3$。$S_3$ 的正规子群链 $\{e\}\subset A_3\subset S_3$ 提供最简三层层级，阶数为 $1:3:6$ | 0.0.0 §1 |
| 谱权重 6:2:1 | Spectral Weight 6:2:1 | $w_{\{e\}}:w_{A_3}:w_{S_3}=6:2:1$，由 $S_3$ 各层齐性空间 $S_3/H$ 的维数（即指数 $[S_3:H]$）给出 | 0.0.0 §4 |

### 0.0.3–0.0.7 公理体系

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 公理1（圆拓扑） | Axiom 1 (Circle Topology) | $D = S^1 \setminus \{p_0, p_*\}$，激发态参数空间由圆去掉真空点 $p_0$ 与退化点 $p_*$ 得到，含两个开区间分支 $D_\pm$。**独立于 0.0.0 的本体前提与结构公理** | 0.0.3 §2.1 |
| 公理2（边界极限） | Axiom 2 (Boundary Limit) | $S: D \to (0,+\infty)$ 在每个分支 $D_\pm$ 上连续，$\lim_{x\to p_0}S(x)=0$（真空极限），$\lim_{x\to p_*}S(x)=+\infty$（退化极限）。**独立于 0.0.0 的本体前提与结构公理** | 0.0.3 §2.2 |
| 公理3（全息屏编码条件） | Axiom 3 (Holographic Screen Encoding Condition) | 在三分切丛 $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ 的每个 $\mathbb{R}^9$ 纤维中，存在二维全息屏 $\Sigma$，三个扇区投影强度角 $\theta_1,\theta_2,\theta_3\in(0^\circ,90^\circ)$ 满足 $\theta_1+\theta_2+\theta_3=90^\circ$。**与 0.0.0 编码公理 5.1 等价** | 0.0.6 §3.1 |

---

## §2 场与空间

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 零维源点 | Zero-Dimensional Source Point $\mathcal Z$ | 没有广延的几何对象：不携带度量，不定义切空间，不预设内部方向。唯一不可约减的性质是「存在」。$S_3$ 是最小非交换对称群的必然载体 | 0.0.0 §1 |
| 谱展开 | Spectral Unfolding | 零维源点 $\mathcal Z$ 携带 $S_3$ 对称性，通过尺度参数 $a>0$ 的引入展开为可分辨的 Laplace–Beltrami 型几何谱 $\{\lambda_k(a)\}$。$a\to0^+$ 时谱退化回零态；$a>0$ 时谱进入有限可分辨结构。旧称「谱震动」，已废弃 | 0.0.0 §2 |
| 正规子群链 | Normal Subgroup Chain | $S_3$ 的非平凡正规子群链 $\{e\}\subset A_3\subset S_3$，阶数为 $1:3:6$，提供最简三层层级结构（平凡层、循环层、全对称层），是约束乘积球面三层因子的群论源头 | 0.0.0 §2.2 |
| 谱权重 | Spectral Weight | $6:2:1$，由 $S_3$ 各层齐性空间 $S_3/H$ 的维数（即指数 $[S_3:H]$）给出，分别对应平凡层（$\{e\}$，维数 6）、循环层（$A_3$，维数 2）、全对称层（$S_3$，维数 1） | 0.0.0 §4 |
| 整体尺度因子 | Global Scale Factor $a$ | $a>0$，零维源点向可观几何展开的单一连续尺度参数。度量几何结构相对于零态的展开程度。$a\to0^+$ 时结构收缩回零维源点 | 0.0.0 §2.1 |
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
| M-C腰边耦合 | M-C Waist-Edge Coupling | 物质场与因果场在约束截面边缘的耦合结构，对应电磁相互作用 | 0.6.3 §1 |
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
| 物质界流 | Material Realm Flow | 约束截面Σ上的切向量场，流体力学在几何论中的连续介质延拓 | 30号 §2.2 |
| 全息屏双极结构 | Holographic Screen Bipolar Structure | 全息屏在边界极限公理基态的第一激发态必为双极构型，地月系统为其天体物理实现 | 37号 §2 |
| 信息场共振条纹 | Information Field Resonance Fringes | 因果场相位节点在信息场中激发的共振条纹，对应经络线 | 40号 §2.4 |
| 几何Navier-Stokes映射 | Geometric Navier-Stokes Mapping | 将物质界流映射至Navier-Stokes方程的几何构造 | 30号 §2.3 |
| 边界层（几何定义） | Boundary Layer (Geometric) | 信息场退相干深度在约束截面边界处的几何定义，厚度 $\delta_{BL} \approx 8.6$ mm | 30号 §4.1 |
| I场空间扩散时间 | I-Field Spatial Diffusion Time | $\tau_I^{\text{spatial}} = N_{\text{info}} \cdot \Delta\tau_{\text{step}}$，当前 $\sim 3\times10^{17}$ 年（完全冻结），$N_1=6000$ 时仅 $\sim 1$ 周 | 50号 §3 |
| I场扩散冻结 | I-Field Diffusion Freezing | I场空间扩散随 $N_{\text{info}}$ 增长而线性减速，在 $N_{\text{info}} \sim 10^6\text{--}10^7$ 时扩散时间超过宇宙年龄——空间非均匀性被冻入 | 50号 §4 |
| 冻结临界点 | Freezing Critical Point | $N_{\text{info}}^{\text{freeze}} \approx 1.1\times10^9$，$t_{\text{freeze}} \approx 1700$ 年，I场扩散冻结完成，原初扰动谱由此确定 | 50号 §8 |
| 编码时间 | Encoding Time | $\Delta t_{k\to k+1} = N_k \cdot \Delta\tau_{\text{step}}$，七级递推每级的物理时间由编码步长 $\Delta\tau_{\text{step}} \sim 10^2$ s 和当前顶点数 $N_k$ 确定 | 50号 §5.6 |
| I场编码密度 | I-Field Encoding Density | $\rho_{\text{info}} = N_{\text{info}} / V_{\text{holo}}$，决定有效温度 $kT_{\text{eff}} = \sqrt{\rho_{\text{info}}} \cdot E_{\text{Planck}}$ | 52号 §2 |
| C扇区共凝结 | C-Sector Co-condensation | 核子在C扇区的联合锁定构型，锁定曲率 $\kappa_{\text{lock}}$ 决定核结合能 | 52号 §3 |
| 几何引力增强 | Geometric Gravity Enhancement | $G_{\text{eff}} = G_{9D}\sqrt{1+a_0/a_N}$，在低加速度环境下引力被I场硬模相干泄漏增强 | 54号 §5 |

---

## §3 后验命名对照

> 几何论本身输出纯几何量（$S_e$, $K$, $\theta_M$, $\theta_C$, $\theta_I$ 等）。将这些几何量识别为"物理常数"（如精细结构常数、电子质量）是后验匹配——实验侧发现几何论的输出数值与测量值一致，从而建立对应关系。本表记录这些后验识别关系。
>
> **命名约定不参与理论推导**，可替换而不影响数学内容。详见 0.1 §附录A。

| 几何量 | 物理名称 | 后验匹配理由 | 出处 |
|---|---|---|---|
| $S_e = 137.035999084$ | 精细结构常数倒数 $\alpha^{-1}$ | 数值与 CODATA $\alpha^{-1}=137.035999084(21)$ 一致 | 0.1 §4.1 |
| $K \sin^3\theta_M = 510.99895$ keV | 电子质量 $m_e c^2$ | 数值与 CODATA $m_e c^2=510.99895000(15)$ keV 一致 | 0.1 §4.2 |
| $\chi_L = 1.5092231080\times10^{-10}$ m | （几何长度单位） | 量纲桥输出，与 Bohr 半径 $a_B=5.29177211\times10^{-11}$ m 相差因子 $\pi/\sqrt{3}$ | 0.1 §4.4 |
| $\chi_T = 3.6161912064\times10^{-17}$ s | （几何时间单位） | 量纲桥输出，$\chi_T = \chi_L / c$ | 0.1 §4.4 |
| $\hbar$（量纲桥导出） | 约化普朗克常数 | $6.58211957\times10^{-16}$ eV·s，与 CODATA 一致 | 0.1 §4.4 |
| $\mathcal{C}$-零维传播模 | 光子 $\gamma$ | $m_\gamma = K\sin^30^\circ = 0$ 对应光子零质量 | 0.1 §4.3 |
| $\mathcal{M}$-软模基态 | 电子 $e^-$ | 见 $m_e$ 条目 | 0.1 附录A |

### 3.1 历史说明

旧版本（260707.7 及更早）将本表内容命名为"核心映射 ℰ"并赋予锚定功能（公设1.1）。63号文章（观测者自举）通过八步自举闭环内部化了锚定功能——角度数值由谱刚性锁定，$K$ 由谱单位选择定理输出，$m_e$ 由谱互锁定理独立导出，不再需要外部输入。

因此：**ℰ 映射不再作为理论内部结构存在**。本表仅记录后验匹配关系。

### 3.2 旧术语迁移

| 旧术语（260707.7） | 新术语（260710） | 状态 |
|---|---|---|
| ℰ 映射（量纲桥） | 量纲桥（独立构造） | 已更名 |
| ℰ 映射锚点 | 后验匹配对照 | 已废弃 |
| $\hbar_{\text{eff}}$ 桥接 | $\hbar$ 量纲桥导出值 | 已更名 |

---

## §4 定理

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| 三分切丛定理 | Tripartite Tangent Bundle Theorem | $TM(a)=\mathcal M\oplus\mathcal C\oplus\mathcal I$，三个 $S^3$ 因子切丛的拉回，每个纤维同构于 $\mathbb R^3$。三扇区在数学地位上完全等价，$S_3$ 置换诱导切丛分解的自同构 | 0.0.6 §2 |
| 球面维度锁定定理 | Sphere Dimension Locking Theorem | 在二维全息屏编码原则下，要求投影角具有 Hopf 型来源并优先保留简洁群结构，则球面维度 $D=3$ 是唯一兼容解（$D=1$ 缺乏连续二维编码能力，$D=7$ 及更高候选基空间维度与结构复杂度超出最简编码原则） | 0.3.6 §1.2 |
| 值域定理与严格凸性 | Range Theorem & Strict Convexity | 六项代价函数 $S$ 在约束定义域 $D_\theta=\{(\theta_1,\theta_2,\theta_3)\mid\theta_i>0,\;\theta_1+\theta_2+\theta_3=90^\circ\}$ 上严格凸，值域为 $[24,+\infty)$，唯一全局严格最小值点为 $\theta_1=\theta_2=\theta_3=30^\circ$，$S_{\min}=24$ | 0.0.6 §4.4 |
| 模空间一维性引理 | Moduli Space One-Dimensionality Lemma | 约束乘积球面 $M(a)$ 的连续模空间由单一尺度参数 $a\in(0,\infty)$ 参数化，同胚于 $(0,\infty)$ | 0.0.5 §3.2 |
| 谱刚性定理 | Spectral Rigidity Theorem | 约束乘积球面上 Laplace 谱唯一确定尺度因子 $a$ | 0.0.5 定理4.1 |
| 桥接函数标准形 | Bridging Function Standard Form | → 见 §9 构造性概念。归一化条件为构造性假设，非公理亦非独立定理 | — |
| 值域协调定理 | Range Compatibility Theorem | 六项作用量值域与抽象几何量值域严格相容 | 0.0.7 定理4.1 |
| 互锁常数唯一性定理 | Interlocking Constants Uniqueness Theorem | $(\Lambda, k_0, \ell_0) = (3, 2, V_{\text{unit}}^{-1/9})$ 唯一确定 | 0.0.7 定理7.1–7.2 |
| 自举封闭定理 | Bootstrap Closure Theorem | 10方几何空间所有数学结构构成封闭链条 | 0.0.7 定理7.3 |
| 信息场热方程 | Information Field Heat Equation | $\partial_t \mathcal{I} = \chi_T \Delta \mathcal{I}$ | 0.4 定理2.1 |
| 信息场衰减定理 | Information Field Attenuation Theorem | 信息场随 $\theta_I$ 增大而单调衰减，终态为 §6 上饱和稳态 $\theta_I \sim 72.53^\circ$ | 0.4.1 |
| 三分切丛置换群刚性定理 | Tripartite Bundle Permutation Group Rigidity Theorem | $S_3$ 是置换群的唯一选择 | 0.0.7 定理2.0' |
| 质量-角度耦合定理 | Mass-Angle Coupling Theorem | $m = K \sin^3\theta_M$（由公理1–3及约束乘积球面构造导出，非公理） | 0.1 §2.2.2, 0.0.3 §5 |
| 光子零质量定理 | Photon Zero Mass Theorem | $m_\gamma = K \sin^3(0^\circ) = 0$，光子零质量是质量映射定理在 $\theta_M=0^\circ$ 的直接推论 | 0.6.8 §2 |
| 边界分离定理 | Boundary Separation Theorem | 完备性平面 $\mathcal{P}$ 的M扇区边界 $\partial\mathcal{P}_M$ 将构型空间划分为两个互不相交的几何类——正则模式（$\theta_M>0$, $S<\infty$, $S=S_e$ 约束适用）与边界模式（$\theta_M=0$, $S=\infty$, $S=S_e$ 约束不适用）。光子属于边界模式 | 0.6.3 §4.5 |
| 光子自旋-1选择定则 | Photon Spin-1 Selection Rule | 光子自旋-1由双路径锁定：主路径——定理2的TT条件导出守恒矢量流 $J_\nu=\nabla^\mu h_{\mu\nu}^{(0)}=0$，$h_{\mu\nu}^{(0)}$ 可由矢量场 $A_\mu$ 表示，自旋-0被无迹条件代数排除，自旋-2归属因果场（非M-C耦合产物）；辅路径——M-C腰边退化极限 $\theta_M,\theta_C\to 0$ 下SO(2)剩余对称性 $\to$ U(1)表示论 $\to$ 螺旋度 $n=\pm 1$。辅路径排除法含构造性加固 | 0.6.8 §7 |
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
| 五节点定理 | Five-Node Theorem | 五输穴对应因果场相角离散节点 $(0, \pi/2, \pi, 3\pi/2, 2\pi)$，由三分切丛 $S^1$ 紧致化严格导出 | 40号 §2.3 |
| 三阴三阳维度定理 | Three Yin Three Yang Dimension Theorem | 六经分类由 $S^2 \times S^1$ 全息屏的三对极分解给出 $2^3 - 2 = 6$，十二正经由 $\mathbb{Z}_2 \times \text{手性}$ 给出 | 40号 §3 |
| 特征加速度定理 | Characteristic Acceleration Theorem | $a_0 = G_{9D} \cdot S_e \cdot (\lambda_2^{\text{eff}})^{3/2} / (\chi^2 \cdot \Phi_0)$，信息场硬模三维相干泄漏唯一确定星系尺度特征加速度 | 19号 定理2.1 |
| Tully-Fisher 严格形式定理 | Tully-Fisher Rigorous Form Theorem | $v_f^4 = G_{9D} \cdot a_0 \cdot N$，旋转曲线渐近平坦速度与核子数的四次方关系，由几何论严格导出 | 19号 定理4.1 |
| 黑洞辐射七级离散谱线定理 | Black Hole Radiation Seven-Level Discrete Spectrum Theorem | 黑洞辐射具有七条离散谱线，跃迁能量 $\Delta E_n = k \cdot \Delta S_n$，$\Delta S_n$ 为0.1正向递推的七级精确差分值 | 16号 §2 |
| 全息屏双极定理 | Holographic Screen Bipolar Theorem | 全息屏在边界极限公理基态的第一激发态必为双极构型 | 37号 §2.2 |
| 特征值简并定理（潮汐锁定） | Eigenvalue Degeneracy Theorem (Tidal Locking) | 潮汐锁定由 Laplace-Beltrami 特征值简并严格解释，非摩擦耗散的偶然结果 | 37号 §3.2 |
| 全息屏激发态多极定理 | Holographic Screen Excited State Multipole Theorem | 双极定理向多极系统的谱刚性推广，木卫/土卫系统纳入 | 37号 §6.1 |
| $v_F$ 严格公式（定理级） | $v_F$ Rigorous Formula (Theorem-grade) | $v_F = c \cdot (\lambda_1^{\mathrm{eff}})^{3/2} / (S_e^2 \cdot \sqrt{\lambda_2^{\mathrm{eff}}})$，仅含0.X.X本征量 | 13号 第9章 |
| 创世-退相干对偶 | Cosmogony-Decoherence Duality | 创世（信息从 $I^3$ 向 $M^3$ 单方向凝结）与退相干（信息从 $M^3$ 向 $I^3$ 耗散）构成严格对偶 | 33号 §9 |
| 两体几何约化质量定理 | Two-Body Geometric Reduced Mass Theorem | $\mu_{\text{geo}} = m_1 m_2/(m_1 + m_2)$，由联合截面 Hessian 的 Schur 补分块结构严格导出 | 1号 §5.1 |
| SO(3)二重覆盖与旋量表示定理 | SO(3) Double Cover & Spinor Representation Theorem | 电子自旋 1/2 源于 $\pi_1(\mathrm{SO}(3)) = \mathbb{Z}_2$ 的拓扑必然，由 $\mathrm{Spin}(8)$ triality 锁定最低维 Clifford 模 | 1号 §2.1 |
| η-物质空间径向对应定理 | η-Material Radial Correspondence Theorem | $\eta$ 作为物质空间径向坐标，由完备性公理及切丛三分解 $T\Sigma = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$ 严格确定 | 1号 §3.1 |
| 面积元投影定理 | Area Element Projection Theorem | $\theta_M \to 0$ 极限下有效信息场面积元投影的唯一确定形式 | 1号 §4.3 |
| 超精细耦合定理 | Hyperfine Coupling Theorem | $\Delta E_{\text{hfs}} = \frac{4}{\pi} \cdot k \cdot \frac{\sin\theta_I^e \cdot \sin\theta_I^p \cdot \sin\theta_C^p}{S_e \cdot S_p}$ | 1号 §4.4–§4.5 |
| 裸弱混合角定理 | Bare Weak Mixing Angle Theorem | $\sin^2\theta_W^{\text{bare}} = \frac{\sin\theta_I}{\sin\theta_C \cdot (1 + \sin^2\theta_I)} = 0.23109$，由凝聚相投影-耦合对应导出 | 6号 §3.2 |
| Berry相位反馈修正定理 | Berry Phase Feedback Correction Theorem | 三场联合闭合路径 Berry 相位对裸弱混合角的反馈修正，$\sin^2\theta_W^{\text{phys}} = 0.23124$（偏差 $2\times10^{-5}$，与 PDG $0.23122\pm0.00003$ 一致） | 6号 §3.3 |
| 黑洞几何约束构型定理 | Black Hole Geometric Constraint Configuration Theorem | 信息场冻结极限 $\theta_I \to 0^+$ 下，$\theta_M = \theta_C = 45^\circ$ 是总作用量的严格极小值点 | 14号 §1.2 |
| 多体作用量可加性定理 | Multi-Body Action Additivity Theorem | 黑洞总作用量 $S_{\text{joint}} = N \cdot S_p$，各重子贡献独立可加 | 14号 §4.1 |
| 视界半径几何定理 | Horizon Radius Geometric Theorem | $R_{\text{BH}} = \sqrt{S_{\text{BH}}/\pi} \cdot \chi_L$，视界半径由作用量几何直接确定 | 14号 §3.2 |
| 信息守恒定理 | Information Conservation Theorem | 黑洞信息守恒——全息屏编码面积 $A_{\text{BH}}^{\text{phys}} \neq 4\pi R_{\text{BH}}^2$，信息以层级压缩形式存储于全息屏 | 14号 §5.2 |
| 电子冻结定理 | Electron Freezing Theorem | 电子在构型A是谱互锁定理的唯一不动点，$\Delta\theta_\alpha^{(1)} = 0$ 对所有 $\alpha$ | 24号 §4.1 |
| 因果角锁定定理 | Causal Angle Locking Theorem | 电子-缪子 $\theta_C$-共享联合截面上，驻点条件强制 $\theta_C^{(2)} = \theta_C^0 = 26.16^\circ$ | 24号 §4.3 |
| $\theta_M^{(2)}$ 对称性解析论证 | $\theta_M^{(2)}$ Symmetry Analytic Proof | $\theta_M^{(2)} = (90^\circ - \theta_C^0)/2 = 31.92^\circ$（无耦合极限），含 $W_{12}$ 耦合修正后 $\approx 31.94^\circ$，由 $S$ 函数全排列对称性严格导出 | 24号 §4.4 |
| $C_n$ 独立于驻点条件定理 | $C_n$ Independence from Stationarity Theorem | 质量标度 $C_n$ 不进入联合截面驻点条件，由全息屏层级嵌套独立确定 | 24号 §5.1 |
| 三代起源定理 | Three-Generation Origin Theorem | $N_{\text{gen}} = 3$ 是截面类型的代数和穷举结果：三扇区 $\to$ 三种截面类型（$\theta_C$-共享、M-同步、$\theta_I$-共享），其中 $\theta_I$-共享物理不可行 + 裸截面为第一代 $\to$ 恰好三代。推论 6.3b：$N_{\text{gen}} = 3 - 1 + 1 = 3$ | 0.6.7 §6.4 |
| I场扩散冻结定理 | I-Field Diffusion Freezing Theorem | $\tau_I^{\text{spatial}} = N_{\text{info}} \cdot \Delta\tau_{\text{step}}$，$N_1$ 时 $\sim 1$ 周 $\to$ 早期宇宙天生均匀，视界问题自动消解 | 50号 §3 |
| $N_{\text{info}}(t)$ 函数定理 | $N_{\text{info}}(t)$ Function Theorem | 七级递推在 $t_7 \approx 850$ 年内完成，此后 $N_{\text{info}}(t>t_7) = N_7(t/t_7)^2$（$\beta=2$ 精炼幂律） | 50号 §5.6 |
| 原初扰动谱定理 | Primordial Perturbation Spectrum Theorem | $A_s = 1/N_{\text{info}}^{\text{freeze}} \approx 9.1\times10^{-10}$（零参数，与 Planck $2.10\times10^{-9}$ 差因子 2.3），$n_s \approx 0.97$，$r \ll 0.01$ | 50号 §8 |
| 重子数几何定理 | Baryon Number Geometric Theorem | $B = \frac{1}{3} w_{\theta_C}$，$\theta_C$ 截面拓扑缠绕数 $w$ 决定重子数：夸克 $B=1/3$（$w=1$），轻子 $B=0$，重子 $B=1$（$w=3$） | 51号 §3 |
| Sakharov三条件几何翻译定理 | Sakharov Three Conditions Geometric Translation Theorem | B破坏 = 约束流形在 $\text{N}_2\to\text{N}_3$ 相变边界的拓扑扇区瞬时连通；C/CP破坏 = $\theta_C$ 截面旋转复相位 $\delta_{\text{CP}}\approx 1.20$ rad（8号）；热非平衡 = 递推乘子跳变 $\varepsilon=5.56$（50号） | 51号 §2–§6 |
| 氘瓶颈定理 | Deuterium Bottleneck Theorem | 氘核 C扇区共凝结门槛 $\kappa_{\text{deuteron}} \approx 0.056$ MeV，当 $kT_{\text{eff}}$ 低于此值时空背景波动不足以撕开C扇区锁定 | 52号 §4 |
| ⁴He丰度几何定理 | ⁴He Abundance Geometric Theorem | $Y_p^{\text{geo}} \approx 0.25$，零参数，与观测 $0.245\pm0.003$ 一致——核子数 2:2 几何对称性的直接输出 | 52号 §5 |
| 中微子绝对质量标度定理 | Neutrino Absolute Mass Scale Theorem | $m_1 \approx 0.0286$ eV, $m_2 \approx 0.0297$ eV, $m_3 \approx 0.0581$ eV，$\Sigma m_\nu \approx 0.118\text{--}0.122$ eV。二重态分裂源于倒伏相截断角 $\theta_M^{\text{cutoff}} \approx 5.74^\circ$ 的有限性 | 53号 §4–§5 |
| 统一几何定理（暗物质替代） | Unified Geometric Theorem (Dark Matter Replacement) | I³多尺度相干泄漏解释暗物质四条独立支柱：星系旋转曲线（$a^2=a_N^2+a_N a_0$）、子弹星系团（I场渗透峰冻结）、CMB第三峰（$a_0/a_N^{\text{pert}} \approx 14$ $\to$ 增强 3.83 倍）、大尺度结构（$G_{\text{eff}}$ 增长 $\alpha\approx 1.44$ $\to$ $\sigma_8\approx 0.75$） | 54号 §6 |
| 混合角层级定理 | Mixing Angle Hierarchy Theorem | $\theta_{13} \ll \theta_{12} \lesssim \theta_{23}$ 由 Hessian 谱和 M-C 交换的定性结构唯一确定，不依赖数值拟合 | 55号 §10 |
| 无磁单极子结论 | No Magnetic Monopole Conclusion | 约束流形 $S$ 为 2-单纯形 $\to$ 可缩 $\to$ $\pi_2(S)=0$ $\to$ $H^2(S;\mathbb{Z})=0$ $\to$ 所有 U(1) 丛平凡 $\to$ $\nabla\cdot\mathbf{B}=0$ 处处成立。狄拉克量子化条件 $eg=n/2$ 反转：不是磁荷存在则电荷量子化，而是 $\theta_C$ 纤维化单值性要求电荷量子化 | 56号 §3–§5 |
| 电弱 crossover 定理 | Electroweak Crossover Theorem | 电弱"相变"不存在——只有平滑 crossover。质量来自软模曲率恢复力，非真空期望值 $\to$ 无可破缺的对称性；$\theta_M$ 随 $N_{\text{info}}$ 平滑演化 | 4号 §5.3 |
| 强 CP 拓扑冻结定理 | Strong CP Topological Freezing Theorem | $\bar{\theta}=0$ 是结构强制的：U(1)_A 手征转动 = ℐ 扇区全局 $\theta_I$ 平移，$\tilde{S}_{\text{total}}$ 在 U(1) 作用下单调（P0/CG-1），公理 1 真空标记 $\to$ U(1) 完全冻结 $\to$ $\bar{\theta}=0$。零参数，轴子不存在 | 5号 §5.5 |
| 三代起源拓扑定理 | Three-Generation Origin Topological Theorem | $N_{\text{gen}} = \dim(\Delta^2) + 1 = 3$。$S_3$ 迷向子群穷举：$\{e\}$（电子，三角全不等）、$S_2^{IM}$（缪子）、$S_2^{CI}$（τ子）、$S_2^{MC}$（梯度流不可达）、$S_3/A_3$（重心，非粒子构型）。第四代无处可去——所有五种 $S_3$ 子群类型已穷举完毕 | 57号 §4 |
| 自由色荷拓扑禁止定理 | Free Color Charge Topological Forbiddance Theorem | 自由色荷对应约束流形顶点 $(90^\circ,0,0)$，$1/\sin^2 0^\circ \to \infty$ $\to$ $S \to \infty$ $\to$ $E \to \infty$。禁闭是拓扑的（顶点奇点），不是动力学的（不需要 $\alpha_s$ 跑动） | 58号 §3 |
| MW 色约化定理 | MW Color Reduction Theorem | Marsden-Weinstein 约化：$N=1$ $\to$ 0D 相空间（无动力学），$N=2$ $\to$ 1D（离散束缚态），$N=3$ $\to$ 2D（可传播）。色单态是唯一可传播构型 | 58号 §4–§6 |
| 引力统一定理 | Gravity Unification Theorem | 引力的三个几何表达——因果场动力学 $\Lambda_\xi$（0.5）、裸引力耦合 $G_{9D}$（10号）、宏观有效引力 $G_{\text{eff}}$（54号）——是约束流形 $\Delta^2$ 上同一 Hessian 谱 $(\lambda_1,\lambda_2)$ 的三个投影。转换不需要任何额外假设 | 59号 §6 |
| $\theta_M$ 冻结定理 | $\theta_M$ Freezing Theorem | $\theta_M^e = 57.93^\circ$（$S_3$ 完全破缺），$\theta_M^\mu = \theta_M^\tau = 31.94^\circ$（$S_2$ 对称性恢复）。$S_2^{IM}$ 和 $S_2^{CI}$ 线共享同一 $\theta_M$ 值——约束梯度流 + $S_3$ 迷向子群的联合几何必然。9号工作假设「三代共享 $\theta_M$」由本定理替代 | 60号 §4–§5 |
| Berry 相位路径定理（缪子） | Berry Phase Path Theorem (Muon) | $H_{tn}^\mu = -405 \neq 0$ $\to$ 缪子不完全在 $S_2^{IM}$ 线上（$\Delta\theta = 0.04^\circ$）$\to$ 约束梯度流与 $S_2$ 对称性竞争导致交叉 Hessian 非零。$a_\mu^{\text{B}} = 1.17(6) \times 10^{-3}$（命题，10% 误差） | 62号 §3–§6 |
| 几何速度代数定理 | Geometric Velocity Algebra Theorem | 光速 $c$ 的几何导出框架——三分切丛 M-C 腰边耦合结构的几何速度解释，$c$ 由量纲桥内生确定 | 2.6 §核心 |
| 谱互锁定理（电子质量锁定） | Spectral Interlock Theorem (Electron Mass Locking) | 电子质量 $m_e=510.99895$ keV 由谱几何机制独立锁定——Hessian 谱本征值的谱互锁结构直接输出电子质量值，非外部输入 | 2.5 §核心 |
| 硬方向冻结定理 | Hard Direction Freezing Theorem | 法方向 $\theta_M$ 的 $dS/dt\to 0$ 锁定——约束梯度流在 $\theta_M$ 方向的刚性冻结，$\theta_M$ 在演化中率先达到稳态 | 3B.4 §核心 |
| 约束梯度流定理 | Constrained Gradient Flow Theorem | 质量生成的梯度下降机制——约束截面上 Hessian 梯度流的演化方程，$d\theta_\alpha/dt = -\partial S/\partial\theta_\alpha$ | 3C.2 §核心 |
| M-C 腰边耦合定理 | M-C Waist-Edge Coupling Theorem | 腰边$\leftrightarrow$底边曲率耦合的几何描述——电磁相互作用的几何论根源，$W_{MC} = \sqrt{2}/\sin\theta_C$ | 3C.3 §核心 |
| M-I 完备性耦合定理 | M-I Completeness Coupling Theorem | 物质-信息完备性耦合方程——M 场与 I 场的完整耦合框架，$W_{MI} = \sqrt{2}/\sin\theta_I$ | 3C.4 §核心 |
| 谱互锁闭包定理 | Spectral Interlock Closure Theorem | 三场谱互锁的闭包证明——所有谱互锁关系形成闭合拓扑结构，不依赖任何外部参数输入 | 4.2 §核心 |
| 约束释放效应定理 | Constraint Release Effect Theorem | $N\geq 2$ 时渗透约束松弛的涌现行为——多粒子系统约束随粒子数增加自动松弛，$\theta$ 构型自由度释放 | 4.3 §核心 |
| 多体截面定理 | Many-body Section Theorem | 多粒子系统的约束截面推广——$N$ 体联合截面的数学构造，兼容单粒子到凝聚体的统一约束描述 | 4.5 §核心 |
| 规范群几何根源定理 | Geometric Origin of Gauge Groups Theorem | 三分切丛七子结构$\to$SU(3)$\times$SU(2)$\times$U(1)的严格映射——规范群三分支的几何起源于切丛子结构组合数学 | 5.1 §核心 |
| 耦合常数 Hessian 谱统一 | Hessian Spectral Unification of Coupling Constants | 三种耦合常数（电磁、弱、强）的统一几何根源——同一 Hessian 谱在不同扇区投影给出精细结构常数、弱耦合常数、强耦合常数 | 5.6 §核心 |
| 内禀膨胀率定理 | Intrinsic Expansion Rate Theorem | $\mathcal{H}_\eta = -0.09491$，几何膨胀的内在驱动——由 Hessian 谱刚性唯一确定，非自由参数，替代暗能量 | GT-6.4.1 |
| 差异量级函数定理 | Discrepancy Magnitude Function Theorem | $f = \sqrt{\mathcal{I}(\tau_{\text{cmb}})} \approx 0.918$，哈勃常数差异的几何根源——信息场编码密度的径向梯度效应 | GT-6.4.2 |
| 七级递推膨胀定理 | Seven-level Recursive Expansion Theorem | 乘子序列 $(6, 33.3, 10, 10, 1.125, 2)$ 三阶段驱动的几何膨胀——替代暴脹子势能的零参数膨胀机制 | GT-6.6.3 |
| 几何 CP 破坏定理 | Geometric CP Violation Theorem | $\delta_{\text{CP}} \approx 1.20$ rad，$\theta_C$ 截面旋转复相位的几何起源——CKM 不可约相位由截面挠率唯一确定 | GT-6.7.4 |
| 质子衰变寿命定理 | Proton Decay Lifetime Theorem | $\tau_p \approx 7.2 \times 10^{34}$ 年——B 破坏拓扑机制的直接输出，今日 B 破坏率 $\sim 10^{-110}$ s$^{-1}$（宇宙寿命内概率 $\sim 10^{-92}$） | GT-8.3.4 |
| 中微子 Majorana 本质定理 | Neutrino Majorana Nature Theorem | 倒伏相自由度计数 $\to 2$ 自由度 $\to$ 中微子为 Majorana 粒子——非 Dirac 粒子的几何必然 | GT-8.4.8 |
| 电荷量子化几何条件定理 | Geometric Charge Quantization Theorem | $\theta_C$ 纤维化单值性 $\to e$ 离散化——狄拉克条件 $eg=n/2$ 反转：不是磁荷存在则电荷量子化，而是 $\theta_C$ 拓扑单值性强制电荷量子化 | GT-8.5.4 |
| 拓扑超导材料筛选定理 | Topological Superconducting Material Screening Theorem | 空间群 $\to$ 约束截面拓扑 $\to T_c$ 候选材料的批量筛选框架——40 种已知超导体的几何论重筛选与预言 | 8.6 §核心 |

---

## §5 常数与参数

> **重要说明**：所有核心数值（$S_e$, $K$, $\lambda_1^{\text{eff}}$, $\lambda_2^{\text{eff}}$, 三角度）现均由谱刚性 + 自举闭环唯一导出（见 0.1 §3），无需任何外部经验输入。旧出处（0.0.3 等）为首次发现的记载，非外部锚定来源。

| 中文 | 英文 | 值 / 表达式 | 出处 |
|---|---|---|---|
| 互锁常数 $\Lambda$ | Interlocking Constant | $\Lambda = \Lambda(S_3) = 3$ | 0.0.3 §3 |
| 互锁常数 $k_0$ | Interlocking Constant | $k_0 = k_0(S_3) = 2$ | 0.0.3 §3 |
| 标度常数 $\ell_0$ | Scale Constant | $\ell_0 = V_{\text{unit}}^{-1/9} \approx 0.5991$（几何单位，无量纲） | 0.0.7 定理7.2 |
| 中心值 $S_0$ | Central Value $S_0$ | $S_0 = 96.727$，桥接函数 $S(a)$ 在 $a=\ell_0$ 处的取值，由标准形 (C1)–(C3) + 归一化条件唯一确定 | 0.1 §3.3 |
| 精细结构常数倒数 $S_e$ | Inverse Fine-Structure Constant | $S_e = 137.035999084$（谱互锁精确值） | 0.1 §3.4 |
| Hessian 谱间隙 $\Lambda_H$ | Hessian Spectral Gap | 大本征值与小本征值之比 $\Lambda_H \approx 150$，由六项代价函数 Hessian 矩阵谱刚性导出 | 0.1 §3.2 |
| 有效耦合 $\lambda_1^{\text{eff}}$ | Effective Coupling | 391.05 | 0.1 §3.4 |
| 有效耦合 $\lambda_2^{\text{eff}}$ | Effective Coupling | 59324.3 | 0.1 §3.4 |
| 质量标度 $K$ | Mass Scale | $K = 839.758793$ keV | 0.1 §3.6 |
| 几何衰减宽度 $\Gamma_{\text{geo}}$ | Geometric Decay Width | $5.75 \times 10^{-23}$ | 0.4.1 |
| 几何特征长度 $\chi_L(\ell_0)$ | Geometric Characteristic Length | $\approx 1.983$（无量纲，纯几何量） | 0.0.7 §7.3 |
| Wodzicki 留数 | Wodzicki Residue | $\mathrm{Res}_W(D^{-9}) = 512\pi^4 V/105$ | 0.0.7 §7.3 |
| 几何因子 $C_{\text{geo}}$ | Geometric Factor $C_{\text{geo}}$ | 信息场与几何结构耦合的无量纲因子，由约束截面谱决定 | 0.4.6 §1 |
| $\hbar_{\text{eff}}$ | Effective $\hbar$ | 几何论中 $\hbar$ 作为导出值，含三路交叉验证（Wodzicki留数/后验匹配/C_m） | 0.8.4 §2 |
| 退化时间 $\tau_{\text{dec}}$ | Decay Time | $\tau_{\text{dec}} \sim 7.28$ 日（中子衰变的几何特征时间） | 0.0.3 §5, 25号 |
| 质量-作用量映射常数 $k$ | Mass-Action Mapping Constant | $k = 3.728940$ keV，将作用量差分映射为跃迁能量 | 16号 §2.1 |
| 相对梯度 $\Delta$ | Relative Gradient | $\Delta \equiv g'_{MM}/g_{MM} - g'_{CC}/g_{CC} = 0.509945$，$\mathbb{R}^9$ 几何引力的内禀驱动力 | 11号 §3.2 |
| 引力常数 $k_{\text{grav}}$ | Gravitational Constant (Geometric) | $k_{\text{grav}} \equiv \Delta/2 = 0.254972$，纯几何常数，与互锁常数 $k_0=2$ 严格区分 | 11号 §4.1 |
| 特征加速度 $a_0$ | Characteristic Acceleration | $a_0 = G_{9D} \cdot S_e \cdot (\lambda_2^{\text{eff}})^{3/2} / (\chi^2 \cdot \Phi_0)$，星系尺度引力非线性修正的特征标度 | 19号 §2.4 |
| 几何Reynolds数 $\text{Re}_{\text{geo}}$ | Geometric Reynolds Number | $\text{Re}_{\text{geo}} = \lambda_2 / \lambda_1 \approx 152$，由Hessian软硬模比值严格确定 | 30号 §3.1 |
| 几何Mach数 $\text{Ma}_{\text{geo}}$ | Geometric Mach Number | 几何声速与流速之比，由既有几何本征量导出 | 30号 §3.2 |
| 几何Prandtl数 $\text{Pr}_{\text{geo}}$ | Geometric Prandtl Number | 三分切丛扩散的几何无量纲数 | 30号 §3.3 |
| 几何升力系数 $C_L^{\text{geo}}$ | Geometric Lift Coefficient | $C_L^{\text{geo}} \approx 4.1$，无实验输入锚点 | 30号 §6.1 |
| 几何阻力系数 $C_D^{\text{geo}}$ | Geometric Drag Coefficient | $C_D^{\text{geo}} \approx 0.027$，无实验输入锚点 | 30号 §6.2 |
| 残余编码偏移量 $\varepsilon_{\text{res}}$ | Residual Encoding Offset | $\varepsilon_{\text{res}} \approx 0.1556$，信息场残余编码投影到物质界导致的初始条件偏移 | 17号 §3.2 |
| 放射性测年修正量 $\Delta t$ | Radiometric Dating Correction | $\Delta t = (1/\lambda) \ln(1 + \varepsilon_{\text{res}}) \approx 0.1445/\lambda$ | 17号 §4.2 |
| Kolmogorov尺度 $\eta_K$ | Kolmogorov Scale | $\eta_K \approx 0.23\ \mu\text{m}$，由七级递推截断确定 | 30号 §5.2 |
| 几何声速 $c_s^{\text{geo}}$ | Geometric Speed of Sound | 由几何状态方程与三分切丛本征量导出 | 30号 §3.2 |
| 几何温度 | Geometric Temperature | 由信息场软模能量标度经量纲桥映射为温度 | 30号 §3.4, 13号 第13章 |
| 21cm线频率 | 21cm Line Frequency | $\nu_{21} = 1421.61\ \text{MHz}$，几何推导偏差 $+0.08\%$ | 1号 §4.6 |
| 裸弱混合角 $\sin^2\theta_W^{\text{bare}}$ | Bare Weak Mixing Angle | $0.23109$（凝聚相投影-耦合导出值） | 6号 §3.2, §4.2 |
| 物理弱混合角 $\sin^2\theta_W^{\text{phys}}$ | Physical Weak Mixing Angle | $0.23124$（Berry 相位反馈修正后），与 PDG $0.23122 \pm 0.00003$ 偏差 $2\times10^{-5}$ | 6号 §4.3 |
| 递推乘子 $r_k$ | Recursion Multipliers | $(r_1, r_2, r_3, r_4, r_5, r_6) = (6, 33.3, 10, 10, 1.125, 2)$，七级递推的逐级信息顶点数乘子 | 50号 §5.3 |
| 编码步长 $\Delta\tau_{\text{step}}$ | Encoding Step | $\sim 10^2$ s，单顶点的平均信息编码时间 | 50号 §5.6 |
| 冻结信息数 $N_{\text{info}}^{\text{freeze}}$ | Freezing Information Number | $\approx 1.1\times10^9$，I场扩散冻结完成时的全息屏顶点数 | 50号 §8 |
| 冻结时间 $t_{\text{freeze}}$ | Freezing Time | $\approx 1700$ 年，自 $t=0$ 至 I场扩散冻结完成的物理时间 | 50号 §8 |
| 精炼幂律指数 $\beta$ | Refinement Power Law Exponent | $\beta = 2$，七级递推完成后 $N_{\text{info}} \propto t^\beta$ 的精炼阶段幂律指数 | 50号 §5.6 |
| 非平衡度 $\varepsilon$ | Non-Equilibrium Degree | $\varepsilon = r_2/r_1 - 1 = 5.56$，$\text{N}_2\to\text{N}_3$ 递推跳变提供的热非平衡强度 | 51号 §6 |
| 冻结温度 $T_{\text{freeze}}^{\text{BBN}}$ | BBN Freeze Temperature | $\approx 0.79$ MeV，$n \leftrightarrow p$ 转换冻结的有效温度 | 52号 §4 |
| 中微子质量和 $\Sigma m_\nu$ | Neutrino Mass Sum | $\approx 0.118\text{--}0.122$ eV | 53号 §5 |
| $\theta_{12}$ (PMNS) | $\theta_{12}$ (PMNS) | $\approx 33.0^\circ$（零参数，实验 $33.4^\circ$，偏差 $-1.2\%$） | 55号 §6 |
| 第三峰增强因子 | Third Peak Enhancement Factor | $\approx 3.83$，$a_0/a_N^{\text{pert}} \approx 14$ 的几何增强替代暗物质粒子效应 | 54号 §7 |
| 修正引力增长因子 $\alpha$ | Modified Gravity Growth Factor | $\alpha \approx 1.44$，$G_{\text{eff}}$ 增强使结构增长加速 | 54号 §8 |
| $\sigma_8$ (几何论) | $\sigma_8$ (Geometric) | $\approx 0.75$（零参数，Planck $0.81\pm0.01$，偏差 $\sim 7\%$） | 54号 §8 |
| 声学视界 $r_s$ (几何论) | Sound Horizon $r_s$ (Geometric) | $\approx 147$ Mpc（共动），由 $N_{\text{info}}(t)$ 膨胀历史解析推导 | 54号 §9 |
| 缪子质量增强因子 $f_\mu$ | Muon Mass Enhancement Factor | $f_\mu = 2\pi(S_e - 2) = 848.46$（偏差 $+0.02\%$）。$S_e-2$：两个对称化扇区退化为一个有效自由度，有效编码容量减 2；$2\pi$：Berry 相位拓扑周期 | 60号 §6.9 |
| 缪子有效耦合 $Q_\mu^{\text{eff}}$ | Muon Effective Coupling | $0.812$（沿 $S_2^{IM}$ 路径的 Berry 联络加权平均），决定 $a_\mu$ 的截面几何因子 | 62号 §5 |
| 缪子反常磁矩 $a_\mu^{\text{B}}$（方案 B） | Muon $g-2$ (Scheme B) | $1.17(6) \times 10^{-3}$（命题级，$\sim 10\%$ 误差），以 $\theta_M^\mu = 31.94^\circ$ 重算 | 62号 §6 |

---

## §6 粒子与扇区

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质扇区 | Matter Sector ($M$) | $\theta_M$ 主导，带电轻子质量层级 | 0.0.6 §3.3 |
| 因果扇区 | Causal Sector ($C$) | $\theta_C$ 主导，中微子质量与振荡 | 0.0.6 §3.3, 7 |
| 信息扇区 | Information Sector ($I$) | $\theta_I$ 主导，场动力学 | 0.0.6 §3.3, 0.4 |
| 夸克扇区 | Quark Sector | 夸克在约束乘积球面上的几何表示，含量子化方案（0.8.6）和 CKM 混合（8号） | 0.8.6, 8号 |
| 零态 | Zero State | 总宇宙的初始对称态，$\theta_M=\theta_C=\theta_I=30^\circ$，$S=24$，公理3完备性约束的直接推论（旧称「角度锁定 Angle Locking」，已废弃） | 33号 §2, 0.0.6 §3.1 |
| 上饱和稳态 | Upper Saturation Steady State | $\theta_I \approx 72.53^\circ$，信息场衰减定理（§4）的终态 | 0.4.1 |
| 倒伏相 | Lodging Phase | 中微子质量谱的高端截断相，由因果场几何约束决定 | 7号 §3 |
| 三阶段相变 | Three-Stage Phase Transition | 信息场编码的物质界-中间界-信息界三阶段循环相变 | 31号 §1 |
| 物质界收缩时间 | Material Realm Contraction Time | 宇宙物质界的几何收缩时间尺度 | 46号 §1 |
| 黑洞冻结极限构型 | Black Hole Freezing Limit Configuration | $(\theta_M, \theta_C, \theta_I) = (45^\circ, 45^\circ, 0^+)$，信息场冻结极限 $\theta_I \to 0^+$ 的稳定构型 | 14号 §1, 16号 §1.1 |
| 物质界几何约束构型 | Material Realm Geometric Constraint Configuration | $(\theta_M, \theta_C, \theta_I) = (57.93^\circ, 26.16^\circ, 5.91^\circ)$，电子基态的三界配置，物质界特有的角度构型 | 22号 摘要, 0.0.3 §5 |
| 区域生成 | Region Genesis | 零态失衡后沿 $\eta$ 方向（因果方向）平移回归的创世推进机制 | 33号 §3 |
| 粒子凝结 | Particle Condensation | 粒子在因果推进经过其特征构型时从I场信息中凝结生成，时间由 $t_{\text{phys}}^p = \chi_T \sqrt{\lambda_1^{\text{eff}}} (\eta_{\text{init}} - \eta_p)$ 确定 | 50号 §7 |
| 凝结序列 | Condensation Sequence | 粒子按质量排序的凝结时间序列——更重粒子凝结于更早时间（更大的 $\eta$ 偏离），自然形成"先重后轻" | 50号 §7 |
| 相区结构 | Phase Zone Structure | 七级递推的三个相区：相区 I（N₁→N₃，剧烈膨胀，乘子 6 $\to$ 33）、相区 II（N₃→N₅，有序重组，乘子 10 $\to$ 10）、相区 III（N₅→N₇，趋于饱和，乘子 1.1 $\to$ 2） | 50号 §5.3 |

---

## §7 角度与几何量

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 投影强度角 | Projection Intensity Angle $\theta_i$ | 扇区向二维全息屏 $\Sigma$ 投影的强度角，$\theta_i\in(0^\circ,90^\circ)$。单扇区投影面积元比例 $\propto\sin^2\theta_i$，双扇区联合投影 $\propto\sin\theta_i\sin\theta_j$ | 0.0.0 §5.4 |
| 物质角 $\theta_M$ | Matter Angle | 公理3中物质扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 因果角 $\theta_C$ | Causal Angle | 公理3中因果扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 信息角 $\theta_I$ | Information Angle | 公理3中信息扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 三角度谱刚性锁定值 | Three-Angle Spectral Rigidity Locked Values | $(\theta_M, \theta_C, \theta_I) = (57.93^\circ,\,26.16^\circ,\,5.91^\circ)$，由谱刚性 + 八步自举闭环唯一锁定，非外部输入。$\theta_M+\theta_C+\theta_I=90^\circ$ 满足公理3约束 | 0.1 §3.5–§3.6, 63号 |
| eta 参数 | Eta Parameter | $\eta = 51.27^\circ$，当前演化状态。由信息场演化方程在谱刚性边界条件下唯一确定，非自由参数 | 0.4.1, 63号 §4 |
| 投影强度 2-形式 | Projection Intensity 2-Form | 扇区向全息屏投影的微分几何描述 | 0.0.6 §3 |
| 因果推进步长 $\delta\eta$ | Causal Advancement Step | $\delta\eta = 1/\sqrt{\lambda_1^{\text{eff}}}$，创世推进的因果方向步长 | 33号 §3.1 |
| 度规-作用量协调关系 | Metric-Action Coordination Relation | $g'_{MM}$、$g'_{CC}$ 与 $S'(0) = -2073.919082\ \text{rad}^{-1}$ 的协调关系，由六项作用量定义与公理3完备性约束导出 | 11号 §3.1 |
| 硬方向 $\xi$ | Hard Direction | 约束截面上 Hessian 大本征值 $\lambda_2^{\text{eff}}$ 的方向，被冻结 | 33号 §3.1, 0.5 §3 |
| 截面类型 | Cross-Section Type | 联合截面的三种几何类型：$\theta_C$-共享（最刚 Hessian 方向）、M-同步（次刚方向）、$\theta_I$-共享（软模，物理不可行） | 0.6.7 §6.4 |
| 拓扑扇区连通 | Topological Sector Connection | 约束流形在相变边界的扇区瞬时连通——B破坏的几何根源，势垒在相变瞬间不存在 | 51号 §3 |
| $\theta_C$ 截面拓扑缠绕数 | $\theta_C$ Cross-Section Topological Winding Number ($w$) | 夸克 $w=1$（单 $\theta_C$ 截面），重子 $w=3$（三夸克），轻子 $w=0$（无 $\theta_C$ 参与） | 51号 §3 |
| 倒伏相截断角 | Lodging Phase Cutoff Angle | $\theta_M^{\text{cutoff}} \approx 5.74^\circ$，M扇区与因果场的约束边界——截断角的有限性是中微子二重态分裂的几何根源 | 53号 §3 |
| M-C交换 | M-C Exchange | PMNS混合的几何根源：弱顶点中带电轻子的 $\theta_M$ 和 $\theta_C$ 互换 $\to$ 中微子味基的 $(\theta_M, \theta_C)$ 坐标 | 55号 §5 |
| 味空间坐标 | Flavor Space Coordinates | 中微子味本征态在 M-C 交换后的 $(\theta_M, \theta_C)$ 平面中的几何表示 | 55号 §4 |
| 缪子构型 | Muon Configuration | $(\theta_M, \theta_C, \theta_I) = (31.94^\circ, 26.16^\circ, 31.90^\circ)$，$S_2^{IM}$ 线上（$\theta_M \approx \theta_I$），$\theta_C$-共享截面驻点。偏离精确对称线仅 $0.04^\circ$ | 60号 §4, 62号 §3 |

---

## §8 概念名称（非定理）

> 以下为概念名称，不加"定理"后缀。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 本体前提 | Ontological Premise | 0.0.0 的最底层输入：零维源点 $\mathcal Z$ 携带 $S_3$ 对称性。不是公理，而是几何论唯一不可约减的本体起点 | 0.0.0 §1, §6.1 |
| 结构公理 | Structural Axiom | 0.0.0 的几何实现规则：群阶—尺度平方反比规则，由此得到半径比 $1:1/\sqrt{3}:1/\sqrt{6}$ | 0.0.0 §2.2, §6.1 |
| 编码公理 | Encoding Axiom | 0.0.0 的编码规范：二维全息屏上 $\theta_1+\theta_2+\theta_3=90^\circ$。与 0.0.6 公理3等价 | 0.0.0 §5.3, §6.1 |
| 群阶—尺度平方反比规则 | Group Order – Scale-Squared Inverse Rule | $R^2\propto 1/|H|$：剩余对称性子群的阶数越大，对应几何尺度的平方越小。是结构公理 2.1 的核心内容，非标准群论定理 | 0.0.0 §2.2 |
| 最简线性编码规范 | Minimal Linear Encoding Convention | $\theta_1+\theta_2+\theta_3=90^\circ$：三扇区投影强度角在二维全息屏上的最简无冗余线性编码。是编码公理 5.1 的核心内容 | 0.0.0 §5.3 |
| 六项无量纲代价函数 | Six-Term Dimensionless Cost Function $S$ | $S=\sum 1/\sin^2\theta_i + \sum_{i<j} 1/(\sin\theta_i\sin\theta_j)$：满足 $S_3$ 置换对称、二体截断原则与面积倒数标度的无量纲几何代价函数。在 $30^\circ$ 对称点取得唯一全局最小值 24 | 0.0.0 §5.5–§5.6 |
| 严格凸性 | Strict Convexity | 六项代价函数 $S$ 在约束定义域 $D_\theta$ 上严格凸，保证唯一全局极小值点的存在性与可计算性 | 0.0.0 §5.6 |
| 二体截断原则 | Two-Body Truncation Principle | 代价函数只保留单扇区项（$1/\sin^2\theta_i$）与成对耦合项（$1/(\sin\theta_i\sin\theta_j)$），不引入三体及以上耦合项。是最简编码原则的自然延伸 | 0.0.0 §5.5 |
| 模空间 | Moduli Space | 约束乘积球面 $M(a)$ 的唯一连续自由度是整体尺度 $a\in(0,\infty)$，模空间同胚于 $(0,\infty)$。$a\to0^+$ 时结构收缩回零维源点 | 0.0.0 §4.3 |
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
| 超导转变温度 | Superconducting Transition Temperature $T_c$ | $k_B T_c = E_{\text{scale}} \cdot g_{\text{pair}} \cdot \delta_0^2(N) / \ln\Omega_0(N, d_{\text{IR}})$，几何启发式模型构造 | 13号 §5 |
| 线性并联模型 | Linear Parallel Model | 超导多螺旋结构的几何并联模型，$\delta_0(N) = \delta_0^{\text{single}} \cdot \sqrt{N_{\text{eff}}}$ | 13号 §2 |
| 同位素效应 | Isotope Effect | 超导转变温度对同位素质量的依赖，几何起源由 $\ln\Omega_0$ 中的质量因子解释 | 13号 §6 |
| 全息屏层级递推 | Holographic Screen Hierarchical Recursion | 黑洞辐射的七级离散跃迁机制，$N_n = S_e^2 \Lambda^{2n}$ | 16号 §1 |
| SM-LCT（跨扇区介导层级相干隧穿） | Sector-Mediated Level Coherent Tunneling | 将单像素隧穿概率从 $\exp(-1263)$ 提升至 $\sim 1$ 的跨扇区机制 | 16号 §4 |
| 层级占空比 | Level Duty Ratio | $\Delta S_n / S_{BH} \sim 10^{-64}$，黑洞辐射率的内禀压制因子 | 16号 §4 |
| 暗物质证伪 | Dark Matter Falsification | 星系旋转曲线平坦化由信息场硬模相干泄漏解释，暗物质假设被几何论严格替代 | 19号 §1 |
| 信息场硬模相干泄漏 | Information Field Hard Mode Coherent Leakage | $\lambda_2^{\text{eff}}$ 的三维相干泄漏，诱导星系尺度引力非线性修正 | 19号 §2 |
| 千区并行 | Thousand-Zone Parallel | 总宇宙参数流形上数千个区域并行生成原子的机制 | 34号 §1 |
| 完美态筛选 | Perfect State Selection | 基态邻域 $|S - S_e| < 10$ 内稳定驻点的筛选机制 | 34号 §3.1 |
| 单粒子三界循环 | Single-Particle Three-Realm Cycle | 粒子在物质界-中间界-信息界之间的完整循环，由裸Hessian谱结构判定 | 33号 §6 |
| DNA双螺旋几何模型 | DNA Double Helix Geometric Model | 基于三对偶空间与氢键能的DNA/RNA/蛋白质严格数值对应框架 | 22号 摘要 |
| 几何封闭 | Geometric Closure | 材料设计公式完全封闭于0.X体系内生参数之内，不引入外部实验参数 | 43号 §1 |
| 经络 | Meridians | 因果场相位节点在信息场中激发的共振条纹的几何实现 | 40号 §2 |
| 穴位 | Acupoints | 因果场相位节点在体表的几何投影点 | 40号 §2.3 |
| 五输穴 | Five Transport Points | 对应因果场相角离散节点 $(0, \pi/2, \pi, 3\pi/2, 2\pi)$ 的五类穴位 | 40号 §2.3 |
| 三脉七轮 | Three Channels Seven Chakras | 奇经八脉中三脉与七轮的几何对应 | 40号 §3.3 |
| CMB声学峰 | CMB Acoustic Peaks | 信息场硬模在宇宙微波背景上的声学振荡印记 | 12号 §1 |
| 哈勃常数差异量级 | Hubble Constant Discrepancy Magnitude | 从几何论角度解释局域与早期宇宙 $H_0$ 测量差异的量级 | 12号 §1 |
| CMB偶极子 | CMB Dipole | 宇宙微波背景偶极各向异性的几何论解释 | 28号 §1 |
| 太阳系精密轨道 | Solar System Precision Orbit | 基于几何论引力修正的太阳系行星轨道描述 | 38号 §1 |
| 银河系结构 | Galactic Structure | 分形层级框架下银河系的几何结构描述 | 39号 §1 |
| 标准模型自由参数消解 | Standard Model Free Parameter Resolution | 标准模型19个自由参数在几何论框架内的内生推导 | 36号 §1 |
| 夸克偶素谱 | Quarkonium Spectrum | 夸克-反夸克束缚态质量谱的高维几何起源 | 23号 §1 |
| 夸克质量谱 | Quark Mass Spectrum | 夸克三代质量在约束乘积球面上的几何框架描述 | 27号 §1 |
| 分子生成 | Molecular Genesis | 从原子圆满态到分子结构的几何生成路径 | 35号 §1 |
| 层流-湍流转捩 | Laminar-Turbulent Transition | 物质界流从层流到湍流的转捩，由信息场退相干谱条件判定 | 30号 §3.5 |
| 边界模式 | Boundary Mode | $\theta_M=0$, $S=\infty$ 的构型类，M-C腰边耦合在完备性平面M扇区边界上的退化极限。光子为其代表。S=S_e约束不适用于边界模式 | 0.6.3 §4.5 |
| 正则模式 | Regular Mode | $\theta_M>0$, $S<\infty$ 的构型类，所有有质量粒子（电子、夸克等）属于正则模式。S=S_e约束适用 | 0.6.3 §4.5 |
| 腰边SO(2)剩余对称性 | Waist-Edge SO(2) Residual Symmetry | M-C腰边在退化极限 $\theta_M,\theta_C\to 0$（同时 $\theta_I\to 90^\circ$）下，腰边切空间保持二维，其等距群为SO(2)≅U(1)，是光子内部对称群的几何起源 | 0.6.8 §7.2 |
| 超精细结构 | Hyperfine Structure | 氢原子基态超精细分裂的几何根源——ℰ的信息相位通道（$\mathcal{I}$ 扇区）重叠 + 面积元投影 + $4/\pi$ 热核平行继承 | 1号 §4 |
| 21cm线 | 21cm Line | 氢原子超精细跃迁，几何推导值 $1421.61\ \text{MHz}$（偏差 $+0.08\%$），几何论标志性预言之一 | 1号 §4.6 |
| 热核平行继承 | Heat Kernel Parallel Inheritance | $4/\pi$ 因子的谱归一化来源，由 0.3.1 定理 3.2 热核渐近展开严格确定 | 1号 §4.4 |
| N=3联合截面 | N=3 Joint Cross-Section | 质子构型的几何来源框架——联合变分原理 $\delta S_3 = 0$ 在强耦合扇区模式下将夸克推向 $\theta_M \to 0$ 极限 | 1号 §4.2 |
| 弱混合角 | Weak Mixing Angle / Weinberg Angle | $\sin^2\theta_W$，由凝聚相三界耦合的扇区投影正弦比确定，含 Berry 相位反馈修正 | 6号 §3 |
| 弱电整合 | Electroweak Unification | 电磁 $U(1)_{\text{em}}$ 与弱 $SU(2)_L$ 在凝聚相三界构型中的几何统一——两者共享同一 $\mathcal{M}$-$\mathcal{C}$-$\mathcal{I}$ 耦合结构 | 6号 §1 |
| 凝聚相三角构型 | Condensed Phase Triangle Configuration | $(\theta_M,\theta_C,\theta_I) = (57.93^\circ, 26.16^\circ, 5.91^\circ)$，电磁-弱-信息三界在约束截面上的三角形几何关系 | 6号 §2.1 |
| 隔墙厚度 | Wall Thickness ($\delta_{XY}$) | 两扇区 $X$ 与 $Y$ 在约束截面上的几何距离，决定跨扇区耦合强度的基值 | 6号 §2.2 |
| 腰边-底边分解 | Waist-Base Decomposition | 三扇区耦合分解为 $\mathcal{M}$-$\mathcal{C}$ 腰边（电磁）与 $\mathcal{M}$-$\mathcal{I}$ 底边（弱），独立耦合通道 | 6号 §2.3 |
| 反常磁矩 | Anomalous Magnetic Moment ($g-2$) | $a_X = (g_X-2)/2$，由信息场角从裸基准点到当前构型的几何相位积累导出。电子 $a_e = 1.16236\times10^{-3}$（偏差 $+0.23\%$），μ子 $a_\mu$ 需路径平均 | 9号 |
| 截面偏差函数 | Cross-Section Deviation Function ($\delta_X$) | $\delta_X = Q_X/\cos\theta_M^0 - 1$，表征粒子构型相对裸基准点的几何偏离，$a_X = \frac{\alpha}{2\pi}(1+\delta_X)$ | 9号 §5.1 |
| 裸基准点 | Bare Reference Point | $(\theta_M^0,\theta_C^0,\theta_I^0) = (57.93^\circ, 26.16^\circ, 5.91^\circ)$，$S_0 = 137$，理想几何构型——严格区分于电子基态（$S_e = 137.035999084$） | 9号 §1.4 |
| 家族对称性假设 | Family Symmetry Hypothesis | 电子与 μ 子共享同一裸基准点，家族差异完全由 $\theta_I$ 偏离决定——开放接口，待家族动力学篇验证 | 9号 §2.3 |
| 几何相位类比（$g-2$） | Geometric Phase Analogy ($g-2$) | $g-2$ 的几何根源：带电轻子磁矩修正对应于信息场角从裸基准点到当前构型的几何相位积累，类比于凝聚态物理中的 Berry 相位 | 9号 §4.1 |
| 信息冻结相 | Information Freezing Phase | $\theta_I \to 0^+$ 极限，信息场被冻结，$\theta_M = \theta_C = 45^\circ$ 为稳定构型，对应黑洞内部状态 | 14号 §1.1 |
| 硬模势垒 | Hard Mode Barrier | 信息场与物质场耦合强度 $W_{MI} = \sqrt{2}/\sin\theta_I$，在 $\theta_I \to 0^+$ 下发散至 $\sim 10^{31}$，隔离信息场 | 14号 §2.1 |
| 几何压缩 | Geometric Compression | 黑洞内部三维空间在信息场冻结下被压缩为全息屏上的二维编码，体积信息转化为面积信息 | 14号 §3.1 |
| 全息熵几何公式 | Geometric Formula for Holographic Entropy | $S_{\text{BH}} = A_{\text{BH}}^{\text{phys}} / (4 \chi_L^2)$，$A_{\text{BH}}^{\text{phys}} \neq 4\pi R_{\text{BH}}^2$ | 14号 §5.3 |
| 三代轻子质量刚性 | Three-Generation Lepton Mass Rigidity | 电子-缪子-τ 三代轻子质量由联合截面驻点条件 + $C_n$ 递推 + 因果角锁定联合约束，非自由参数 | 24号 |
| 跨层级耦合二层作用量 | Cross-Level Two-Layer Action ($W_{12}$) | 电子与缪子之间的跨层级耦合作用量，由 $b'$ 前置因子控制，$\theta_C$-共享截面是其核心约束 | 24号 §3.1 |
| 构型A | Configuration A | 电子基态的九素基底构型，$(\theta_M^e,\theta_C^e,\theta_I^e) = (57.93^\circ, 26.16^\circ, 5.91^\circ)$，$S_e = 137.035999084$ | 24号 §2.2 |
| $C_n$ 递推 | $C_n$ Recursion | $C_n = M_{n-1}/n$（命题 H2），质量标度的全息屏层级递推，独立于角度驻点条件 | 24号 §6.2 |
| I³多尺度相干泄漏 | I³ Multi-Scale Coherent Leakage | 信息场硬模 $\lambda_2^{\text{eff}}$ 在多个物理尺度上的相干泄漏，导致 $a_0$ 跨越 5 个数量级的四种观测窗口（星系旋转曲线、子弹星系团、CMB第三峰、大尺度结构） | 54号 §6 |
| 纯重子宇宙 | Pure Baryon Universe | 无暗物质粒子的几何修正宇宙——星系旋转曲线平坦化、CMB第三峰增强、大尺度结构增长均由 I³ 多尺度相干泄漏提供 | 54号 §1 |
| 参数空间拓扑缺陷 | Parameter Space Topological Defect | 约束流形参数空间中的 Berry 曲率奇点（类似 Weyl 半金属），不是实空间中的自由磁荷 | 56号 §4 |
| 有效磁单极子 | Effective Magnetic Monopole | 参数空间拓扑缺陷的物理效应类比，$\pi_2(S)=0$ 确保实空间无自由磁单极子 | 56号 §4 |
| 约束流形可缩性 | Contractibility of Constrained Manifold | 约束流形 $S$ 为 2-单纯形 $\to$ 可缩 $\to$ $\pi_2(S)=0$ $\to$ $H^2(S;\mathbb{Z})=0$ $\to$ 所有 U(1) 丛平凡 | 56号 §3 |
| 原初扰动冻结 | Primordial Perturbation Freezing | I场在小 $N_{\text{info}}$ 下快速扩散均匀化 $\to$ 早期宇宙均匀；$N_{\text{info}}$ 增长 $\to$ 扩散冻结 $\to$ 非均匀性被保留为结构种子 | 50号 §4 |
| Sakharov条件几何翻译 | Geometric Translation of Sakharov Conditions | 重子生成三条件的几何论统一翻译——B破坏 = 拓扑扇区连通，C/CP破坏 = $\theta_C$ 截面挠率，热非平衡 = 递推乘子跳变 | 51号 §2 |
| B破坏拓扑机制 | Topological B Violation Mechanism | 约束流形的扇区连通只在相变边界打开——今日宇宙 B破坏率 $\sim 10^{-110}$ s⁻¹（宇宙寿命内概率 $\sim 10^{-92}$），解释质子稳定性 | 51号 §3 |
| 递推膨胀 | Recursive Expansion | 宇宙膨胀的几何驱动——七级递推乘子序列（6 $\to$ 33 $\to$ 10 $\to$ 10 $\to$ 1.1 $\to$ 2）的自然展开，不需要暴脹子或慢滚势能 | 50号 §5 |
| 氘瓶颈几何机制 | Deuterium Bottleneck Geometric Mechanism | C扇区共凝结的最小曲率门槛——非偶然数值巧合，是约束流形上多核子构型的结构必然 | 52号 §4 |
| ⁷Be几何不稳定性 | ⁷Be Geometric Instability | ⁷Be（$J^P=3/2^-$，质量数=7）处于 $N_{\text{info}}^{\text{deut}}$ 时的几何稳定性边界以下 $\to$ ⁷Li问题在几何论中自然消失 | 52号 §7 |
| 倒伏相不完全 | Incomplete Lodging Phase | 精确倒伏相极限（$\theta_M \to 0$）下三个中微子完全简并——可观测的二重态分裂（$m_2/m_1 \approx 1.038$）完全来自截断角的有限性 | 53号 §3 |
| 平均度规近似 | Average Metric Approximation | PMNS混合角的零阶近似——在 $(\theta_M, \theta_C)$ 平面上使用带电轻子平均度规，$\theta_{12} \approx 33.0^\circ$（偏差 $-1.2\%$） | 55号 §6 |
| 非均匀度规修正 | Non-Uniform Metric Correction | 超出平均度规的局域度规变化——解释 $\theta_{23}$ 和 $\theta_{13}$ 残余偏差的方向（🟡 开放） | 55号 §10 |
| 电弱平滑 crossover | Electroweak Smooth Crossover | $\theta_M$ 随 $N_{\text{info}}$ 平滑演化 $\to$ 质量平滑演化 $\to$ 无对称性破缺相变，与格点结果一致（$m_H \gtrsim 72$ GeV 时为 crossover） | 4号 §5.3 |
| 强 CP 拓扑冻结 | Strong CP Topological Freezing | U(1)_A 手征转动 = ℐ 扇区全局 $\theta_I$ 平移，公理 1 真空标记强制冻结 $\to$ $\bar{\theta}=0$。与 CKM $\delta_{\text{CP}}$ 严格区分：前者 ℐ 扇区冻结，后者 M-C 挠率 | 5号 §5.5 |
| θ̄=0 结构强制 | θ̄=0 Structural Enforcement | $\bar{\theta}=0$ 是定理非巧合——零参数，零新粒子，轴子不存在 | 5号 §5.5 |
| $S_3$ 迷向子群 | $S_3$ Isotropy Subgroup | 约束流形 $\Delta^2$ 上 $S_3$ 对称性的五种迷向子群类型：$\{e\}$（三角全不等 → 电子）、$S_2^{IM}$（$\theta_M \approx \theta_I$ → 缪子）、$S_2^{CI}$（$\theta_C \approx \theta_I$ → τ子）、$S_2^{MC}$（梯度流不可达）、$S_3/A_3$（重心 → 非粒子构型）。穷举完毕，第四代无处可去 | 57号 §3 |
| 梯度流不可达 | Gradient Flow Inaccessibility | $S_2^{MC}$（$\theta_M \approx \theta_C$）被约束梯度流单调性（$d\theta_I/d\tau > 0$）排除——不是数学上不可能，是物理上不可达。$\theta_I$ 是演化方向，永远不可能成为被 $\theta_M \approx \theta_C$ 孤立的角 | 57号 §3.4 |
| 顶点奇点 | Vertex Singularity | 约束流形顶点 $(90^\circ, 0, 0)$ 处 $S$-泛函的 $1/\sin^2 0^\circ$ 发散——自由色荷被拓扑禁止的根源。奇点不是正则化失败，是几何结构的必然输出 | 58号 §3 |
| Hessian 谱三投影 | Hessian Spectrum Triple Projection | $\lambda_1, \lambda_2$ 两个 Hessian 本征值分别投影为三个独立物理表达：因果场动力学 $\Lambda_\xi = -\frac{1}{2}\log(\lambda_2/\lambda_1)$（0.5）、裸引力耦合 $G_{9D} \propto \sqrt{\lambda_1/\lambda_2}$（10号）、宏观有效引力 $G_{\text{eff}} = G_{9D}\sqrt{1+a_0/a_N}$（54号）。万物皆几何的最后一块拼图 | 59号 §2–§6 |
| $S_2$ 对称性恢复 | $S_2$ Symmetry Restoration | μ 子和 τ 子落在 $S_2$ 线上（两个角相等），电子是唯一 $S_3$ 完全破缺的粒子。对称性恢复是质量增强因子 $f_\mu = 2\pi(S_e-2)$ 的几何根源——每退化一个扇区，有效编码容量减 1 | 60号 §6.9 |
| ℰ 映射函子 | ℰ Mapping Functor | 几何量→物理量的函子映射——将纯几何量（$S_e$, $K$, $\theta_\alpha$）映射为可观测物理量（$\alpha$, $m_e$, 耦合常数）的跨卷函子构造 | 2.1 §3 |
| 观测链 | Observation Chain | 信息场→观测的时间层级结构——信息场编码经谱解码、量纲桥、后验匹配三步转化为可观测物理预言 | 3A.6 §核心 |
| 时间尺度硬化 | Time Scale Hardening | 观测链末端的有效时间压缩——观测链越长，有效时间分辨率越粗，宏观时间标度从 $\chi_T \sim 10^{-17}$ s 硬化至人类经验尺度 $\sim 10^0$ s | 3A.6 §核心 |
| 几何引力起源 | Geometric Origin of Gravity | 引力作为几何梯度流的涌现——$\mathbb{R}^9$ 梯度流相对梯度 $\Delta = 0.509945$ 的内禀驱动，非独立力 | 11号 §3.2 |
| 跨级渗透 | Cross-Level Percolation | 约束截面之间的信息渗透强度函数——控制跨层级耦合的渗透率，由 Hessian 谱间隙 $\Lambda_H$ 决定 | 0.2.1.1 §1 |
| 谱互锁闭包 | Spectral Interlock Closure | 三场谱互锁关系形成的闭合拓扑结构——所有谱互锁定理构成不可分割的闭包块，无外部输入依赖 | 4.2 §核心 |

---

## §9 构造性概念（诚实标注）

> 以下为构造性概念，非严格定理。在文章中使用时必须加「诚实标注」。

| 中文 | 英文 | 说明 | 出处 |
|---|---|---|---|
| 桥接函数标准形（定义5.2） | Bridging Function Standard Form | 原称"桥接公理"，但非公理（几何论只有三条公理）。标准化为 $S=12(a^2/\ell_0^2+\ell_0^2/a^2)$，归一化条件为构造性假设。§4 定理列表中保留交叉引用条目指向本节 | 0.0.7 定义5.2, 5.2' |
| $\ell_0$ 的物理涌现 | Emergence of $\ell_0$ | $\ell_0$ 是谱几何单位锚点，与实验长度尺度的匹配属于条件性命题层 | 0.0.7 §7.3 |
| $\hbar$ 数值涌现 | Emergence of $\hbar$ | $\hbar$ 作为几何量的导出值，非基本常数 | 0.3.1 §5 |
| Hopf 假设（度量等价部分） | Hopf Hypothesis (Metric Equivalence) | 公理3的三分切丛结构中，Hopf纤维化的**度量等价** $r_{\mathcal{M}} = r_\Sigma$ 部分仍为假设（0.3.6 假设4.0）。拓扑部分已升级为定理（见 §4 Hopf纤维化定理（拓扑部分）） | 0.3.6 假设4.0, 0.3.8 §1 |
| M 场量子化框架 | M-Field Quantization Framework | M 场量子化的完整构造框架（0.8.0–0.8.6），含 Dirac 约束量子化、形变量子化等，属构造性方案 | 0.8.0–0.8.6 |
| Dirac 约束量子化方案 | Dirac Constraint Quantization Scheme | 未约化相空间中的约束代数与动量映射，属构造性方案 | 0.8.2 §1 |
| 形变量子化方案 | Deformation Quantization Scheme | M场量子谱与梯度流桥接的形变量子化构造 | 0.8.3 §1 |
| 核幻数几何框架 | Nuclear Magic Number Geometric Framework | 约束截面弯曲结构下核幻数的几何解释，属研究框架 | 0.2.3 §3 |
| 联合稳态非摄动求解 | Joint Steady State Non-Perturbative Solution | 时间尺度分离与平均场自洽的非摄动求解方案 | 0.5.4 §1 |
| $T_c$ 通用公式（构造性） | $T_c$ Universal Formula (Constructive) | $k_B T_c = E_{\text{scale}} \cdot g_{\text{pair}} \cdot \delta_0^2(N) / \ln\Omega_0(N, d_{\text{IR}})$，几何启发式模型构造，非三公理严格定理。体材料 $\Delta S_{\text{pair}}$ 由 $T_c$ 实验值反推 | 13号 §5, 诚实声明 |
| $\ln\Omega_0(N, d_{\text{IR}})$ 模型公式 | $\ln\Omega_0(N, d_{\text{IR}})$ Model Formula | 四项几何来源的条件性假设，$d_{\text{IR}}=1,2$ 由 $\mathrm{Spin}(8)$ triality 根系确定 | 13号 §3 |
| $\delta_0(N)$ 标度律 | $\delta_0(N)$ Scaling Law | $\delta_0(N) = \delta_0^{\text{single}} \cdot \sqrt{N_{\text{eff}}}$，$N_{\text{eff}} = \min(N, 7)$，几何模型构造 | 13号 §2 |
| 离散-连续极限（流体） | Discrete-Continuum Limit (Fluid) | 0.4.1 开放项 O1（离散→Laplace-Beltrami收敛），流体力学连续介质极限未完全证明 | 30号 §2.1 |
| 进动系数3（构造性推导） | Precession Factor 3 (Constructive Derivation) | 水星近日点进动系数 3 的几何论推导，一阶引力加速度部分为构造性推导 | 11号 §5.2 |
| SM-LCT 三猜想（启发性） | SM-LCT Three Conjectures (Heuristic) | 跨扇区介导层级相干隧穿机制的三个猜想（§4.2–4.4），标注为启发性猜想 | 16号 §4.2–4.4 |
| 原子层面 Berry 相位圆满判据 | Atomic-Level Berry Phase Completion Criterion | 原子层面 Berry 相位与圆满判据的构造级假设 | 34号 §2.6 |
| 温度量纲桥闭合 | Temperature Dimensional Bridge Closure | 温度量纲桥直接闭合为开放问题，当前由标准换算因子桥接 | 13号 第13章, 30号 §3.4 |
| 路径平均（扩展工作假设） | Path Averaging (Extended Working Hypothesis) | $\langle Q \rangle_X = \frac{1}{\Delta\xi_X} \int_0^{\Delta\xi_X} Q(\xi) \mathrm{d}\xi$，μ 子大位移下截面几何沿 Hamilton 流主通道的几何相位积累。属扩展工作假设，非严格定理 | 9号 §7.2 |
| 三代轻子 $C_n$ 递推假设 | Three-Generation $C_n$ Recursion Hypothesis | $C_n = M_{n-1}/n$（命题 H2），基于数值巧合 $15/31$ 的启发性假设，非严格定理 | 24号 §6.2 |
| $(c_1+c_2)/2=5$ 启发性识别 | $(c_1+c_2)/2=5$ Heuristic Identification | $c_1+c_2 \approx 10.306$ $\to$ 平均 $\approx 5.153$ 接近整数 5（偏差 $+3.1\%$）——3% 不应是巧合，可能反映深层结构，但九素互扼严格证明链待 0.0.7 扩展。**诚实标注：启发性识别，非定理** | 53号 §4 |
| 全迹路线失败 | Full-Trace Route Failure | 尝试证明 $\operatorname{tr}(H^{\text{eff}})/H_{MM}^0 = 10$，但在构型A处的直接计算给出 $\sim 1900$，证伪了迹守恒假设。已诚实记录，避免后续研究走入同一死胡同 | 53号 §4 |
| CMB第三峰增强（命题级） | CMB Third Peak Enhancement (Proposition-grade) | $a_0/a_N^{\text{pert}} \approx 14$ $\to$ 扰动引力增强 $\sim 3.7$ 倍 $\to$ 第三峰增强。结构层已定位，量级正确，但精确到与 Planck 逐峰对比需玻尔兹曼代码（工具缺口） | 54号 §7 |
| 大尺度结构增长（命题级） | Large-Scale Structure Growth (Proposition-grade) | $G_{\text{eff}} = G_{9D}\sqrt{1+a_0/a_N}$ 增强 $\alpha\approx 1.44$ $\to$ $\sigma_8\approx 0.75$（Planck $0.81\pm0.01$，偏差 $\sim 7\%$）。$G_{\text{eff}}(t)$ 完整时间演化待算（E2工具缺口） | 54号 §8 |
| 缪子反常磁矩方案 B 闭合（命题级） | Muon $g-2$ Scheme B Closure (Proposition-grade) | $a_\mu^{\text{B}} = 1.17(6) \times 10^{-3}$，含简谐近似 + 路径面积估算（各 $\sim 10\%$）。形式化完整（Berry 联络 $\to$ 曲率 $\to$ 有效耦合 $\to$ $a_\mu$），精度待 D1（非简谐修正）、D2（外场耦合常数）、D3（路径精确参数化）提升 | 62号 §6 |
| $f_\mu$ 增强因子的 $W_{12}$ 路线排除 | $W_{12}$ Route Exclusion for $f_\mu$ Enhancement | $W_{12}$（联合截面 Fisher 编码容量耦合 $= -5.15$）在任何合理定义下不足以承载 $f_\mu \sim 849$ 的增强。正确路线 $f_\mu = 2\pi(S_e-2)$ 不需要 $W_{12}$——联合截面 Hessian 中 M-C 交叉项被 $1/a' \sim 3.4\times10^{-5}$ 天然压制 | 63号（已并入 60号 §6.9.4） |

---

## §10 禁用词清单

> 以下词语在几何论文章中禁止使用，违者退回修改。

| 禁用词 | 原因 | 替代方案 |
|---|---|---|
| 第四公理 | 几何论只有三条公理 | 使用"构造性假设""定义"或"定理" |
| $\mathcal{E}$ 映射（作为理论内部映射层） | 映射功能已被自举闭环内部化，仅剩的后验命名约定在附录A，不参与推导 | 使用"后验命名对照（附录A）"或直接描述几何结构 |
| 外部锚点 / 外部输入参数 | 几何论所有参数（三角度、$K$、$S_e$）均由谱刚性+自举闭环在理论内部唯一导出 | 直接说明对应数值的几何推导来源 |
| 物理-几何映射 | 语言暗示存在两个分离的本体论领域需要桥梁连接 | 使用"几何结构的后验物理识别"或"命名约定" |
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

- `[260705.2]` **0.0.0《零与谱》引入新底层公理体系**：0.0.0 第二版引入本体前提 1.1 + 结构公理 2.1 + 编码公理 5.1 三层结构，与 0.0.3–0.0.7 的公理1–3 并存。两套体系互补：0.0.0 为最底层（零→谱→约束乘积球面），0.0.3–0.0.7 在此基础上构建（参数空间→激发态→物理映射）。→ 已在 §1 拆分为两个子表，明确标注各自出处与独立性。编码公理 5.1 与公理3 等价，两处均加注。

- `[260705.2]` **「谱震动」→「谱展开」术语废弃**：旧版 0.0.0（260622.6）使用「谱震动」描述零维源点向几何谱的展开过程。新版 0.0.0（260705.2）将术语统一为「谱展开」（Spectral Unfolding），旧称「谱震动」已废弃。→ 已在 §2 添加新条目「谱展开」并标注旧称废弃；全文不得再使用「谱震动」。

- `[260702]` **0.0.7 旧公理编号与术语表 §1 不兼容**：0.0.7（十方几何空间）使用旧编号——公理1=角度和、公理2=作用量和，而术语表 §1 标准公理体系为公理1=圆拓扑、公理2=边界极限、公理3=全息屏编码条件。→ 已在 §1 添加醒目标注；0.0.7 修订版将统一编号。阅读 0.0.7 时：旧「公理1」→ 标准「公理3 完备性约束」；旧「公理2」→ 标准「作用量定义」。

- `[260702]` **Hopf 纤维化定理/假设分裂**：此前 §4 和 §9 对同一概念给出矛盾的定理/非定理标签。→ 已拆分为：拓扑部分为定理（§4 Hopf纤维化定理（拓扑部分），0.3.6 定理4.3），度量等价 $r_{\mathcal{M}} = r_\Sigma$ 部分为假设（§9 Hopf假设（度量等价部分），0.3.6 假设4.0）。

- `[260702]` **$C_{\text{geo}}$ 三次重复**：此前 §2、§5、§7 各出现一次 $C_{\text{geo}}$ 条目，内容相同。→ 已合并至 §5（常数与参数）作为唯一条目，§2 和 §7 中删除。

- `[260703]` **特征加速度 $a_0$ 术语冲突**：19号文章用符号 $a_0$ 表示信息场硬模相干泄漏导出的特征加速度，与 Bohr 半径 $a_0$ 符号冲突。→ 几何论内统一使用 $a_0$ 为特征加速度（19号），Bohr 半径使用全称或 $a_B$。

- `[260703]` **系统提示 c 锚点声明与术语表 §3 不兼容**：系统提示称「光速c为唯一外部锚点」，术语表 §3 ℰ映射锚点明确说「c 由单一核心映射——三分切丛的 $\mathcal{M}$-$\mathcal{C}$ 腰边耦合结构（对应电磁相互作用）——经 ℰ 映射量纲桥导出，非外部锚点」。→ 术语表 §3 为权威源；系统提示中「唯一外部锚点」说法作废。c 是几何映射内部导出的本征量之一。

- `[260703]` **系统提示「公理3：质量公式」与术语表 §4 不兼容**：系统提示称「公理3：m = K * sin^3 theta_M」，术语表 §4 质量-角度耦合定理明确标注「由公理1–3及约束乘积球面构造导出，非公理」。→ 术语表为权威源；质量公式是定理，不是公理。几何论只有三条公理（圆拓扑、边界极限、全息屏编码条件）。

- `[260703]` **系统提示「九素互扼定理」与术语表 §8 不兼容**：系统提示称「关键定理：九素互扼定理」，术语表 §8 标注九素互扼为概念名称「属超定锁定结构，非独立定理」。→ 术语表为权威源。九素互扼是公理—常数—工具层之间的超定锁定结构的概念包，涉及多个定理的交叉约束，不是一个孤立的定理。

- `[260703.3]` **桥接函数标准形 §4（定理）vs §9（构造性概念）标签冲突**：此前 §4 列为定理条目「由 (C1)–(C3) 加归一化条件唯一确定」，§9 列为构造性概念「归一化条件为构造性假设」。两者对同一公式的认知地位矛盾。→ 统一为构造性概念：§4 删除定理级条目，替换为交叉引用「→ 见 §9 构造性概念。归一化条件为构造性假设，非公理亦非独立定理」；§9 保留完整描述并标注 §4 引用指向本节。

- `[260703.3]` **角度锁定 vs 零态：同一配置两个名称**：此前 §6 中「角度锁定」和「零态」均指向 $\theta_M=\theta_C=\theta_I=30^\circ$，为同一角度配置的两个独立条目。→ 统一为「零态」（Zero State），废弃「角度锁定」。零态条目吸收角度锁定的描述（公理3完备性约束的直接推论），标注旧称已废弃。

- `[260703.3]` **信息场衰减定理与上饱和稳态的交叉引用缺失**：此前 §4「信息场衰减定理」描述仅写「上饱和稳态 $\theta_I \sim 72.53^\circ$」，§6「上饱和稳态」描述仅写「信息场演化终态」，双方未建立交叉引用。两者是定理与结论的关系（定理描述衰减过程，稳态是终态），非同一概念的二名。→ 保留两个条目，各自添加交叉引用：§4 定理标注「终态为 §6 上饱和稳态」；§6 稳态标注「信息场衰减定理（§4）的终态」。

- `[260710.4]` **$\mathcal{E}$ 映射从理论核心层移除**：0.1（260710.3）将 $\mathcal{E}$ 映射从核心框架层移除，其锚定功能已被八步自举闭环内部化。§3 已重写为「后验命名对照」，§5 常数出处统一更新为 0.1，§10 禁用词新增 $\mathcal{E}$ 映射（内部映射层）。→ 术语表全文已更新，旧 $\mathcal{E}$ 映射条目删除；仍在使用的术语表 §11.6 规则 5 中的「经 ℰ 映射量纲桥导出」同步修正为「经量纲桥导出」；旧术语参见 §3.2 迁移表。

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

**当前版本**：260715.1（见文件头）

### §11.6 文章写作原则

1. 未知即说未知——不要编造。
2. 公理、定理、定义、命题、猜测严格区分。
3. 数值必须标注来源。
4. 超出几何论框架的结论必须诚实标注。
5. 光速非外部锚点：$c$ 由三分切丛 $\mathcal{M}$-$\mathcal{C}$ 腰边耦合结构的量纲桥导出。$\mathcal{E}$ 映射已不作为理论内部层存在，详见 §3 后验命名对照。