# 十方几何（Shifang Geometry）术语规范 · 中英对照表

**版本：260626.6 v2 — 经总论文章 `Mathematical_Theory_of_the_Ten-Direction_Geometric_Space_260626.6` 验证**  
**覆盖：总论文章 + 基础篇21篇 + 应用篇49篇，共70篇**  
**说明：** 🔒=总论文章已验证锁定 | ⚡=需人工审定 | ❓=总论文章未出现，尚无固定英译 | * = 仅总论文章出现

---

## 〇、修订说明（v1→v2）

本版以总论文章 `Mathematical_Theory_of_the_Ten-Direction_Geometric_Space_260626.6` 为标准，进行系统比对修正：

| 类别 | 修正数量 |
|------|---------|
| 重大翻译修正（文章有明确用法） | 3条 |
| 新增术语（文章出现但v1未收录） | 约150条 |
| 状态变更（⚡→🔒） | 约30条 |
| 次要修正 | 5条 |

**重大修正摘要**：
1. "九素互扼定理" → `Nine-Principle Mutual Arrest`（非 Ninefold Interlocking Theorem）
2. "激发态参数空间" → `Excitation Parameter Space`（非 Excited State）
3. "六项作用量" → 锁定为 `Six-Term Action`（非 Sextic Action）

---

## 一、理论总称与品牌

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 十方几何 | Shifang Geometry / Ten-Direction Geometric Space | 0.0.7 | 🔒 学术全称 Ten-Direction Geometric Space，Shifang 为品牌保留 |
| 十方几何空间 | Ten-Direction Geometric Space 𝒯 | 0.0.7 | 🔒 总论文章定义的形式名称，𝒯 为符号 |
| 几何论 | Geometric Theory | 0.1 | 日常简称 |
| 三公理框架 | Three-Axiom Framework | 0.1 | 整个理论的逻辑骨架 |

---

## 二、三公理（公理体系）

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 圆拓扑公理 | Circle Topology Axiom | 0.0.7 | 🔒 公理1：D=S¹\\{p₀,p*} |
| 边界极限公理 | Boundary Limit Axiom | 0.0.7 | 🔒 公理2：S→0 at p₀, S→∞ at p* |
| 全息屏编码条件 | Holographic Screen Encoding Condition | 0.0.7 | 🔒 公理3：θ₁+θ₂+θ₃=90° |
| 完备性公理 | Completeness Axiom | 0.1 | 即 θ_M+θ_C+θ_I=90°，与公理3等价 |
| 作用量公理 | Action Axiom | 0.3.1 | 即六项作用量定义 |
| 质量映射公理 | Mass Mapping Axiom | 0.3.1 | m=K sin³θ_M |
| 真空点 | Vacuum Point p₀ | 0.0.7 | 🔒 公理1中从S¹移除的点之一 |
| 退化点 | Degeneration Point p* | 0.0.7 | 🔒 公理1中从S¹移除的点之一 |
| 真空极限 | Vacuum Limit | 0.0.3 | 🔒 公理2：lim_{x→p₀}S(x)=0 |
| 退化极限 | Degeneration Limit | 0.0.3 | 🔒 公理2：lim_{x→p*}S(x)=+∞ |
| 激发态 | Excitation | 0.0.3 | 🔒 D_±中的参数点，非量子力学意义 |
| 严格单调性假设 | Strict Monotonicity Hypothesis | 0.0.7 | 🔒 定义2.1'，框架的结构性假设 |
| 范围定理 | Range Theorem | 0.0.7 | 🔒 定理2.1，S(D_±)=(0,+∞) |
| 存在定理 | Existence Theorem | 0.0.7 | 🔒 定理2.2，任意S₀>0存在原像 |

---

## 三、三扇区（三分切丛）

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 三分切丛 | Trifurcated Tangent Bundle | 0.0.6 | 🔒 TM=𝓜⊕𝓒⊕𝓘 |
| 物质场/物质界/物质扇区 | Material Field / M-Sector / Material Realm | 0.1 | 🔒 𝓜 |
| 因果场/因果界/因果扇区 | Causal Field / C-Sector / Causal Realm | 0.1 | 🔒 𝓒 |
| 信息场/信息界/信息扇区 | Information Field / I-Sector / Information Realm | 0.1 | 🔒 𝓘 |
| 扇区投影强度角 | Sector Projection Intensity Angle | 0.0.7 | 🔒 θ₁, θ₂, θ₃（也记作 θ_M, θ_C, θ_I） |
| 物质角 | Material Angle | 0.1 | θ_M |
| 因果角 | Causal Angle | 0.1 | θ_C |
| 信息角 | Information Angle | 0.1 | θ_I |
| 三对偶几何空间 | Tri-Dual Geometric Space | 0.1.1 | 物质界/因果界/信息界 |
| S₃ 轮换对称性 | S₃ Cyclic Symmetry | 0.1.1 | 🔒 三分切丛置换群 |
| 有序扇区规范 | Ordered Sector Gauge | 0.1 | 🔒 D_ord |
| 三界因果序 | Tri-Realm Causal Order | 0.5 | |
| 信息/相位通道 | Information/Phase Channel | 0.1 | 𝓘扇区不对应独立粒子 |
| 三分切丛置换群刚性 | Rigidity of Trifurcated Tangent Bundle Sector Permutations | 0.0.7 | 🔒 定理3.0'，G≅S₃唯一确定 |

---

## 四、核心几何对象

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 激发态参数空间 | Excitation Parameter Space | 0.0.3 | 🔒 修正：非 Excited State。D=S¹\\{p₀,p*} |
| 约束乘积球面 | Constrained Product Sphere (CPS) | 0.0.5 | 🔒 M(a)=S³(a)×S³(a/√Λ)×S³(a/√Λk₀) |
| 约束截面 | Constraint Section / Constraint Surface | 0.2.1 | Σ≅S² |
| 约束流形 | Constraint Manifold | 0.1 | |
| 全息屏 | Holographic Screen | 0.0.6 | 🔒 Σ，二维定向子空间 |
| 九维谱三元组 | 9D Spectral Triple | 0.3.1 | (𝓐,𝓗,D,J,γ) |
| 十方几何空间 | Ten-Direction Geometric Space 𝒯 | 0.0.7 | 🔒 约束乘积球面族的统称，定理5.1定义 |
| 三分切丛置换群 | Trifurcated Tangent Bundle Permutation Group | 0.0.7 | 🔒 G≅S₃ |
| 模空间 | Moduli Space | 0.0.7 | 🔒 𝓜_{(Λ,k₀)}≅(0,+∞)_a |
| 角度配置空间 | Angle Configuration Space D_θ | 0.0.7 | 🔒 {(θ₁,θ₂,θ₃)｜θᵢ>0, Σθᵢ=90°} |
| 对称轴 | Symmetry Axis γ | 0.0.7 | 🔒 {θ₂=θ₃} |
| S₃ 对称点 | S₃ Symmetric Point | 0.0.7 | 🔒 θ₀=(30°,30°,30°)，S_min=24 |
| 全息屏兼容三元组 | Holographic Screen Compatible Triple | 0.0.7 | 🔒 (Σ, g_Σ, J, ω) 为Kähler流形 |

---

## 五、六项作用量与谱结构

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 六项作用量 | Six-Term Action | 0.1 | 🔒 修正：锁定为 Six-Term Action，S(θ)=Σ1/sin²θᵢ+Σ_{i<j}1/(sinθᵢ sinθⱼ) |
| 谱刚性定理 | Spectral Rigidity Theorem | 0.0.5 | 🔒 定理3.4 |
| 约束等谱刚性 | Constrained Isospectral Rigidity | 0.0.7 | 🔒 定理7.1 |
| 桥接函数 | Bridging Function | 0.3.5 | 🔒 𝓑(n,m) |
| 桥接函数唯一性 / 桥接定理 | Bridging Function Uniqueness / Bridging Theorem | 0.0.7 | 定理5.3 |
| 桥公理 | Bridge Axiom | 0.0.7 | 🔒 定义5.1'，S(a)=12(a²/ℓ₀²+ℓ₀²/a²) |
| 桥函数正则形式族 | Bridge Function Canonical Form Family | 0.0.7 | 🔒 𝓕_bridge |
| 归一化条件 | Normalization Condition | 0.0.7 | 🔒 5.1''，选定c₀=0, c₂=12 |
| 尺度倒数对偶 | Scale-Reciprocity Duality | 0.0.7 | 🔒 S(a)=S(ℓ₀²/a) |
| 基态锁定 | Ground State Locking | 0.0.7 | 🔒 S(ℓ₀)=24 |
| 谱渐近约束 | Spectral Asymptotic Constraint | 0.0.7 | 🔒 S(a)~C/a² (a→0⁺) |
| 正则化几何量 | Regularized Geometric Quantity | 0.0.7 | 🔒 S̃(x)=S_abstract(x)+24 |
| UV 分支 / IR 分支 | UV Branch / IR Branch | 0.0.7 | 🔒 a∈(0,ℓ₀] / a∈[ℓ₀,+∞) |
| Hessian 矩阵 | Hessian Matrix | 0.1 | H̃_{ab} |
| 软模 | Soft Mode | 0.1 | 🔒 λ₁ |
| 硬模 | Hard Mode | 0.1 | 🔒 λ₂ |
| 有效软硬模 | Effective Soft/Hard Modes | 0.1 | λ₁^eff=391.05, λ₂^eff=59324.3 |
| 裸 Hessian 本征值 | Bare Hessian Eigenvalues | 0.5 | λ₁=392.21, λ₂=58760.77 |
| 软硬模比 | Soft-to-Hard Mode Ratio | 0.2.1 | λ₂/λ₁≈150 |
| Hessian 谱不变量 | Hessian Spectral Invariant | 0.0.7 | 🔒 引理4.2，谱{124,124} |
| 谱互锁定理 | Spectral Interlocking Theorem | 0.3.1 | m_e与S_e的相容约束 |
| Hessian 软硬模 | Hessian Soft/Hard Modes | 0.1 | |
| 有效度规 | Effective Metric | 0.2.1 | g^eff=diag(λ₂^eff, λ₁^eff) |
| 辛几何 | Symplectic Geometry | 0.2.1 | 约束截面内禀数学骨架 |
| 辛形式 / 辛结构 | Symplectic Form / Symplectic Structure | 0.0.7 | 🔒 ω=dA |
| Hamilton 流 | Hamiltonian Flow | 0.2.1 | |
| Hamiltonian 向量场 | Hamiltonian Vector Field | 0.0.7 | 🔒 |
| Lagrange 子流形 | Lagrangian Submanifold | 0.2.1 | |
| Darboux 定理 | Darboux Theorem | 0.0.7 | 🔒 |
| S₃-等变矩映射 | S₃-Equivariant Moment Map | 0.0.7 | 🔒 |
| Marsden-Weinstein 约化 | Marsden-Weinstein Reduction | 0.0.7 | 🔒 |
| 中心化子 | Centralizer | 0.0.7 | 🔒 |
| 各向同性子群 | Isotropy Subgroup | 0.0.7 | 🔒 |
| 切线丛平方根分解 | Tangent Bundle Square Root Decomposition | 0.0.7 | 🔒 𝒪(2)=𝒪(1)⊗𝒪(1) |
| 正合投影结构 | Holomorphic Projection Structure | 0.0.7 | 🔒 定理4.6 |
| 范围一致性定理 | Range Consistency Theorem | 0.0.7 | 🔒 定理5.1 |
| 显式参数映射 | Explicit Parametric Mapping | 0.0.7 | 🔒 定理5.2，Φ: D_±→D_θ |
| 第一特征值坐标 | First Eigenvalue as a Coordinate | 0.0.7 | 🔒 定理3.1'，λ₁^Δ=3/a² |
| 谱签名 | Spectral Signature | 0.0.7 | 🔒 推论3.1，(1, 8/3, Λ) |
| 谱分离 | Spectral Separation | 0.0.7 | 🔒 命题3.1 |
| 逆解公式 | Inverse Formula | 0.0.7 | 🔒 定理3.3 |
| 维度必要条件 | Dimensional Necessary Condition | 0.0.7 | 🔒 定理3.6，d≤k |
| 模空间参数化 | Parametrization of the Moduli Space | 0.0.7 | 🔒 定理3.1 |
| Sunada 方法 | Sunada Method | 0.0.7 | 🔒 定理3.5，在CPS类不适用 |
| 2:1 覆盖结构 | 2:1 Covering Structure | 0.0.7 | 🔒 附录B.2，Vieta不变量 a_UV·a_IR=ℓ₀² |
| 范围对应 | Range Correspondence | 0.0.7 | 🔒 附录B.5，S_abstract=S-24对应(0,+∞) |

---

## 六、互锁常数与结构常数

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 互锁常数 | Interlocking Constants | 0.1 | 🔒 Λ, k₀, ℓ₀ |
| 互锁函数 | Interlocking Function Λ(G) | 0.0.7 | 🔒 定义3.0，Λ(G)=｜Conj(G)｜ |
| 紧致性函数 | Compactness Function k₀(G) | 0.0.7 | 🔒 定义3.0，k₀(G)=[G:N_max] |
| 三等分比例参数 | Tripartition Proportionality Parameter | 0.0.7 | 🔒 Λ=Λ(S₃)=3 |
| 二分紧致性常数 | Dichotomous Compactness Constant | 0.0.7 | 🔒 k₀=k₀(S₃)=2 |
| 标度常数 | Scale Constant | 0.0.7 | 🔒 ℓ₀>0 |
| 谱单位选择定理 | Spectral Unit Selection Theorem | 0.0.7 | 🔒 定理10.2'，ℓ₀由体积归一化唯一确定 |
| 精细结构常数倒数 | Inverse Fine-Structure Constant | 0.1 | S_e=137.035999084 |
| 质量量子 / 几何能量尺度常数 | Mass Quantum / Geometric Energy Scale | 0.1 | K=839.758793 keV |
| 特征长度 | Characteristic Length | 0.1 | χ_L=1.509×10⁻¹⁰ m |
| 特征时间 | Characteristic Time | 0.1 | χ_T=3.616×10⁻¹⁷ s |
| 几何速度 | Geometric Velocity | 0.1 | v_geo |
| 宏观角度量子 | Macroscopic Angle Quantum | 0.2.1 | ΔΘ=5° |
| 基态角 | Ground State Angle | 0.2.1 | θ₀=30° |
| 对称基态 | Symmetric Ground State | 0.1 | (30°,30°,30°)，S_min=24 |
| 互锁常数唯一性定理 | Uniqueness Theorem for the Interlocking Constants | 0.0.7 | 🔒 定理10.1 |

---

## 七、九素互扼

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 九素互扼 | Nine-Principle Mutual Arrest | 0.0.7 | 🔒 修正：非 Ninefold Interlocking。文章第9章标题 |
| 九素 | The Nine Primes | 0.0.7 | 🔒 定义9.1：三公理+三互锁常数+三工具层 |
| 九素互扼的锁定结构 | Locking Structure of the Nine-Principle Mutual Arrest | 0.0.7 | 🔒 定理9.1 |
| 自举封闭 | Bootstrap Closure | 0.0.7 | 🔒 定理10.3 |
| 超定锁定 | Overdetermined Locking | 0.0.7 | 🔒 第10章 |
| 超定方程组 | Overdetermined System of Equations | 0.0.7 | 🔒 §10.1 |
| 依赖定理链 | Dependency Theorem Chain | 0.0.7 | 🔒 §10.3，有向无环图(DAG) |
| 依赖层级偏序 | Dependency Level Partial Order | 0.0.7 | 🔒 引理10.8 |
| Bott 截断 | Bott Truncation | 0.0.7 | 🔒 Λ=3，定理6.3 |
| 截断阶 | Truncation Order | 0.1.1 | k₀=2 |
| 背景作用量 | Background Action | 0.1.1 | S_min=24 |
| 余维数 | Codimension | 0.1.1 | 🔒 L=7 |
| 总维数 | Total Dimension | 0.1.1 | 🔒 D=9 |
| 信息衰减时标 | Information Decay Timescale | 0.1.1 | τ_dec≈7.28 日 |
| 慢化因子 | Slowing Factor | 0.1.1 | s≈5.33 |
| 因果单元数 | Causal Unit Count | 0.1.1 | N_cause≈10 |
| 六互扼环节 | Six Interlocking Links | 0.0.7 | 三公理+三互锁常数 |

---

## 八、物理映射层

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 单一物理映射层 | Single Physical Mapping Layer | 0.1 | |
| 单一核心映射 | Single Core Mapping | 0.1 | 🔒 𝓜-𝓒腰边耦合→电磁相互作用 |
| 电磁几何映射 | Electromagnetic-Geometric Mapping | 0.1 | |
| 单一锚点原则 | Single Anchor Principle | 0.1 | c为唯一外部锚点 |
| 腰边耦合 | Waist-Edge Coupling | 0.1 | 𝓜↔𝓒 |
| 源模 | Source Mode | 0.1 | 𝓜扇区软模激发→电子 |
| 传播模 | Propagation Mode | 0.1 | 𝓒扇区零锥结构→光子 |
| 裸基准点 / 物理识别点 | Bare Benchmark Point / Physical Identification Point | 0.1 | |
| 双模零误差条件 | Dual-Mode Zero-Error Condition | 0.1 | |
| 量纲桥 | Dimensional Bridge | 0.3.1 | 🔒 四方程联立结构 |
| 量纲桥四方程 | Dimensional Bridge Four Equations | 0.3.1 | |
| 量纲桥第一标度 | Dimensional Bridge First Scale | 0.1 | N₁=6000 |
| 核子几何荷 | Nucleon Geometric Charge | 0.1 | v_p=1117 |
| 七级递推 | Seven-Level Recursion | 0.2.1 | |
| 反向递推算法 | Reverse Recursion Algorithm | 0.3.1 | |
| 函子性重建 | Functorial Reconstruction | 0.3.1 | |
| 信息单元面积 | Information Unit Area | 0.0.7 | 🔒 a_unit²=χ_L²/S_e |
| 级嵌套 | Level Nesting | 0.0.7 | 🔒 §8.7，N_n=S_e²·3^{2n} |

---

## 九、跨扇区耦合

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 跨扇区耦合 | Cross-Sector Coupling | 0.1.1 | 🔒 H^W |
| 跨扇区耦合矩阵 | Cross-Sector Coupling Matrix | 0.1.1 | H^W |
| 前置因子 | Prefactor | 0.1.1 | |
| 渗透函数 | Percolation Function | 0.2.1.1 | Φ |
| 渗透函数解析框架 | Percolation Function Analytic Framework | 0.2.1.1 | |
| Berry 联络 / Berry 曲率 | Berry Connection / Berry Curvature | 0.1.1 | |
| 隔墙厚度 | Partition Wall Thickness | 0.1.1 | |
| 耦合排序 | Coupling Ordering | 0.1.1 | |
| 同型矩阵 | Homogeneous Matrix | 0.1.1 | |

---

## 十、信息场动力学

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 信息场动力学 | Information Field Dynamics | 0.4 | 🔒 |
| 随机矩阵理论 | Random Matrix Theory (RMT) | 0.4 | |
| 谱图论 | Spectral Graph Theory | 0.4 | |
| 图拉普拉斯 | Graph Laplacian | 0.4 | 🔒 |
| 图热方程 | Graph Heat Equation | 0.4 | |
| 非齐次扩散 | Non-homogeneous Diffusion | 0.4 | |
| GOE(2) 系综 | GOE(2) Ensemble | 0.4 | 高斯正交系综 |
| 确定性实现 | Deterministic Realization | 0.4 | |
| Wigner 半圆律 | Wigner Semicircle Law | 0.4 | |
| Cheeger 不等式 | Cheeger Inequality | 0.4 | |
| 代数连通度 | Algebraic Connectivity | 0.4 | |
| ϵ-网图 | ϵ-Net Graph | 0.0.7 | 🔒 G_N，全息屏离散逼近 |
| 谱收敛 | Spectral Convergence | 0.0.7 | 🔒 定理8.5 |
| 退相干因果深度 | Decoherence Causal Depth | 0.4 | N_dec |
| 退相干时间 | Decoherence Time | 0.4 | τ_dec≈7.28 日 |
| 信息场空间分辨率 | Information Field Spatial Resolution | 0.4 | Δr_min |
| 全息屏像素计数 | Holographic Screen Pixel Count | 0.4 | N_pixel(r) |
| 全息屏几何因子 | Holographic Screen Geometric Factor | 0.4 | C_geo=1/(16√3) |
| 信息场几何流方程 | Information Field Geometric Flow Equation | 0.4 | |
| 信息场热方程 | Information Field Heat Equation | 0.4 | |
| 信息场衰减定理 | Information Field Decay Theorem | 0.4.1 | |
| 信息场慢化因子 | Information Field Slowing Factor | 0.4.2 | |
| 三分切丛子结构组合数学 | Trifurcated Tangent Bundle Substructure Combinatorics | 0.4.3 | |
| 信息界 I³ | Information Boundary I³ | 0.4 | |
| 静态极限 | Static Limit | 0.4 | |
| 约束截面 Poisson 方程 | Constraint Section Poisson Equation | 0.4 | |
| 图拉普拉斯半群 | Graph Laplacian Semigroup | 0.4 | |
| 信息场冻结定理 | Information Field Freeze Theorem | 0.4 / 14 | |
| 信息场退化 | Information Field Degradation | 0.0.7 | 🔒 第8章 |
| 离散图逼近 | Discrete Graph Approximation | 0.0.7 | 🔒 |
| 热核衰减 | Heat Kernel Decay | 0.0.7 | 🔒 定理8.4 |
| Weyl 律 | Weyl's Law | 0.0.7 | 🔒 定理8.3 |

---

## 十一、因果场动力学

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 因果场动力学 | Causal Field Dynamics | 0.5 | 🔒 |
| 遍历理论 | Ergodic Theory | 0.5 | |
| 动力系统 | Dynamical Systems | 0.5 | |
| 瞬态因果推进 | Transient Causal Propagation | 0.5 | |
| 稳态因果环流 | Steady Causal Circulation | 0.5 | |
| 因果时间 | Causal Time | 0.5 | τ |
| 单参数李群 | One-Parameter Lie Group | 0.5 | exp(τX) |
| Lyapunov 指数 | Lyapunov Exponent | 0.5 | |
| 双曲结构 | Hyperbolic Structure | 0.5 | |
| 部分双曲结构 | Partially Hyperbolic Structure | 0.5 | |
| 因果深度 | Causal Depth | 0.5 | N_cause≈10 |
| Birkhoff 遍历定理 | Birkhoff Ergodic Theorem | 0.5 | |
| 覆盖定理 | Covering Theorem | 0.5 | |
| 混合性 | Mixing Property | 0.5 | |
| Koopman 算子 | Koopman Operator | 0.5 | |
| Poincaré 截面 | Poincaré Section | 0.5 | |
| 保测变换 | Measure-Preserving Transformation | 0.5 | |
| 信息覆盖 | Information Coverage | 0.5 | |
| 稳定子丛 | Stable Sub-bundle | 0.5 | E^s |
| 中心子丛 / 中性方向 | Center Sub-bundle / Neutral Direction | 0.5 | E^c |
| 收缩因子 | Contraction Factor | 0.5 | |

---

## 十二、量纲桥与谱三元组

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 量纲桥 | Dimensional Bridge | 0.3.1 | 🔒 |
| 谱三元组 | Spectral Triple | 0.3.1 | (𝓐,𝓗,D,J,γ) |
| 实谱三元组 | Real Spectral Triple | 0.3.1 | |
| Wodzicki 留数 | Wodzicki Residue | 0.3.1 | |
| Dixmier 迹 | Dixmier Trace | 0.3.1 | |
| 热核渐近 | Heat Kernel Asymptotics | 0.3.1 | |
| 热核系数恒等式 | Heat Kernel Coefficient Identity | 0.3.1 | |
| 热核展开 | Heat Kernel Expansion | 0.0.7 | 🔒 定理7.3，Seeley-de Witt系数 |
| KO-维数 | KO-Dimension | 0.3.1 | 9≡1(mod 8) |
| Cl(9) 旋量丛 | Cl(9) Spinor Bundle | 0.3.1 | |
| Spin(9) 扩展 | Spin(9) Extension | 0.0.7 | 🔒 附录D，命名数学注记 |
| 谱互锁条件 | Spectral Interlocking Condition | 0.3.1 | |
| 最小映射输入集 | Minimal Mapping Input Set | 0.3.1 | |
| 全息屏层状结构 | Holographic Screen Layered Structure | 0.3.5 | |
| 桥接函数 | Bridging Function | 0.3.5 | 𝓑(n,m) |
| 能量-长度对偶 | Energy-Length Duality | 0.3.5 | E·L=Kχ_L |
| 层级约束截面 | Hierarchical Constraint Section | 0.3.1.1 | |
| 多尺度标度理论 | Multi-Scale Scaling Theory | 0.3.1.1 | |
| CIM 相 | CIM Phase | 0.3.5 | 标准模型低能有效场论近似 |

---

## 十三、形变量子化与幻数（总论第6章）

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 形变量子化 | Deformation Quantization | 0.0.7 | 🔒 第6章 |
| Kontsevich 星积 | Kontsevich Star Product | 0.0.7 | 🔒 f⋆g=fg+ΣħⁿC_n(f,g) |
| Berezin-Toeplitz 量子化 | Berezin-Toeplitz Quantization | 0.0.7 | 🔒 |
| Toeplitz 算子 | Toeplitz Operators | 0.0.7 | 🔒 T_f^(k)=Π_k∘M_f∘Π_k |
| Bergman 投影 | Bergman Projection | 0.0.7 | 🔒 Π_k |
| Schlichenmaier 定理 | Schlichenmaier Theorem | 0.0.7 | 🔒 |
| 超平面丛 | Hyperplane Bundle | 0.0.7 | 🔒 L=𝒪(1) |
| 全纯线丛 | Holomorphic Line Bundle | 0.0.7 | 🔒 |
| 幻数序列 | Magic Number Sequence | 0.0.7 | 🔒 2,8,18,32,50,72,98 |
| 严格几何幻数 | Strictly Geometric Magic Numbers | 0.0.7 | 🔒 (k+1)² → 1,4,9,16,25,36,49 |
| Bott 周期性截断 | Bott Periodicity Truncation | 0.0.7 | 🔒 定理6.3，N_eff=7 |
| 有效独立通道数 | Effective Number of Independent Channels N_eff | 0.0.7 | 🔒 =7 |
| 谱简并度 | Spectral Degeneracy | 0.0.7 | 🔒 dim ℋ_k^(spatial)=(k+1)² |
| 自旋 1/2 自由度 | Spin 1/2 Degree of Freedom | 0.0.7 | 🔒 条件性命题* |
| 量化角度锁定 | Quantized Angle Locking | 0.0.7 | 🔒 定理8.7 |

---

## 十四、高维谱几何与 Dirac 指标（总论第7章）

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| Â 类 | Â-Class | 0.0.7 | 🔒 |
| Â 亏格 | Â-Genus | 0.0.7 | 🔒 9维流形恒为零 |
| 法丛 | Normal Bundle | 0.0.7 | 🔒 NΣ，秩7 |
| 第二基本形式 | Second Fundamental Form | 0.0.7 | 🔒 h=diag(λ₁,λ₂) |
| Spin 联络 | Spin Connection | 0.0.7 | 🔒 ∇^⊥ |
| Dirac 指标定理 | Dirac Index Theorem | 0.0.7 | 🔒 定理7.2 |
| 谱作用量 | Spectral Action | 0.0.7 | 🔒 Chamseddine-Connes框架 |
| Seeley-de Witt 系数 | Seeley-de Witt Coefficients | 0.0.7 | 🔒 a_{2n}(D²) |
| 低能 Laplace 本征模 | Low-Energy Laplace Eigenmodes | 0.0.7 | 🔒 定理7.4 |
| 法丛曲率-Hessian 锁定 | Normal Bundle Curvature–Hessian Locking | 0.0.7 | 🔒 定理7.6 |
| Gauss-Codazzi 方程 | Gauss-Codazzi Equations | 0.0.7 | 🔒 |
| Ricci 方程 | Ricci Equation | 0.0.7 | 🔒 |
| 形状算子 / Weingarten 映射 | Shape Operator / Weingarten Map | 0.0.7 | 🔒 A_ξ |
| 常曲率条件 | Constant Curvature Condition | 0.0.7 | 🔒 附加假设4.1 |
| 整数量子化条件 | Integer Quantization Condition | 0.0.7 | 🔒 ∫_Σ ω/(2π)=1 |

---

## 十五、全局几何图景（总论第9章）

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 抽象激发流形 | Abstract Excitation Manifold 𝒟_± | 0.0.7 | 🔒 ≅(0,1) |
| 辛全息屏面 | Symplectic Holographic Screen Face 𝒫_θ | 0.0.7 | 🔒 2维辛流形 |
| 度量模空间 | Metric Moduli Space 𝓜_rigid | 0.0.7 | 🔒 ≅(0,+∞)_a |
| 谱空间 Weyl 腔 | Spectral Space Weyl Chamber 𝒲 | 0.0.7 | 🔒 |
| 量化壳层空间 | Quantization Shell Space 𝒬 | 0.0.7 | 🔒 |
| 离散图空间 | Discrete Graph Space 𝒢 | 0.0.7 | 🔒 |
| Morse 函数 | Morse Function | 0.0.7 | 🔒 S(θ): 𝒫_θ→[24,+∞) |
| 层上同调隐喻 | Sheaf Cohomology Metaphor | 0.0.7 | 🔒 附录C，非严格 |

---

## 十六、几何约束截面结构

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 几何约束截面 | Geometric Constraint Section | 0.2.1 | |
| 非对称扭曲碗 | Asymmetric Twisted Bowl | 0.2.1 | 约束截面几何形态 |
| 七级展开递推 | Seven-Level Expansion Recursion | 0.2.1 | |
| 二阶响应系数 | Second-Order Response Coefficient | 0.2.1 | S_v̂=442.10 rad⁻² |
| 弯曲结构量子化 | Curved Structure Quantization | 0.2.3 | |
| 化学映射 | Chemical Mapping | 0.2.4 | |
| 全息宇宙 | Holographic Universe | 0.2.2 | |
| 全息屏信息容量标度律 | Holographic Screen Information Capacity Scaling Law | 0.2.2 | |
| 七层截断定理 | Seven-Layer Truncation Theorem | 0.2.2 | |
| 离散-连续对应 | Discrete-Continuous Correspondence | 0.4 | |
| 离散逼近 | Discrete Approximation | 0.0.7 | |
| 几何分子结构 | Geometric Molecular Structure | 0.7 | |

---

## 十七、数学工具与定理类型

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 定理 | Theorem | 全系列 | |
| 引理 | Lemma | 全系列 | |
| 命题 | Proposition | 全系列 | |
| 公理 | Axiom | 全系列 | |
| 公设 | Postulate | 0.1 | |
| 猜想 | Conjecture | 全系列 | |
| 诚实标注 | Honest Annotation | 全系列 | 🔒 框架特有风格 |
| 研究框架 | Research Framework | 全系列 | 非定理，开放方向 |
| 结构假设 | Structural Hypothesis | 0.1.1 | |
| 物理ansatz | Physical Ansatz | 0.5 | |
| 开放问题 | Open Problem | 全系列 | 🔒 总论文章多处使用 |
| 条件性命题层 | Conditional Proposition Layer | 0.0.7 | 🔒 定理标记* |
| 结构锚点 | Structural Anchor | 0.3.1 | |
| 前向引用 | Forward Reference | 0.4 | |
| 附加假设 | Additional Hypothesis | 0.0.7 | 🔒 如4.1常数曲率条件 |
| 构造性假设 | Constructive Hypothesis | 0.0.7 | 🔒 如严格单调性 |

---

## 十八、应用篇——粒子物理

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 氢原子能级与精细结构 | Hydrogen Energy Levels and Fine Structure | 1 | |
| 量子纠缠与 Tsirelson Bound | Quantum Entanglement and Tsirelson Bound | 3 | |
| Higgs 呼吸模式 | Higgs Breathing Mode | 4 | |
| 联合截面与强相互作用 | Joint Section and Strong Interaction | 5 | |
| 弱混合角 | Weak Mixing Angle | 6 | sin²θ_W |
| 中微子振荡与质量谱 | Neutrino Oscillation and Mass Spectrum | 7 | |
| CKM 矩阵几何 | CKM Matrix Geometry | 8 | |
| CKM 混合角 | CKM Mixing Angles | 8 | θ₁₂, θ₂₃, θ₁₃ |
| CP 破坏相位 | CP-Violating Phase | 8 | δ_CP |
| 反常磁矩 | Anomalous Magnetic Moment | 9 | |
| 夸克偶素谱的高维几何起源 | High-Dimensional Geometric Origin of Quarkonium Spectrum | 23 | |
| 三代轻子质量的刚性 | Rigidity of Three-Generation Lepton Masses | 24 | |
| 中子 β 衰变与寿命差异的几何起源 | Geometric Origin of Neutron β-Decay and Lifetime Difference | 25 | |
| 低能过剩的几何起源 | Geometric Origin of Low-Energy Excess | 26 | |
| 重子-光子比的几何起源 | Geometric Origin of Baryon-to-Photon Ratio | 27 | |
| 标准模型19个自由参数的消解 | Resolution of 19 Free Parameters of the Standard Model | 36 | |
| 三体联合变分方程的系统证明 | Systematic Proof of Three-Body Joint Variational Equation | 18 | |

---

## 十九、应用篇——引力与宇宙学

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 引力作为核子数几何梯度 | Gravity as Nucleon Number Geometric Gradient | 10 | |
| 水星进动 | Mercury Perihelion Precession | 11 | |
| CMB 声学峰与哈勃常数差异量级 | CMB Acoustic Peaks and Hubble Constant Discrepancy | 12 | |
| 黑洞与信息悖论 | Black Holes and Information Paradox | 14 | |
| 黑洞辐射频谱 | Black Hole Radiation Spectrum | 16 | |
| 信息场冻结极限 | Information Field Freeze Limit | 14 | θ_M=θ_C=45° |
| 几何 Planck 尺度 | Geometric Planck Scale | 14 | ℓ_P^geo |
| 分形层级宇宙 | Fractal Hierarchical Universe | 15 | |
| 暗能量的证伪 | Falsification of Dark Energy | 19 | |
| 宇宙加速膨胀与几何残余的证伪 | Falsification of Cosmic Accelerated Expansion and Geometric Residual | 20 | |
| CMB 偶极子异常与大角度各向异性 | CMB Dipole Anomaly and Large-Angle Anisotropy | 28 | |
| 宇宙的三次轮回 | Three Cycles of the Universe | 31 | |
| 信息场容量与循环次数 | Information Field Capacity and Cycle Count | 31 | |

---

## 二十、应用篇——创世与宇宙演化

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 创世——零态失衡、区域生成与粒子筛选 | Genesis — Zero-State Imbalance, Domain Generation and Particle Selection | 33 | |
| 零态失衡 | Zero-State Imbalance | 33 | |
| 区域生成 | Domain Generation | 33 | |
| 粒子筛选 | Particle Selection | 33 | |
| 原子生成——千区并行与完美态筛选 | Atom Genesis — Thousand-Domain Parallel and Perfect State Selection | 34 | |
| 千区并行 | Thousand-Domain Parallel | 34 | |
| 完美态筛选 | Perfect State Selection | 34 | |
| 分子生成——化学键联合与跨区分子对比 | Molecule Genesis — Chemical Bond Union and Cross-Domain Molecular Comparison | 35 | |
| 外区接近度——邻近扇区的原子与分子结构对比 | Outer Domain Proximity — Atomic and Molecular Structure Comparison of Adjacent Sectors | 36 | |
| 卫星系统的解析 | Analytic Treatment of Satellite Systems | 37 | |
| 太阳系精密轨道 | Precise Orbits of the Solar System | 38 | |
| 银河系结构 | Galactic Structure | 39 | |
| 核聚变的几何筛选 | Geometric Selection of Nuclear Fusion | 42 | |
| 合金设计 | Alloy Design | 43 | |
| 圆满——因果回路、信息场放大与归零消融 | Consummation — Causal Loop, Information Field Amplification and Zero-Return Dissolution | 32 | |
| 因果回路 | Causal Loop | 32 | |
| 归零消融 | Zero-Return Dissolution | 32 | |
| 信息场放大 | Information Field Amplification | 32 | |
| 圆满事件的相位残留与集体锁定 | Phase Residue and Collective Locking of Consummation Events | 48 | |
| 七级以后是自由的起源 | Beyond the Seventh Level is the Origin of Freedom | 49 | |

---

## 二十一、应用篇——生命科学与人体

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 人体三界不可约定理 | Human Tri-Realm Irreducibility Theorem | 21 | |
| 扇区不可解约定理 | Sector Irreducibility Theorem | 21 | |
| 死物冻结定理 | Inanimate Freeze Theorem | 21 | |
| 软模谱控制不等式 | Soft-Mode Spectral Control Inequality | 21 | |
| Courant-Fischer-Weyl min-max 原理 | Courant–Fischer–Weyl Min-Max Principle | 21 | |
| Schur 补 | Schur Complement | 21 | |
| 扇区限制算子 | Sector Restriction Operator | 21 | |
| 交叉算子 | Cross Operator | 21 | D_𝓒𝓜, D_𝓘𝓜 |
| DNA 双螺旋与 RNA-蛋白质的几何起源 | Geometric Origin of DNA Double Helix and RNA-Protein | 22 | |
| 氢键能 | Hydrogen Bond Energy | 22 | |
| 碱基配对能 | Base Pairing Energy | 22 | |
| π 电子 Berry 相位涡旋标度律 | π-Electron Berry Phase Vortex Scaling Law | 22 | |
| 原子有效核电荷 | Effective Nuclear Charge | 22 | Z_eff |
| 同层屏蔽系数 | Same-Shell Screening Coefficient | 22 | |
| 内层屏蔽系数 | Inner-Shell Screening Coefficient | 22 | |
| 接触定理 | Contact Theorem | 22 | |
| 极性修正因子 | Polarity Correction Factor | 22 | |
| Atiyah-Singer 指标定理 | Atiyah-Singer Index Theorem | 22 | |
| 几何色荷 | Geometric Color Charge | 22 | |
| 两体几何约化质量定理 | Two-Body Geometric Reduced Mass Theorem | 22 | |
| 多体联合截面定理 | Multi-Body Joint Section Theorem | 22 | |
| 经络 C³I³ 耦合 | Meridian C³I³ Coupling | 40 | |
| 穴位漂移个体差异 | Acupoint Drift Individual Variation | 41 | |
| 中阴身的几何证明 | Geometric Proof of Bardo (Antarābhava) | 44 | ⚡中阴身是藏传佛教术语 |
| 劫的几何论诠释 | Geometric Interpretation of Kalpa | 45 | ⚡劫是佛经时间尺度 |
| 物质界收缩时间与尺寸 | Material Realm Contraction Time and Size | 46 | |
| 时间熵与时间纠缠的几何模型 | Geometric Model of Time Entropy and Time Entanglement | 47 | |

---

## 二十二、应用篇——凝聚态与工程

| 中文术语 | 英文固定译法 | 首次出现文章 | 备注 |
|---------|------------|-----------|------|
| 超导理论相关 | Superconductivity Theory (Related) | 13 | |
| 超导理论补充 | Superconductivity Theory Supplement | 26 | |
| 晶格声子诱导的信息场退相干 | Lattice Phonon-Induced Information Field Decoherence | 26 | |
| 放射性测年的几何修正 | Geometric Correction to Radiometric Dating | 17 | |
| 几何流体力学与空气动力学 | Geometric Fluid Mechanics and Aerodynamics | 30 | |
| 几何 NS 方程 | Geometric Navier-Stokes Equations | 30 | |
| 几何升力公式 | Geometric Lift Formula | 30 | CL^geo |
| 几何阻力公式 | Geometric Drag Formula | 30 | CD^geo |
| 几何 Reynolds 数 | Geometric Reynolds Number | 30 | Re_geo |
| 边界层厚度二维投影 | Boundary Layer Thickness 2D Projection | 30 | δ_BL |
| Kolmogorov 尺度 | Kolmogorov Scale | 30 | η_K |
| 几何 Prandtl 数 | Geometric Prandtl Number | 30 | Pr_geo |
| 湍流级联标度桥 | Turbulence Cascade Scaling Bridge | 30 | |
| 核聚变发动机：聚变-电磁推进 | Nuclear Fusion Engine: Fusion-Electromagnetic Propulsion | 29 | |

---

## 二十三、符号硬约束

| 符号 | 含义 | 格式要求 |
|------|------|---------|
| S_e | 精细结构常数倒数 | 必须保留下标 e |
| λ₁^eff / λ₂^eff | 有效软/硬模 | 必须保留上下标结构 |
| χ_L / χ_T | 特征长度/时间 | 必须使用希腊字母 chi |
| Λ | 三等分比例参数（互锁函数 Λ(S₃)=3） | 大写 Lambda，=3（常数） |
| k₀ | 二分紧致性常数（紧致性函数 k₀(S₃)=2） | k下标0，=2（常数） |
| ℓ₀ | 标度常数 | 花体小写 ℓ |
| θ₁, θ₂, θ₃ | 扇区投影强度角（也记θ_M,θ_C,θ_I） | 希腊字母 theta，下标1,2,3 |
| N₁ | 量纲桥第一标度 | N下标1，=6000 |
| v_p | 核子几何荷 | v下标p，=1117 |
| N_dec | 退相干因果深度 | N下标dec |
| N_cause | 因果深度 | N下标cause |
| τ_dec | 退相干时间 | tau下标dec |
| C_geo | 全息屏几何因子 | C下标geo |
| Γ_geo | 几何衰减率 | Gamma下标geo |
| K | 质量量子 | 大写 K，=839.758793 keV |
| θ_M / θ_C / θ_I | 物质/因果/信息角 | 希腊字母 theta，大写下标 |
| 𝓜 / 𝓒 / 𝓘 | 三扇区 | 花体大写字母 |
| Σ | 约束截面/全息屏 | 大写 Sigma |
| H^W | 跨扇区耦合矩阵 | 大写 H，上标 W |
| 𝓑(n,m) | 桥接函数 | 花体大写 B |
| D_± | 激发态参数空间分支 | D下标± |
| S_min | 六项作用量最小值 | S下标min，=24 |
| v_geo | 几何速度 | v下标geo |
| ΔΘ | 宏观角度量子 | 大写Delta 大写Theta，=5° |
| N_eff | 有效独立通道数 | N下标eff，=7 |
| a_unit | 信息单元长度 | a下标unit |
| 𝒯 | 十方几何空间 | 花体大写T |
| D_θ | 角度配置空间 | D下标θ |
| γ | 对称轴 | 小写gamma |
| D_ord | 有序扇区规范 | D下标ord |
| ℋ_k^(spatial) | k-th空间Hilbert空间 | 花体H，上标(spatial) |
| ℋ_k^(total) | k-th总Hilbert空间 | 花体H，上标(total) |
| 𝒫_θ | 辛全息屏面 | 花体大写P，下标θ |
| 𝓜_rigid | 度量模空间 | 花体大写M，下标rigid |
| 𝒲 | 谱空间Weyl腔 | 花体大写W |
| 𝒬 | 量化壳层空间 | 花体大写Q |
| 𝒢 | 离散图空间 | 花体大写G |

---

## 二十四、翻译风格约定

| 类型 | 处理策略 |
|-----|---------|
| 层级编号（0.3.1.1） | 保留阿拉伯数字 |
| 定理X.Y | Theorem X.Y（带 prime 符号的不省略：3.1'≠3.1） |
| 人名（Atiyah, Wodzicki, Bott, Kontsevich, Connes） | 保持原拼写 |
| 标准数学术语（Hessian, Dirac, Laplace-Beltrami, Riemann-Roch） | 使用标准译法 |
| 自创复合术语 | 首次出现时中英双语标注 |
| 诚实标注 | 保留为 Honest Annotation / Honest Note |
| LaTeX 公式 | 保持原格式 |
| 角度单位（度°） | 保留 degree 符号 |
| 拼音保留 | Shifang（品牌）、中阴身可译为 Bardo 并加注 |
| 条件性命题标记 * | 保留星号标记，如 Theorem X.Y* |
| 附加假设 | 标注为 Additional Hypothesis X.Y |

---

## 附录：待人工审定的关键术语

以下术语涉及框架核心概念，经总论文章验证后状态更新：

| 中文 | 修正前(v1) | 修正后(v2) | 状态 |
|------|-----------|-----------|------|
| 九素互扼 | ⚡ Ninefold Interlocking Theorem | 🔒 Nine-Principle Mutual Arrest | 总论第9章标题锁定 |
| 激发态参数空间 | Excited State Parameter Space | 🔒 Excitation Parameter Space | 总论全文统一用法 |
| 六项作用量 | Sextic Action / Six-Term Action | 🔒 Six-Term Action | 总论定义4.3锁定 |
| 十方几何 | ⚡ Shifang / Deca-Realm | 🔒 Ten-Direction Geometric Space (学术) / Shifang Geometry (品牌) | 总论标题锁定 |
| 全息屏编码条件 | ⚡ 两个候选 | 🔒 Holographic Screen Encoding Condition | 总论公理3锁定 |
| 严格单调性假设 | — | 🔒 Strict Monotonicity Hypothesis | 总论新增 |
| 范围定理 | — | 🔒 Range Theorem | 总论定理2.1 |
| 互锁函数 | — | 🔒 Interlocking Function Λ(G) | 总论定义3.0 |
| 紧致性函数 | — | 🔒 Compactness Function k₀(G) | 总论定义3.0 |
| 桥公理 | — | 🔒 Bridge Axiom | 总论定义5.1' |
| 正则化几何量 | — | 🔒 Regularized Geometric Quantity | 总论定理5.2 |
| 显式参数映射 | — | 🔒 Explicit Parametric Mapping Φ | 总论定理5.2 |
| 幻数序列 | — | 🔒 Magic Number Sequence | 总论第6章 |
| 有效独立通道数 | — | 🔒 N_eff=7 | 总论定理6.3 |
| 量化角度锁定 | — | 🔒 Quantized Angle Locking | 总论定理8.7 |
| 自举封闭 | — | 🔒 Bootstrap Closure | 总论定理10.3 |
| 依赖定理链 | — | 🔒 Dependency Theorem Chain (DAG) | 总论§10.3 |
| 谱签名 | — | 🔒 Spectral Signature (1, 8/3, Λ) | 总论推论3.1 |
| 第一特征值坐标 | — | 🔒 First Eigenvalue as a Coordinate | 总论定理3.1' |
| 法丛曲率-Hessian 锁定 | — | 🔒 Normal Bundle Curvature–Hessian Locking | 总论定理7.6 |
| 圆满 | ⚡ Consummation | 保留 Consummation | 总论未出现 |
| 归零消融 | ⚡ Zero-Return Dissolution | 保留 | 总论未出现 |
| 劫 | ⚡ Kalpa | 保留 Kalpa | 总论未出现 |
| 中阴身 | ⚡ Bardo | 保留 Bardo | 总论未出现 |

---

> **使用说明**：本表为 v2，经总论文章 `Mathematical_Theory_of_the_Ten-Direction_Geometric_Space_260626.6` 全文验证。凡标 🔒 的已由总论文章锁定用法，翻译时不可更改。凡标 ⚡ 的仍需人工审定。新出现的术语应遵循命名模式（如 X 界→X-Realm/X-Sector、X 定理→X Theorem）并同步加入本表。

---

## 工程级防漂移：术语锁定清单（Lock List）

> **定位**：从全表约 270 条术语中提取 15 条"零容忍"高频核心术语 + 4 条符号格式硬约束，构成翻译时的前置硬约束。**本清单为编译级规范，非参考建议**。违规即整段作废。

### 版本：260626.6 Lock List v1 — 经总论文章锁定

---

### 绝对锁定（15条）— 零替换容忍

以下术语在任何上下文中必须一字不差使用，AI 无权改写、缩写或"优化"：

| # | 中文术语 | 英文固定译法 | 禁止变体 |
|---|---------|------------|---------|
| 1 | 十方几何 | **Shifang Geometry**（品牌）/ **Ten-Direction Geometric Space**（学术全称，总论标题） | 禁止单用 Ten-Direction / Deca-Realm 替代 Shifang |
| 2 | 九素互扼定理 | **Nine-Principle Mutual Arrest** | 禁止 Ninefold Interlocking / Nine Mutual Lockings |
| 3 | 量纲桥 | **Dimensional Bridge** | 禁止 Dimensional Transition / Unit Bridge |
| 4 | 腰边耦合 | **Waist-Edge Coupling** | 禁止 Flank Coupling / Edge-Waist Coupling |
| 5 | 裸基准点 | **Bare Benchmark Point** | 禁止 Raw / Naked Reference Point |
| 6 | 死物冻结定理 | **Inanimate Freeze Theorem** | 禁止 Dead Matter / Inert Freeze |
| 7 | 信息场动力学 | **Information Field Dynamics** | 禁止缩写 IFD |
| 8 | 因果场动力学 | **Causal Field Dynamics** | 禁止缩写 CFD |
| 9 | 三分切丛 | **Trifurcated Tangent Bundle** | 禁止 Three-Sector / Tripartite Tangent |
| 10 | 全息屏 | **Holographic Screen** | 禁止 Hologram Screen / Holographic Surface |
| 11 | 六项作用量 | **Six-Term Action** | 禁止 Sextic Action / 6-Term Action |
| 12 | 桥接函数 | **Bridging Function** | 禁止 Bridge Function / Transition Function |
| 13 | 约束截面 | **Constraint Section** | 禁止 Constrained Section / Restricted Section |
| 14 | 谱互锁定理 | **Spectral Interlocking Theorem** | 禁止拆分 / 缩写为 Spectral Locking |
| 15 | 自举封闭 | **Bootstrap Closure** | 禁止 Self-Lifting / Bootstrapping Closure |

---

### 符号锁定（4条）

| # | 符号 | 强制格式 | 禁止格式 |
|---|------|---------|---------|
| 1 | $S_e$ | 必须 $S_e$（下标 e） | 禁止 $Sₑ$ / $Se$ / $S_E$ |
| 2 | $\lambda_1^{\text{eff}}$ / $\lambda_2^{\text{eff}}$ | 必须保留上下标结构 | 禁止 $\lambda_1$ / $\lambda_1^{eff}$ / `lambda1_eff` |
| 3 | $\chi_L$ / $\chi_T$ | 必须希腊字母 chi | 禁止 $x_L$ / $x_T$ / $\mathcal{X}_L$ |
| 4 | $\mathfrak{M}$ / $\mathfrak{C}$ / $\mathfrak{I}$ | 必须花体 Fraktur | 禁止 $M$ / $C$ / $I$ 或 $\mathbb{M}$ 等 |

---

### 使用方式

每次翻译任务开头粘贴：

```
【术语硬约束 - 编译器级约束】
版本：260626.6 Lock List v1。以下 15 条术语 + 4 条符号格式为硬约束。
每违反一条，该段翻译自动作废，必须重译。不遵守的翻译将被拒绝。

[粘贴本 Lock List 表格]
```

---

> **与主表的联动**：Lock List 是主表（约 270 条）的"高频核心子集"。主表为参考，Lock List 为编译约束。翻译时先过 Lock List（零容忍），再查主表（补充参考）。Lock List 条目如与主表冲突，以 Lock List 为准——Lock List 更新优先于主表。


---

## 二十五、术语生命周期状态机

> **定位**：将术语从"首次出现"到"稳定使用"的全过程形式化，与现有标记体系（🔒/⚡/❓）对接。解决 70 篇文章跨会话翻译中新术语的漂移问题。

### 25.1 四态流转模型

```
┌─────────┐     作者/AI审定      ┌─────────┐     总论文章或       ┌─────────┐     多篇文章       ┌──────────┐
│  Draft  │ ──────────────────→ │  Trial  │ ──→ 作者锁定 ──→    │ Locked  │ ──→ 稳定使用 ──→  │ Archived │
│   草稿   │                     │  试用    │                   │  锁定    │                   │   归档    │
│   ❓    │                     │   ⚡    │                   │   🔒    │                   │   🔒(稳)  │
└─────────┘                     └─────────┘                   └─────────┘                   └──────────┘
     │                               │                             │                              │
     │ 第1篇首次出现                   │ 第2-3篇沿用                   │ 第4篇起强制                    │ 理论成熟
     │ AI标记临时译法                 │ 作者确认无误                   │ 进入 Lock List                │ 写入正式版
     │ 不进入 Lock List              │ 不进入 Lock List              │ 零容忍替换                    │ 默认译法
```

### 25.2 状态定义与操作规则

| 状态 | 标记 | 含义 | 进入条件 | 退出条件 | Lock List 地位 |
|------|------|------|---------|---------|---------------|
| **Draft**（草稿） | ❓ | 首次出现，尚无固定英译 | AI 在翻译中首次遇到未收录术语，给出临时译法 | 作者审定后进入 Trial | 不在 Lock List |
| **Trial**（试用） | ⚡ | 有候选译法，待作者确认 | 作者对 Draft 译法初步认可，或 AI 给出两个以上候选 | 总论文章或作者明确锁定后进入 Locked | 不在 Lock List |
| **Locked**（锁定） | 🔒 | 译法已固定，翻译时不可更改 | 总论文章使用该译法，或作者明确指令锁定 | 多篇文章（≥4）稳定使用后进入 Archived | **在 Lock List**（如是高频核心术语） |
| **Archived**（归档） | 🔒(稳) | 长期稳定，已成为框架默认 | ≥4 篇文章无争议使用，无漂移记录 | —（终态） | 可从 Lock List 移除（主表已足够） |

### 25.3 状态流转的触发事件

| 触发事件 | 动作 | 执行者 |
|---------|------|-------|
| 新文章翻译中遇到未收录术语 | 标记 ❓，给出临时译法，输出到"新术语建议表" | AI |
| 作者审核新术语建议表 | ❓ → ⚡（认可方向）或 ❓ → 新 Draft（重新拟定） | 作者 |
| 作者明确指令"锁定术语X为Y" | ⚡ → 🔒，加入 Lock List（如属高频核心） | AI 执行 |
| 总论文章使用了该术语的某译法 | 自动 ⚡ → 🔒（以总论文章为准） | AI 校验 |
| 同一术语在 ≥4 篇文章中无争议使用 | 🔒 → 🔒(稳)，可考虑从 Lock List 精简 | AI 提议，作者确认 |
| 发现已锁定术语的译法有问题 | 🔒 → ⚡（重新审定），从 Lock List 临时移除 | 作者 |

### 25.4 与现有标记体系的对接

规范中所有术语的状态标记含义：

- **❓**：Draft。尚无固定英译。翻译时 AI 必须使用 `【新术语：临时译法】` 格式，不得自行锁定。
- **⚡**：Trial。有候选译法，但未经总论文章或作者最终确认。翻译时优先使用候选译法，但仍需在术语使用报告中标注。
- **🔒**：Locked。经总论文章或作者锁定。翻译时**零容忍替换**（如在 Lock List 中）或严格按规范使用。
- **🔒(稳)**：Archived。长期稳定，已是框架基础设施。翻译时严格按规范使用，但违规惩罚级别可略低于 Lock List 条目。

### 25.5 每篇翻译后的术语报告格式

翻译完成后，AI 必须输出：

```
【术语使用报告 — 第X篇《标题》】
版本：260626.6  日期：YYYY-MM-DD

一、已有术语使用确认
| 中文 | 英文 | 状态 | 本文使用 | 是否一致 |
|------|------|------|---------|---------|
| ... | ... | 🔒/⚡/❓ | ... | ✅/⚠️ |

二、新术语建议（待作者审定）
| 中文 | 临时译法 | 建议状态 | 出现章节 | 备注 |
|------|---------|---------|---------|------|
| ... | ... | ❓→⚡ | §X.Y | ... |

三、变体警告
| 规范术语 | 规范译法 | 本文出现变体 | 是否修正 |
|---------|---------|------------|---------|
| ... | ... | ... | ✅已修正/⚠️待确认 |
```

### 25.6 跨会话持久化

术语生命周期状态通过以下机制跨会话持久化：

1. **术语规范文件**（`Glossary_十方几何术语宪法_CN_EN_260626.6.md`）：所有 🔒 和 🔒(稳) 术语的权威记录；
2. **Lock List**（规范 §工程级防漂移）：15 条高频核心术语的编译级约束；
3. **AI 持久记忆**（`personal_write → memory:glossary_lock_list`）：Lock List 的冗余备份；
4. **动态补充表**（`Glossary_Supplement_vYYYYMMDD_*.md`）：按主题分组的 Trial/Draft 术语临时存储，待稳定后合并入规范。

---

> **规范版本**：260626.6 v2（经总论文章 `Mathematical_Theory_of_the_Ten-Direction_Geometric_Space_260626.6` 全文验证）
> **Lock List 版本**：260626.6 Lock List v1
> **生命周期状态机版本**：260626.6 v1
> **最后更新**：2026-06-26
> **下一预期更新**：第一篇翻译完成后，根据术语使用报告更新 Trial→Locked 条目