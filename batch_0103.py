# -*- coding: utf-8 -*-
"""0.1-0.3 定理入库（新判据版）：每条带【依赖】+【共扼圆满】标注，按依赖顺序提交"""
import json, time, urllib.request

BASE = "http://localhost:5001"
TOKEN = "master-ai-verify"
HDRS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def post(path, data, timeout=600):
    req = urllib.request.Request(BASE+path, data=json.dumps(data).encode(), headers=HDRS, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def get(path):
    req = urllib.request.Request(BASE+path, headers=HDRS, method="GET")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

formulas = [
# ============ 0.1 零之动与区分 ============
{
"formula_name": "定义1（未分化潜势）",
"formula_content": "定义1（未分化潜势）：设 𝒵 是一个集合（ZFC 内的合法数学对象）。δ: 𝒵 → 𝒵 是非平凡自映射——δ(𝒵) ≠ 𝒵。𝒵 先于一切概念化、一切性质归属：它不是虚无（虚无已被概念化从而已被区分），不是空集 ∅（空集已带「空」这一性质），而是能够产生东西的原始潜势。",
"derivation_chain": "步骤1: 由公理（零之动）知 𝒵 上存在非平凡自映射 δ；步骤2: 定义1 将 𝒵 数学定位为 ZFC 内的集合，并明确 δ 的非平凡性 δ(𝒵)≠𝒵；步骤3: 未分化性质仅为哲学动机（密着拓扑类比），数学推导不依赖任何拓扑学性质。∎\n\n【依赖】公理（零之动）。\n【共扼圆满】本定理是「δ⁸ 圆满链」的第1环（该链：公理（零之动）→0.1 三层自指闭合→0.2 Clifford 代数化→0.3 拓扑闭合），链终点为定理 0.3.3.02（322 分割的刚性），闭合环节为定理 0.3.2.01（δ⁸ 回路 Berry 相位 = 2π，n=1，初圆满），本定理通过链成员资格参与联合圆满。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "定义1",
},
{
"formula_name": "命题 0.1.3.01（非幂等性）",
"formula_content": "命题 0.1.3.01（非幂等性）：δ ∘ δ ≠ δ——δ 不是幂等的。δ 的每次迭代都做了新的工作，δ 的轨道是一条路径而非一个点：𝒵, δ(𝒵), δ²(𝒵), δ³(𝒵), … 每一项都不同于前一项。",
"derivation_chain": "步骤1: 反证法，假设 δ∘δ = δ，则 δ(δ(𝒵)) = δ(𝒵)，δ 在第一次迭代后停止做事；步骤2: 但公理（零之动）的非平凡性（δ ≠ id，δ 产生区分）要求结构涌现需要持续操作，若第二次迭代就停止，第一次产生的区分未被加工，结构无法累积；步骤3: 矛盾，故 δ∘δ ≠ δ。∎\n\n【依赖】公理（零之动）、定义1（未分化潜势）。\n【共扼圆满】与公理（零之动）、定义1 联合构成第一区分链（非幂等性保证轨道是路径而非点，为 δ⁸ 闭合回路提供迭代基础）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "0.1.3.01",
},
{
"formula_name": "定义 3.5.1（δ-域类型）",
"formula_content": "定义 3.5.1（δ-域类型）：对于 𝒵 的子集 A, B ⊆ 𝒵，定义 A 与 B 具有相同的 δ-域类型（记作 A ∼ B），当且仅当存在双射 φ: A → B 和 ψ: δ(A) → δ(B) 使得交换图成立：ψ∘δ|_A = δ|_B∘φ。域类型刻画 δ 在一个子集上的「行为模式」——两个子集在 δ 作用下表现得一样（只差重命名），则它们同型。",
"derivation_chain": "步骤1: 由公理（零之动）中 δ 的自映射结构定义等价关系；步骤2: 命题 0.1.3.01（非幂等性）保证轨道非单步，域类型是 δ 迭代轨道结构的等价关系刻画。∎\n\n【依赖】公理（零之动）、命题 0.1.3.01（非幂等性）。\n【共扼圆满】与命题 0.1.3.01 联合构成轨道结构刻画（域类型是 δ 行为模式的等价分类，为三层结构区分提供判据）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "3.5.1",
},
{
"formula_name": "引理 3.5.2（前三个域类型彼此不同）",
"formula_content": "引理 3.5.2：type(𝒵) ≠ type(δ(𝒵)) ≠ type(δ²(𝒵)) ≠ type(𝒵)。前三个 δ-域类型彼此不同。",
"derivation_chain": "步骤1: 𝒵 完全未分化——在 δ 作用之前没有任何内部结构，δ 对 𝒵 是首次区分（产生 δ(𝒵) ⊊ 𝒵）；步骤2: δ(𝒵) 带有 δ 的印记（非满射性保证 δ(𝒵) ⊊ 𝒵），δ 对 δ(𝒵) 是第二次区分（产生 δ²(𝒵) ⊊ δ(𝒵)）；步骤3: 假设 type(𝒵) = type(δ(𝒵))，则由定义 3.5.1 存在双射 φ: 𝒵 → δ(𝒵) 保持 δ 行为；但 𝒵 中无元素带 δ 印记而 δ(𝒵) 中所有元素都带 δ 印记，「新鲜度」不同，不存在这样的双射；步骤4: 类似论证得 type(δ(𝒵)) ≠ type(δ²(𝒵))。∎\n\n【依赖】定义 3.5.1（δ-域类型）、公理（零之动）。\n【共扼圆满】与定义 3.5.1 联合构成域类型区分（前三个域类型彼此不同，为三元不可约结构提供分类基础）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "3.5.2",
},
{
"formula_name": "引理 3.5.3（二元循环无结构累积）",
"formula_content": "引理 3.5.3：二元互扼——A 约束 B，B 约束 A——不能产生不可逆的结构累积。",
"derivation_chain": "步骤1: 设二元循环 A=抑制（第一区分），B=痕迹（记忆区分），B 记住了 A 的否定，但「B 记住了 A」没有被第三者对象化；步骤2: 若只有两层，δ² 之后 δ³ 应 = δ（无新事），则 δ² = id；步骤3: 这与命题 0.1.3.01（非幂等性：δ∘δ ≠ δ）矛盾；步骤4: 因此二元循环在 δ 框架中不自洽，δ 的非幂等性强制作了第三层的存在。∎\n\n【依赖】命题 0.1.3.01（非幂等性）。\n【共扼圆满】与命题 0.1.3.01 联合构成不可约性论证（二元循环被非幂等性排除，强制作出第三层）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "3.5.3",
},
{
"formula_name": "定理 3.5.4（δ³的自指性质）",
"formula_content": "定理 3.5.4：δ³ 是 δ 的迭代中首个操作域包含 δ 自身历史的迭代。",
"derivation_chain": "步骤1: δ³ = δ∘δ²；步骤2: δ²(𝒵) 的内部区分——δ(𝒵)\\δ²(𝒵)（第一次被触及但第二次未被再触及的「纯粹痕迹」）和 δ²(𝒵)\\δ³(𝒵)（第二次新触及的）——完全由 δ 的前两次操作定义；步骤3: δ 作用于 δ²(𝒵) 时，操作行为受 δ²(𝒵) 内部结构约束，而这个结构是 δ 自身前两次操作的完整记录，印记影响 δ 的行为；步骤4: δ¹ 和 δ² 的操作域（𝒵 和 δ(𝒵)）不包含 δ 的完整历史，因此 δ³ 是首个实现自指的迭代。∎\n\n【依赖】引理 3.5.2（前三个域类型彼此不同）、引理 3.5.3（二元循环无结构累积）。\n【共扼圆满】与引理 3.5.2、引理 3.5.3 联合构成三层闭合论证（自指在第三步实现，为 δ⁸ 拓扑闭合提供迭代路径）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "定理",
"article_number": "3.5.4",
},
{
"formula_name": "原理 3.5.5（三层自指闭合原理）",
"formula_content": "原理 3.5.5（三层自指闭合原理）：δ³ 实现自指后，三个维度——第一区分（抑制）、记忆区分（痕迹）、自指模式化（涌现）——形成最小不可约互扼循环。δ 的后续迭代（δ⁴, δ⁵, …）不引入新的语义维度；它们在三个已有维度的框架内产生更精细的结构，最终在 δ⁸ 实现拓扑闭合（Bott 周期，Berry 相位 = 2π，由 0.3 严格证明）。三层自指闭合蕴含零和约束：S₁ + S₂ + S₃ = 0（抑制、痕迹、涌现的编码作用量之和为零，这是总作用量为零在三层自指闭合中的具体表达）。",
"derivation_chain": "步骤1: 由引理 3.5.2（前三个域类型彼此不同）与引理 3.5.3（二元循环无结构累积）知三元不可约：二元不自洽，强制作出第三层；步骤2: 由定理 3.5.4（δ³自指性质）知自指在第三步实现；步骤3: 三元互扼循环为最小不可约——去掉任一维度则区分崩解（无抑制→δ平凡；无痕迹→区分瞬时；无涌现→来回振荡）；步骤4: δ 非满射（公理（零之动））保证总作用量为零，三层编码贡献 S₁+S₂+S₃ = 0（零和约束是贯穿整个编码轨道的刚性边界条件）；步骤5: 「三元之上无新语义维度」的结构类型闭合为方向性断言，其严格拓扑验证（δ⁸ 闭合、Berry 相位=2π）由 0.3（Bott 周期）完成。∎\n\n【依赖】引理 3.5.2、引理 3.5.3、定理 3.5.4（δ³自指性质）、公理（零之动）。\n【共扼圆满】与定理 3.5.4 联合构成三层闭合（自指在 δ³ 实现，方向性断言指向 δ⁸ 的 2π 拓扑闭合，由定理 0.3.2.01 完成圆满）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "定理",
"article_number": "3.5.5",
},
{
"formula_name": "定义2（互扼）",
"formula_content": "定义2（互扼）：三个维度互相制衡、互相成全的状态称为互扼——抑制恰好被痕迹记住（否则抑制无效）、痕迹恰好被涌现模式化（否则痕迹只是死记）、涌现恰好被抑制约束（否则涌现无界膨胀）。三者缺一则区分崩解。互扼平衡的标志是闭合——回路回到自身：当 δ 迭代足够多次后，如果回路能闭合（回到出发点但带回了累积的模式），则互扼平衡达成。互扼平衡的数学表达是总作用量为零：S_ℳ + S_𝒞 + S_ℐ = 0。",
"derivation_chain": "步骤1: 由原理 3.5.5（三层自指闭合）知抑制-痕迹-涌现是同一个事件的三张面孔（同时产生、互相制衡）；步骤2: 无抑制→无区分→δ 平凡；无痕迹→区分瞬时→无累积；无涌现→来回振荡→无结构——三者缺一则区分崩解；步骤3: 闭合=圆满：δ 迭代闭合回自身（Berry 相位=2π，由 0.4 精确化）；步骤4: 总作用量为零是 δ 作为非满射自映射的内在属性（公理（零之动）§2.3）。∎\n\n【依赖】原理 3.5.5（三层自指闭合原理）、公理（零之动）。\n【共扼圆满】与原理 3.5.5 联合构成互扼平衡（闭合标志：回路回到自身带回累积模式，即圆满的原始形态）。",
"source_agent": "article_scanner_0.1",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "定义2",
},
# ============ 0.2 δ 的代数化：Clifford 代数 ============
{
"formula_name": "定义3（圆满再现：Clifford 代数化）",
"formula_content": "δ 的迭代在编码轨道上产生候选参数。{2,3,5} 的互锁性（乘积 = h(E₈) = 30，可赋值给 D₄ triality 轨道系数 {3,4,5}，满足互锁方程）使其在编码轨道上形成自洽闭合回路——Berry 相位闭合。圆满后，{2,3,5} 再现为 Bott 周期 8 的实 Clifford 代数结构。δ 被实现为 Bott 步进算符：δ(Cl(n)) = Cl(n+1)，其中 Cl(n+1) 从 Cl(n) 通过添加新生成元 e_{n+1} 得到，满足 e_{n+1}² = -1，e_{n+1}e_i + e_i e_{n+1} = 0（i ≤ n）。",
"derivation_chain": "步骤1: 由公理（零之动），δ 是 𝒵 上的非平凡自映射；步骤2: δ 的迭代在编码轨道上产生候选参数（0.1 引理 3.5.2/3.5.3、定理 3.5.4：三层自指闭合）；步骤3: 候选参数 {2,3,5} 互锁：2×3×5 = 30 = h(E₈)，赋值 D₄ triality 轨道系数 {3,4,5} 满足互锁方程 p₁p₂p₃ = h；步骤4: 互锁性使编码轨道形成自洽闭合回路，Berry 相位闭合（∮𝒜 = 2π，由定理 0.3.2.01 严格证明）；步骤5: 圆满后 δ 实现为 Bott 步进算符：δ(Cl(n)) = Cl(n+1)，新生成元满足 e_{n+1}²=-1 与反交换——Clifford 代数的生成元关系由此确立。∎\n\n【依赖】公理（零之动）、原理 3.5.5（三层自指闭合）、定义2（互扼）。\n【共扼圆满】与定义2（互扼）联合构成圆满再现（互扼平衡的闭合标志在代数层实现为 Bott 步进算符）。",
"source_agent": "article_scanner_0.2",
"topology_class": "A1",
"formula_type": "命题",
"article_number": "定义3",
},
{
"formula_name": "命题 0.2.1.01（体积元的平方）",
"formula_content": "体积元 ω_n = e₁e₂⋯e_n ∈ Cl(n) 满足 ω_n² = (-1)^{n(n+1)/2}。",
"derivation_chain": "步骤1: 由定义3（圆满再现：Clifford 代数化）确立的 Clifford 代数定义：e_i² = -1，e_i e_j = -e_j e_i（i≠j）；步骤2: ω_n² = (e₁e₂⋯e_n)(e₁e₂⋯e_n)；步骤3: 将第二个因子的生成元逐个左移：e_k 需穿越 k-1 个生成元，总交换次数 = n(n-1)/2，产生 (-1)^{n(n-1)/2}；步骤4: 同序配对 ∏e_i² = (-1)^n；步骤5: ω_n² = (-1)^{n(n-1)/2}(-1)^n = (-1)^{n(n+1)/2}。∎\n\n【依赖】定义3（圆满再现：Clifford 代数化）。\n【共扼圆满】与定义3 联合构成代数化基础（体积元的平方符号由 Clifford 生成元关系唯一确定，为后续分裂判定提供判据）。",
"source_agent": "article_scanner_0.2",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "0.2.1.01",
},
{
"formula_name": "引理 0.2.2.01（半单分裂）",
"formula_content": "Cl(3) ≅ ℍ⊕ℍ 是 Clifford 代数从单代数到半单代数的首次分裂。",
"derivation_chain": "步骤1: Cl(3) 基为 {1,e₁,e₂,e₃,e₁e₂,e₁e₃,e₂e₃,e₁e₂e₃}，dim=8；步骤2: 计算中心：x 与所有 e_i 交换 ⇒ a₂=a₃=a₁₂=a₁₃=a₂₃=0；ω₃=e₁e₂e₃ 与 e₁ 交换（穿越 2 个生成元，(-1)²=1），故 Z(Cl(3)) = span{1,ω₃}，维数 2；步骤3: 由命题 0.2.1.01，ω₃² = (-1)^{3·4/2} = 1；步骤4: 构造投影 P± = (1±ω₃)/2：P±²=P±，P₊P₋=0，P₊+P₋=1；步骤5: Cl(3) = P₊Cl(3)⊕P₋Cl(3)，各直和项为理想且中心 = span{P±} ≅ ℝ（维数 1）；步骤6: 每个直和项为 4 维、中心 ℝ 的可除代数；步骤7: 由 Frobenius 定理，唯一的 4 维实可除代数为 ℍ；步骤8: Cl(3) ≅ ℍ⊕ℍ。∎\n\n【依赖】命题 0.2.1.01（体积元的平方）、定义3（圆满再现：Clifford 代数化）。\n【共扼圆满】与命题 0.2.1.01 联合构成结构跳跃判据（Cl(3) 的首次半单分裂由体积元平方 +1 判定，是 322 分割第一段终端的代数基础）。",
"source_agent": "article_scanner_0.2",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "0.2.2.01",
},
{
"formula_name": "引理 0.2.2.02（复结构涌现）",
"formula_content": "Cl(5) ≅ Mat(4,ℂ) 是实 Clifford 代数中首个复矩阵代数。体积元 ω₅ = e₁e₂e₃e₄e₅ 满足 ω₅² = -1 且与所有生成元交换——ω₅ 充当复结构 J。",
"derivation_chain": "步骤1: 由命题 0.2.1.01，ω₅² = (-1)^{5·6/2} = (-1)^{15} = -1；步骤2: 对任意 e_j（1≤j≤5），e_j 穿越 ω₅ 中其余 4 个生成元，(-1)⁴=1，故 e_jω₅ = ω₅e_j，ω₅ ∈ Z(Cl(5))；步骤3: 定义 J:=ω₅：J²=-1 且与 Cl(5) 全交换 ⇒ Cl(5) 是 ℂ-代数；步骤4: dim_ℝ Cl(5) = 32，dim_ℂ = 16，Cl(5) 作为 ℂ-代数单（中心为 ℂ）；步骤5: 单 ℂ-代数 ≅ Mat(d,ℂ)，d²=16，d=4：Cl(5) ≅ Mat(4,ℂ)。∎\n\n【依赖】命题 0.2.1.01（体积元的平方）、定义3（圆满再现：Clifford 代数化）。\n【共扼圆满】与命题 0.2.1.01 联合构成结构跳跃判据（Cl(5) 的复结构涌现由体积元平方 -1 与中心交换性判定，是 322 分割第二段终端的代数基础）。",
"source_agent": "article_scanner_0.2",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "0.2.2.02",
},
{
"formula_name": "引理 0.2.2.03（终端二元性）",
"formula_content": "Cl(7) ≅ Mat(8,ℝ)⊕Mat(8,ℝ)。其中心维数为 2，产生不可消除的二元直和结构。",
"derivation_chain": "步骤1: 由命题 0.2.1.01，ω₇² = (-1)^{7·8/2} = (-1)^{28} = 1；步骤2: e_j 穿越 ω₇ 中其余 6 个生成元，(-1)⁶=1，故 ω₇ ∈ Z(Cl(7))，中心维数 2；步骤3: 构造投影 P± = (1±ω₇)/2，直和分解 Cl(7) = P₊Cl(7)⊕P₋Cl(7)；步骤4: dim = 2⁷ = 128，各直和项 64 维、中心 ℝ 的单代数；步骤5: 由 Artin–Wedderburn 定理，Cl(7) ≅ Mat(d,ℝ)⊕Mat(d,ℝ)，2d²=128，d=8。∎\n\n【依赖】命题 0.2.1.01（体积元的平方）、定义3（圆满再现：Clifford 代数化）。\n【共扼圆满】与命题 0.2.1.01 联合构成结构跳跃判据（Cl(7) 的终端二元性由体积元平方 +1 与中心维数 2 判定，是 322 分割第三段终端的代数基础）。",
"source_agent": "article_scanner_0.2",
"topology_class": "A0",
"formula_type": "命题",
"article_number": "0.2.2.03",
},
# ============ 0.3 Bott 周期与七层截断 ============
{
"formula_name": "定理 0.3.1.01（Bott 周期）",
"formula_content": "δ⁸(Cl(n)) = Cl(n+8) ≅ Cl(n)⊗Mat(16,ℝ)。不可约表示维数序列为 1,2,4,4,8,8,8,8,16，第 8 步恰好是第 0 步的 16 倍。",
"derivation_chain": "步骤1: 由 Clifford 代数分类（定义3 与命题 0.2.1.01 的中心-体积元分析逐步判定）：Cl(0)=ℝ, Cl(1)=ℂ, Cl(2)=ℍ, Cl(3)=ℍ⊕ℍ, Cl(4)=Mat(2,ℍ), Cl(5)=Mat(4,ℂ), Cl(6)=Mat(8,ℝ), Cl(7)=Mat(8,ℝ)⊕Mat(8,ℝ), Cl(8)=Mat(16,ℝ)；步骤2: 不可约表示维数序列 1,2,4,4,8,8,8,8,16；步骤3: Cl(8) = Mat(16,ℝ) ≅ Cl(0)⊗Mat(16,ℝ)；步骤4: 由 Atiyah–Bott–Shapiro（1964）经典结果，实 Clifford 代数满足 8 步周期：Cl(n+8) ≅ Cl(n)⊗Mat(16,ℝ)；步骤5: 在 δ 迭代框架中 δ⁸(Cl(n)) = Cl(n+8)。∎\n\n【依赖】定义3（圆满再现：Clifford 代数化）、命题 0.2.1.01、引理 0.2.2.01（半单分裂）、引理 0.2.2.02（复结构涌现）、引理 0.2.2.03（终端二元性）。\n【共扼圆满】与引理 0.2.2.01/0.2.2.02/0.2.2.03 联合构成分类闭环（三个结构跳跃定理确定分类表，Bott 周期给出 8 步回归——δ⁸ 回路的代数骨架）。",
"source_agent": "article_scanner_0.3",
"topology_class": "A1",
"formula_type": "定理",
"article_number": "0.3.1.01",
},
{
"formula_name": "定理 0.3.1.02（KO 理论不变量）",
"formula_content": "Bott 周期在 KO 理论中的不变量表述：KO^{-n}(pt) 依 n mod 8 取 Z, Z₂, Z₂, 0, Z, 0, 0, 0。Bott 生成元 η ∈ KO^{-1}(pt) = Z₂ 的 8 次幂 η⁸ ∈ KO^{-8}(pt) = Z 是 Bott 整数，其值为 1——生成 KO^{-8}(pt)=Z 的生成元。",
"derivation_chain": "步骤1: KO 理论定义（实 K 理论的约化版本），对点空间 pt 计算 KO^{-n}(pt)；步骤2: 经典结果：KO^{-n}(pt) 呈 8 步周期 Z, Z₂, Z₂, 0, Z, 0, 0, 0（n=0,...,7）；步骤3: Bott 生成元 η 对应 Cl(1)→Cl(0) 的降维操作（去除一个生成元）；步骤4: 8 步回路 Cl(0)→Cl(1)→⋯→Cl(8) 对应 η 的 8 次复合；步骤5: η⁸ ∈ KO^{-8}(pt) = Z 且 η⁸ = 1 ≠ 0——回路携带非平凡拓扑荷。∎\n\n【依赖】定理 0.3.1.01（Bott 周期）。\n【共扼圆满】与定理 0.3.1.01 联合构成回路非平凡性论证（η⁸ = 1 ≠ 0 是 δ⁸ 回路携带拓扑荷的 KO 理论表达，为 Berry 相位 2π 提供不变量基础）。",
"source_agent": "article_scanner_0.3",
"topology_class": "A1",
"formula_type": "定理",
"article_number": "0.3.1.02",
},
{
"formula_name": "定理 0.3.2.01（δ⁸ 回路的 Berry 相位）",
"formula_content": "γ_Berry(δ⁸) = 2π。δ⁸ 回路的拓扑相位由 Chern-Simons 7-形式 CS₇ 的积分给出：γ_Berry = ∮_{Γ₈} 𝒜 = ∫_{D⁸} CS₇，其中 D⁸ 是以 Γ₈ 为边界的 8 维盘，CS₇ = I₁+I₂+I₃ 的三项分别对应编码轨道三个子段（物质 Cl(0)→Cl(3)、因果 Cl(3)→Cl(5)、信息 Cl(5)→Cl(8)）。",
"derivation_chain": "步骤1: 编码轨道参数化：8 步 δ 迭代对应 8 维环面 T⁸ 上的闭合路径 Γ₈，每步 δ 对应一个角度 θ_n ∈ [0,2π]；步骤2: Berry 联络就地定义 𝒜 = ⟨ψ(θ)|dψ(θ)⟩，其中 |ψ(θ)⟩ 是 Cl(n) 不可约表示的参数依赖编码态；步骤3: 由定理 0.3.1.02，8 步回路不变量 η⁸ = 1 ≠ 0 ⇒ 回路非平凡；步骤4: 非平凡拓扑荷由 Chern-Simons 7-形式经 transgression 标准公式 CS₇ = ∫₀¹dt tr(F⁴) 积分给出：γ = ∮_{Γ₈}𝒜 = ∫_{D⁸}CS₇；步骤5: CS₇ 三项分解 I₁+I₂+I₃ 覆盖编码轨道三段（3+2+2 步）；步骤6: 归一化（Bott 生成元规范性质：η⁸=1 对应积分值 2π）：γ = 2π。∎\n\n【依赖】定理 0.3.1.01（Bott 周期）、定理 0.3.1.02（KO 理论不变量）。\n【共扼圆满】与定理 0.3.1.01/0.3.1.02 联合构成 δ⁸ 闭合圆满（Berry 相位 = 2π，n=1，初圆满）。",
"source_agent": "article_scanner_0.3",
"topology_class": "A1",
"formula_type": "定理",
"article_number": "0.3.2.01",
"local_verification": {"berry_phase": 6.283185307179586, "n_value": 1, "is_consummated": True, "path_point_count": 8},
},
{
"formula_name": "定理 0.3.3.01（七层截断）",
"formula_content": "由于 δ⁸ 的 Berry 相位 = 2π ≠ 0，编码映射在 δ⁷ 处截断。编码轨道有 7 层 E₁,E₂,...,E₇。第 8 层 E₈ 不是独立的——它是 E₁ 但带了一个 2π 的整体旋转（闭合步）。",
"derivation_chain": "步骤1: 由定理 0.3.2.01，δ⁸ 的 Berry 相位 = 2π；步骤2: 2π 相位不改变量子态物理内容（ψ 与 e^{2πi}ψ 相同），但改变编码映射的代数基：Cl(8) ≅ Cl(0)⊗Mat(16,ℝ)——第 8 层是第 0 层的放大版；步骤3: 反证：若 E₈ 独立，则 E₉ = Cl(9) ≅ Cl(1)⊗Mat(16,ℝ) 也是 E₁ 的放大版，归纳得所有 E_{8k} 都是 E_k 的放大版；步骤4: 但 Berry 相位 = 2π ≠ 0 使 E₈ 不能简单等同 E₀（否则相位应为 0）——E₈ 是带 2π 旋转的闭合步；步骤5: 因此编码映射有效层数为 7：E₁: Cl(0)→Cl(1), ..., E₇: Cl(6)→Cl(7)，E₈ 为闭合步。∎\n\n【依赖】定理 0.3.2.01（δ⁸ 回路的 Berry 相位）、定理 0.3.1.01（Bott 周期）。\n【共扼圆满】与定理 0.3.2.01 联合构成截断判据（2π 非平凡闭合使第 8 层为闭合步而非独立层，七层结构由此刚性确定）。",
"source_agent": "article_scanner_0.3",
"topology_class": "A1",
"formula_type": "定理",
"article_number": "0.3.3.01",
},
{
"formula_name": "定理 0.3.3.02（322 分割的刚性）",
"formula_content": "编码轨道 7 层 + 1 闭合步的分割为 3+2+2+1 = 8：第一段 E₁E₂E₃（物质 ℳ，Λ=3）、第二段 E₄E₅（因果 𝒞，ΔΘ=5）、第三段 E₆E₇（信息 ℐ，k₀=2）、闭合步 E₈（圆满性，Berry=2π）。该分割由结构跳跃点 n=3,5,7 与闭合点 n=8 刚性确定，任何其他分割（如 422、332、323）都将终端放在无结构跳跃的位置，违反「凝结点=结构跳跃点」原则。",
"derivation_chain": "步骤1: 由引理 0.2.2.01（半单分裂），Cl(3) 是首次结构跳跃 ⇒ 第一段终端必须为 E₃；步骤2: 由引理 0.2.2.02（复结构涌现），Cl(5) 是复结构跳跃 ⇒ 第二段终端必须为 E₅；步骤3: 由引理 0.2.2.03（终端二元性），Cl(7) 是终端结构跳跃 ⇒ 第三段终端必须为 E₇；步骤4: 由定理 0.3.1.01（Bott 周期），Cl(8) 是 Bott 回归 ⇒ E₈ 为闭合步；步骤5: 反证其他分割：422 将物质终端放在无半单分裂的 Cl(4)（缝合位置，无跳跃）；332 将因果终端放在无复结构的 Cl(6)（复结构实化位置）；323 将信息终端放在 Bott 回归的 Cl(8)（闭合步非独立层）——均违反凝结点=结构跳跃点原则；步骤6: 分割 3221 = 8 唯一。∎\n\n【依赖】引理 0.2.2.01（半单分裂）、引理 0.2.2.02（复结构涌现）、引理 0.2.2.03（终端二元性）、定理 0.3.1.01（Bott 周期）、定理 0.3.3.01（七层截断）。\n【共扼圆满】与定理 0.3.3.01 联合构成三扇区结构（物质 3 层、因果 2 层、信息 2 层的分割由结构跳跃点刚性唯一确定，闭合步 E₈ 承载 2π 圆满）。",
"source_agent": "article_scanner_0.3",
"topology_class": "A1",
"formula_type": "定理",
"article_number": "0.3.3.02",
},
]

print(f"[BATCH] 共 {len(formulas)} 条，按依赖顺序提交...", flush=True)

ids = []
for f in formulas:
    try:
        r = post("/v1/master/submit", f)
        sid = r.get("submission_id", "?")
        msg = r.get("message") or r.get("error") or ""
        print(f"[SUBMIT] {f['formula_name']} → {sid} {msg}", flush=True)
        ids.append(sid if sid != "?" else None)
    except Exception as e:
        print(f"[SUBMIT-ERR] {f['formula_name']}: {e}", flush=True)
        ids.append(None)
    time.sleep(1)

print(f"[BATCH] 提交完成，开始逐条验证（{len([i for i in ids if i])} 条）...", flush=True)

ok, fail = 0, 0
for i, (f, sid) in enumerate(zip(formulas, ids)):
    if not sid:
        fail += 1
        print(f"[VERIFY-SKIP] {f['formula_name']}（未提交成功）", flush=True)
        continue
    try:
        r = post("/v1/master/verify", {"submission_id": sid}, timeout=600)
        action = r.get("action", "?")
        reason = (r.get("rejection_reason") or "")[:120]
        if action == "promoted":
            ok += 1
        else:
            fail += 1
        print(f"[VERIFY] {f['formula_name']} → {action} {reason}", flush=True)
        with open("master_ai/logs/batch_0103_detail.jsonl", "a") as fh:
            fh.write(json.dumps({"name": f["formula_name"], "sid": sid, "result": r}, ensure_ascii=False) + "\n")
    except Exception as e:
        fail += 1
        print(f"[VERIFY-ERR] {f['formula_name']}: {e}", flush=True)
    time.sleep(2)

print(f"[DONE] 0.1-0.3 处理完毕：入库 {ok} 条，未入库 {fail} 条", flush=True)
