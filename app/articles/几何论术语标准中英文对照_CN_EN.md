# 几何论术语标准中英文对照

> **版本**：260703.3  
> **用途**：几何论全部术语在此统一。任何新文章引入术语前必须先在本表登记。  
> **语言**：中文 / English  
> **更新规则**：见 §11 维护规则  
> **本次更新**：第二轮补缺——新增术语来自：1号（氢原子超精细结构）、6号（弱混合角与弱电整合）、9号（反常磁矩）、14号（黑洞与信息悖论）、24号（三代轻子质量刚性）。首轮涵盖：11号（水星进动）、12号（CMB哈勃）、13号（超导）、16号（黑洞辐射频谱）、17号（放射性测年）、19号（星系旋转曲线）、22号（DNA）、23号（夸克偶素）、27号（夸克质量谱）、28号（CMB偶极子）、30号（几何流体力学）、33号（创世）、34号（原子生成）、35号（分子生成）、36号（标准模型19参数）、37号（卫星系统）、38号（太阳系）、39号（银河系）、40号（经络）、43号（合金设计）

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

## §3 核心映射 ℰ

> ℰ 是几何论物理识别的唯一锚点。质量、光速等均为其导出项，不是第四条公理。

| 中文 | 英文 | 公式 / 陈述 | 出处 |
|---|---|---|---|
| ℰ 映射（量纲桥） | ℰ-map (Dimensional Bridge) | $\mathcal{E}: \text{几何量} \to \text{物理量}$ | 0.3.1 §4 |
| ℰ 映射锚点 | ℰ-map Anchor | ℰ 映射的导出量：$c = 2.99792458 \times 10^8$ m/s，由单一核心映射——三分切丛的 $\mathcal{M}$-$\mathcal{C}$ 腰边耦合结构（对应电磁相互作用）——经 ℰ 映射量纲桥导出，非外部锚点 | 0.3.1 §4, 0.6.3 §1 |
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

---

## §7 角度与几何量

| 中文 | 英文 | 定义 | 出处 |
|---|---|---|---|
| 物质角 $\theta_M$ | Matter Angle | 公理3中物质扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 因果角 $\theta_C$ | Causal Angle | 公理3中因果扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| 信息角 $\theta_I$ | Information Angle | 公理3中信息扇区向全息屏 $\Sigma$ 的投影强度角 | 0.0.6 §3.3 |
| eta 参数 | Eta Parameter | $\eta = 51.27^\circ$，当前演化状态 | 0.4.1 |
| 投影强度 2-形式 | Projection Intensity 2-Form | 扇区向全息屏投影的微分几何描述 | 0.0.6 §3 |
| 因果推进步长 $\delta\eta$ | Causal Advancement Step | $\delta\eta = 1/\sqrt{\lambda_1^{\text{eff}}}$，创世推进的因果方向步长 | 33号 §3.1 |
| 度规-作用量协调关系 | Metric-Action Coordination Relation | $g'_{MM}$、$g'_{CC}$ 与 $S'(0) = -2073.919082\ \text{rad}^{-1}$ 的协调关系，由六项作用量定义与公理3完备性约束导出 | 11号 §3.1 |
| 硬方向 $\xi$ | Hard Direction | 约束截面上 Hessian 大本征值 $\lambda_2^{\text{eff}}$ 的方向，被冻结 | 33号 §3.1, 0.5 §3 |

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

- `[260703]` **特征加速度 $a_0$ 术语冲突**：19号文章用符号 $a_0$ 表示信息场硬模相干泄漏导出的特征加速度，与 Bohr 半径 $a_0$ 符号冲突。→ 几何论内统一使用 $a_0$ 为特征加速度（19号），Bohr 半径使用全称或 $a_B$。

- `[260703]` **系统提示 c 锚点声明与术语表 §3 不兼容**：系统提示称「光速c为唯一外部锚点」，术语表 §3 ℰ映射锚点明确说「c 由单一核心映射——三分切丛的 $\mathcal{M}$-$\mathcal{C}$ 腰边耦合结构（对应电磁相互作用）——经 ℰ 映射量纲桥导出，非外部锚点」。→ 术语表 §3 为权威源；系统提示中「唯一外部锚点」说法作废。c 是几何映射内部导出的本征量之一。

- `[260703]` **系统提示「公理3：质量公式」与术语表 §4 不兼容**：系统提示称「公理3：m = K * sin^3 theta_M」，术语表 §4 质量-角度耦合定理明确标注「由公理1–3及约束乘积球面构造导出，非公理」。→ 术语表为权威源；质量公式是定理，不是公理。几何论只有三条公理（圆拓扑、边界极限、全息屏编码条件）。

- `[260703]` **系统提示「九素互扼定理」与术语表 §8 不兼容**：系统提示称「关键定理：九素互扼定理」，术语表 §8 标注九素互扼为概念名称「属超定锁定结构，非独立定理」。→ 术语表为权威源。九素互扼是公理—常数—工具层之间的超定锁定结构的概念包，涉及多个定理的交叉约束，不是一个孤立的定理。

- `[260703.3]` **桥接函数标准形 §4（定理）vs §9（构造性概念）标签冲突**：此前 §4 列为定理条目「由 (C1)–(C3) 加归一化条件唯一确定」，§9 列为构造性概念「归一化条件为构造性假设」。两者对同一公式的认知地位矛盾。→ 统一为构造性概念：§4 删除定理级条目，替换为交叉引用「→ 见 §9 构造性概念。归一化条件为构造性假设，非公理亦非独立定理」；§9 保留完整描述并标注 §4 引用指向本节。

- `[260703.3]` **角度锁定 vs 零态：同一配置两个名称**：此前 §6 中「角度锁定」和「零态」均指向 $\theta_M=\theta_C=\theta_I=30^\circ$，为同一角度配置的两个独立条目。→ 统一为「零态」（Zero State），废弃「角度锁定」。零态条目吸收角度锁定的描述（公理3完备性约束的直接推论），标注旧称已废弃。

- `[260703.3]` **信息场衰减定理与上饱和稳态的交叉引用缺失**：此前 §4「信息场衰减定理」描述仅写「上饱和稳态 $\theta_I \sim 72.53^\circ$」，§6「上饱和稳态」描述仅写「信息场演化终态」，双方未建立交叉引用。两者是定理与结论的关系（定理描述衰减过程，稳态是终态），非同一概念的二名。→ 保留两个条目，各自添加交叉引用：§4 定理标注「终态为 §6 上饱和稳态」；§6 稳态标注「信息场衰减定理（§4）的终态」。

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
5. 光速非外部锚点：$c$ 由单一核心映射（三分切丛 $\mathcal{M}$-$\mathcal{C}$ 腰边耦合结构，对应电磁相互作用）经 ℰ 映射量纲桥导出（详见 §3 ℰ 映射锚点）。