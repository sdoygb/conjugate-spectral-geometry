# -*- coding: utf-8 -*-
"""批量提交 0.2-0.5 系列定理到主库AI（17条）"""
import json, time, urllib.request, sys

BASE = "http://localhost:5001"
TOKEN = "master-ai-verify"
HDRS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def post(path, data, timeout=300):
    req = urllib.request.Request(BASE+path, data=json.dumps(data).encode(), headers=HDRS, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def get(path):
    req = urllib.request.Request(BASE+path, headers=HDRS, method="GET")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

formulas = [
# ============ 0.2 Clifford 代数化 ============
{
"formula_name": "命题 0.2.1.01（体积元的平方）",
"formula_content": "体积元 ω_n = e₁e₂⋯e_n ∈ Cl(n) 满足 ω_n² = (-1)^{n(n+1)/2}。",
"derivation_chain": "步骤1: 由 Clifford 代数定义（0.2 §1.2）：e_i² = -1，e_i e_j = -e_j e_i（i≠j）；步骤2: ω_n² = (e₁e₂⋯e_n)(e₁e₂⋯e_n)；步骤3: 将第二个因子的生成元逐个左移：e_k 需穿越 k-1 个生成元，总交换次数 = n(n-1)/2，产生 (-1)^{n(n-1)/2}；步骤4: 同序配对 ∏e_i² = (-1)^n；步骤5: ω_n² = (-1)^{n(n-1)/2}(-1)^n = (-1)^{n(n+1)/2}。∎",
"topology_class": "A0", "formula_type": "命题", "article_number": "0.2.1.01",
"source_agent": "article_scanner_0.2"
},
{
"formula_name": "引理 0.2.2.01（半单分裂）",
"formula_content": "Cl(3) ≅ ℍ⊕ℍ 是 Clifford 代数从单代数到半单代数的首次分裂。",
"derivation_chain": "步骤1: Cl(3) 基为 {1,e₁,e₂,e₃,e₁e₂,e₁e₃,e₂e₃,e₁e₂e₃}，dim=8；步骤2: 计算中心：x 与所有 e_i 交换 ⇒ a₂=a₃=a₁₂=a₁₃=a₂₃=0；ω₃=e₁e₂e₃ 与 e₁ 交换（穿越 2 个生成元，(-1)²=1），故 Z(Cl(3)) = span{1,ω₃}，维数 2；步骤3: 由命题 0.2.1.01，ω₃² = (-1)^{3·4/2} = 1；步骤4: 构造投影 P± = (1±ω₃)/2：P±²=P±，P₊P₋=0，P₊+P₋=1；步骤5: Cl(3) = P₊Cl(3)⊕P₋Cl(3)，各直和项为理想且中心 = span{P±} ≅ ℝ（维数 1）；步骤6: 每个直和项为 4 维、中心 ℝ 的可除代数；步骤7: 由 Frobenius 定理，唯一的 4 维实可除代数为 ℍ；步骤8: Cl(3) ≅ ℍ⊕ℍ。∎",
"topology_class": "A0", "formula_type": "命题", "article_number": "0.2.2.01",
"source_agent": "article_scanner_0.2"
},
{
"formula_name": "引理 0.2.2.02（复结构涌现）",
"formula_content": "Cl(5) ≅ Mat(4,ℂ) 是实 Clifford 代数中首个复矩阵代数。体积元 ω₅ = e₁e₂e₃e₄e₅ 满足 ω₅² = -1 且与所有生成元交换——ω₅ 充当复结构 J。",
"derivation_chain": "步骤1: 由命题 0.2.1.01，ω₅² = (-1)^{5·6/2} = (-1)^{15} = -1；步骤2: 对任意 e_j（1≤j≤5），e_j 穿越 ω₅ 中其余 4 个生成元，(-1)⁴=1，故 e_jω₅ = ω₅e_j，ω₅ ∈ Z(Cl(5))；步骤3: 定义 J:=ω₅：J²=-1 且与 Cl(5) 全交换 ⇒ Cl(5) 是 ℂ-代数；步骤4: dim_ℝ Cl(5) = 32，dim_ℂ = 16，Cl(5) 作为 ℂ-代数单（中心为 ℂ）；步骤5: 单 ℂ-代数 ≅ Mat(d,ℂ)，d²=16，d=4：Cl(5) ≅ Mat(4,ℂ)。∎",
"topology_class": "A0", "formula_type": "命题", "article_number": "0.2.2.02",
"source_agent": "article_scanner_0.2"
},
{
"formula_name": "引理 0.2.2.03（终端二元性）",
"formula_content": "Cl(7) ≅ Mat(8,ℝ)⊕Mat(8,ℝ)。其中心维数为 2，产生不可消除的二元直和结构。",
"derivation_chain": "步骤1: 由命题 0.2.1.01，ω₇² = (-1)^{7·8/2} = (-1)^{28} = 1；步骤2: e_j 穿越 ω₇ 中其余 6 个生成元，(-1)⁶=1，故 ω₇ ∈ Z(Cl(7))，中心维数 2；步骤3: 构造投影 P± = (1±ω₇)/2，直和分解 Cl(7) = P₊Cl(7)⊕P₋Cl(7)；步骤4: dim = 2⁷ = 128，各直和项 64 维、中心 ℝ 的单代数；步骤5: 由 Artin–Wedderburn 定理，Cl(7) ≅ Mat(d,ℝ)⊕Mat(d,ℝ)，2d²=128，d=8。∎",
"topology_class": "A0", "formula_type": "命题", "article_number": "0.2.2.03",
"source_agent": "article_scanner_0.2"
},
{
"formula_name": "定义3（圆满再现：Clifford 代数化）",
"formula_content": "δ 的迭代在编码轨道上产生候选参数。{2,3,5} 的互锁性（乘积 = h(E₈) = 30，可赋值给 D₄ triality 轨道系数 {3,4,5}，满足互锁方程）使其在编码轨道上形成自洽闭合回路——Berry 相位闭合。圆满后，{2,3,5} 再现为 Bott 周期 8 的实 Clifford 代数结构。δ 被实现为 Bott 步进算符：δ(Cl(n)) = Cl(n+1)，其中 Cl(n+1) 从 Cl(n) 通过添加新生成元 e_{n+1} 得到，满足 e_{n+1}² = -1，e_{n+1}e_i + e_i e_{n+1} = 0（i ≤ n）。",
"derivation_chain": "步骤1: 由公理（零之动），δ 是 𝒵 上的非平凡自映射；步骤2: δ 的迭代在编码轨道上产生候选参数（0.1 引理 3.5.2/3.5.3、定理 3.5.4：三层自指闭合）；步骤3: 候选参数 {2,3,5} 互锁：2×3×5 = 30 = h(E₈)，赋值 D₄ triality 轨道系数 {3,4,5} 满足互锁方程 p₁p₂p₃ = h；步骤4: 互锁性使编码轨道形成自洽闭合回路，Berry 相位闭合（∮𝒜 = 2π，定理 0.3.2.01）；步骤5: 圆满后 δ 实现为 Bott 步进算符：δ(Cl(n)) = Cl(n+1)，新生成元满足 e_{n+1}²=-1 与反交换。∎",
"topology_class": "A1", "formula_type": "命题", "article_number": "定义3",
"source_agent": "article_scanner_0.2"
},
# ============ 0.3 Bott 周期与七层截断 ============
{
"formula_name": "定理 0.3.1.01（Bott 周期）",
"formula_content": "δ⁸(Cl(n)) = Cl(n+8) ≅ Cl(n)⊗Mat(16,ℝ)。不可约表示维数序列为 1,2,4,4,8,8,8,8,16，第 8 步恰好是第 0 步的 16 倍。",
"derivation_chain": "步骤1: 由 Clifford 代数分类（0.2 §1.4 中心-体积元分析逐步判定）：Cl(0)=ℝ, Cl(1)=ℂ, Cl(2)=ℍ, Cl(3)=ℍ⊕ℍ, Cl(4)=Mat(2,ℍ), Cl(5)=Mat(4,ℂ), Cl(6)=Mat(8,ℝ), Cl(7)=Mat(8,ℝ)⊕Mat(8,ℝ), Cl(8)=Mat(16,ℝ)；步骤2: 不可约表示维数序列 1,2,4,4,8,8,8,8,16；步骤3: Cl(8) = Mat(16,ℝ) ≅ Cl(0)⊗Mat(16,ℝ)；步骤4: 由 Atiyah–Bott–Shapiro（1964）经典结果，实 Clifford 代数满足 8 步周期：Cl(n+8) ≅ Cl(n)⊗Mat(16,ℝ)；步骤5: 在 δ 迭代框架中 δ⁸(Cl(n)) = Cl(n+8)。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.3.1.01",
"source_agent": "article_scanner_0.3"
},
{
"formula_name": "定理 0.3.1.02（KO 理论不变量）",
"formula_content": "Bott 周期在 KO 理论中的不变量表述：KO^{-n}(pt) 依 n mod 8 取 Z, Z₂, Z₂, 0, Z, 0, 0, 0。Bott 生成元 η ∈ KO^{-1}(pt) = Z₂ 的 8 次幂 η⁸ ∈ KO^{-8}(pt) = Z 是 Bott 整数，其值为 1——生成 KO^{-8}(pt)=Z 的生成元。",
"derivation_chain": "步骤1: KO 理论定义（实 K 理论的约化版本），对点空间 pt 计算 KO^{-n}(pt)；步骤2: 经典结果：KO^{-n}(pt) 呈 8 步周期 Z, Z₂, Z₂, 0, Z, 0, 0, 0（n=0,...,7）；步骤3: Bott 生成元 η 对应 Cl(1)→Cl(0) 的降维操作（去除一个生成元）；步骤4: 8 步回路 Cl(0)→Cl(1)→⋯→Cl(8) 对应 η 的 8 次复合；步骤5: η⁸ ∈ KO^{-8}(pt) = Z 且 η⁸ = 1 ≠ 0——回路携带非平凡拓扑荷。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.3.1.02",
"source_agent": "article_scanner_0.3"
},
{
"formula_name": "定理 0.3.2.01（δ⁸ 回路的 Berry 相位）",
"formula_content": "γ_Berry(δ⁸) = 2π。δ⁸ 回路的拓扑相位由 Chern-Simons 7-形式 CS₇ 的积分给出：γ_Berry = ∮_{Γ₈} 𝒜 = ∫_{D⁸} CS₇，其中 D⁸ 是以 Γ₈ 为边界的 8 维盘，CS₇ = I₁+I₂+I₃ 的三项分别对应编码轨道三个子段（物质 Cl(0)→Cl(3)、因果 Cl(3)→Cl(5)、信息 Cl(5)→Cl(8)）。",
"derivation_chain": "步骤1: 编码轨道参数化：8 步 δ 迭代对应 8 维环面 T⁸ 上的闭合路径 Γ₈，每步 δ 对应一个角度 θ_n ∈ [0,2π]；步骤2: Berry 联络 𝒜 = ⟨ψ(θ)|dψ(θ)⟩，其中 |ψ(θ)⟩ 是 Cl(n) 不可约表示的参数依赖编码态（定义 0.4.2.01）；步骤3: 由定理 0.3.1.02，8 步回路不变量 η⁸ = 1 ≠ 0 ⇒ 回路非平凡；步骤4: 非平凡拓扑荷由 Chern-Simons 7-形式经 transgression 标准公式 CS₇ = ∫₀¹dt tr(F⁴) 积分给出：γ = ∮_{Γ₈}𝒜 = ∫_{D⁸}CS₇；步骤5: CS₇ 三项分解 I₁+I₂+I₃ 覆盖编码轨道三段（3+2+2 步）；步骤6: 归一化（Bott 生成元规范性质：η⁸=1 对应积分值 2π）：γ = 2π。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.3.2.01",
"source_agent": "article_scanner_0.3"
},
{
"formula_name": "定理 0.3.3.01（七层截断）",
"formula_content": "由于 δ⁸ 的 Berry 相位 = 2π ≠ 0，编码映射在 δ⁷ 处截断。编码轨道有 7 层 E₁,E₂,...,E₇。第 8 层 E₈ 不是独立的——它是 E₁ 但带了一个 2π 的整体旋转（闭合步）。",
"derivation_chain": "步骤1: 由定理 0.3.2.01，δ⁸ 的 Berry 相位 = 2π；步骤2: 2π 相位不改变量子态物理内容（ψ 与 e^{2πi}ψ 相同），但改变编码映射的代数基：Cl(8) ≅ Cl(0)⊗Mat(16,ℝ)——第 8 层是第 0 层的放大版；步骤3: 反证：若 E₈ 独立，则 E₉ = Cl(9) ≅ Cl(1)⊗Mat(16,ℝ) 也是 E₁ 的放大版，归纳得所有 E_{8k} 都是 E_k 的放大版；步骤4: 但 Berry 相位 = 2π ≠ 0 使 E₈ 不能简单等同 E₀（否则相位应为 0）——E₈ 是带 2π 旋转的闭合步；步骤5: 因此编码映射有效层数为 7：E₁: Cl(0)→Cl(1), ..., E₇: Cl(6)→Cl(7)，E₈ 为闭合步。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.3.3.01",
"source_agent": "article_scanner_0.3"
},
{
"formula_name": "定理 0.3.3.02（322 分割的刚性）",
"formula_content": "编码轨道 7 层 + 1 闭合步的分割为 3+2+2+1 = 8：第一段 E₁E₂E₃（物质 ℳ，Λ=3）、第二段 E₄E₅（因果 𝒞，ΔΘ=5）、第三段 E₆E₇（信息 ℐ，k₀=2）、闭合步 E₈（圆满性，Berry=2π）。该分割由结构跳跃点 n=3,5,7 与闭合点 n=8 刚性确定，任何其他分割（如 422、332、323）都将终端放在无结构跳跃的位置，违反「凝结点=结构跳跃点」原则。",
"derivation_chain": "步骤1: 由引理 0.2.2.01（半单分裂），Cl(3) 是首次结构跳跃 ⇒ 第一段终端必须为 E₃；步骤2: 由引理 0.2.2.02（复结构涌现），Cl(5) 是复结构跳跃 ⇒ 第二段终端必须为 E₅；步骤3: 由引理 0.2.2.03（终端二元性），Cl(7) 是终端结构跳跃 ⇒ 第三段终端必须为 E₇；步骤4: 由定理 0.3.1.01（Bott 周期），Cl(8) 是 Bott 回归 ⇒ E₈ 为闭合步；步骤5: 反证其他分割：422 将物质终端放在无半单分裂的 Cl(4)（缝合位置，无跳跃）；332 将因果终端放在无复结构的 Cl(6)（复结构实化位置）；323 将信息终端放在 Bott 回归的 Cl(8)（闭合步非独立层）——均违反凝结点=结构跳跃点原则；步骤6: 分割 3221 = 8 唯一。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.3.3.02",
"source_agent": "article_scanner_0.3"
},
# ============ 0.4 圆满性判据 ============
{
"formula_name": "定理 0.4.1.02（自洽性筛选与存活者层级）",
"formula_content": "筛选算符 Σ 作用于候选结构集合，保留自洽的候选结构：Σ({S_n}) = {S_n | S_n 自洽}，其中候选结构 S_n = (e₁,...,e_n) 满足生成元公理（e_i²=-1）、反交换公理（e_i e_j = -e_j e_i）、结合性、闭合性（存在 e_{n+1} 使 S_{n+1} 也自洽）。存活者层级 S₀ ⊂ S₁ ⊂ ⋯ ⊂ S₇ 每层在同构意义下唯一：S_n = {Cl(n)}。编码轨道是唯一的——没有分支或选择。",
"derivation_chain": "步骤1: 定义候选结构 S_n = (e₁,...,e_n)（0.4 §1.2 定义4）；步骤2: 自洽性四条件（定义5）：生成元公理、反交换公理、结合性、闭合性；步骤3: 定义筛选算符 Σ（定义6）：保留自洽候选；步骤4: 归纳：S₀ = {ℝ} 唯一起点；假设 S_{n-1} = {Cl(n-1)} 唯一，则添加 e_n（e_n²=-1，与已有生成元反交换）在同构意义下唯一确定 Cl(n)（Clifford 代数生成元关系刚性）；步骤5: 由定理 0.3.3.01（七层截断），有效层数 7，存活者层级 S₀⊂⋯⊂S₇；步骤6: 编码轨道唯一。∎",
"topology_class": "A0", "formula_type": "定理", "article_number": "0.4.1.02",
"source_agent": "article_scanner_0.4"
},
{
"formula_name": "定义 0.4.2.01（Berry 联络）",
"formula_content": "在编码轨道的参数空间 T⁸ 上，Berry 联络 𝒜 定义为 𝒜 = ⟨ψ(θ)|dψ(θ)⟩，其中 |ψ(θ)⟩ 是参数依赖的编码态（Clifford 代数 Cl(n) 的不可约表示在参数 θ=(θ₁,...,θ_n) 下的实现）。Berry 曲率 F = d𝒜 + 𝒜∧𝒜。𝒜 的积分 ∮_Γ 𝒜 是回路 Γ 的 Berry 相位。",
"derivation_chain": "步骤1: 编码轨道参数化：每步 δ 对应引入角度 θ_n，8 个角度张成参数空间 T⁸（0.3 §2.1）；步骤2: 编码态构造：e_n(θ_n) = cosθ_n·e_n⁽⁰⁾ + sinθ_n·e_n⁽¹⁾，|ψ(θ)⟩ 为 ρ_n 的参数依赖基态；步骤3: 定义 Berry 联络 𝒜 = ⟨ψ(θ)|dψ(θ)⟩（1-形式）；步骤4: 定义 Berry 曲率 F = d𝒜 + 𝒜∧𝒜；步骤5: 沿闭合回路 Γ 积分得 Berry 相位 ∮_Γ 𝒜。∎",
"topology_class": "A1", "formula_type": "命题", "article_number": "0.4.2.01",
"source_agent": "article_scanner_0.4"
},
{
"formula_name": "定理 0.4.3.01（CS₇ 三项结构）",
"formula_content": "δ⁸ 回路的 Berry 相位通过 Chern-Simons 7-形式计算：γ_Berry = ∫_{D⁸} CS₇ = ∫_{D⁸}(I₁+I₂+I₃)。三项分别对应编码轨道三个子段：I₁（物质，Cl(0)→Cl(3)，半单分裂的拓扑荷）、I₂（因果，Cl(3)→Cl(5)，复结构涌现的拓扑荷）、I₃（信息，Cl(5)→Cl(8)，终端二元性的拓扑荷）。各项积分贡献均为 2π/3：∫I₁ = ∫I₂ = ∫I₃ = 2π/3，总和 2π。",
"derivation_chain": "步骤1: 由定理 0.3.2.01，γ_Berry = ∫_{D⁸} CS₇；步骤2: 编码轨道三段分割（3+2+2 步）刚性确定 CS₇ 三项分解 I₁+I₂+I₃（定理 0.3.3.02）；步骤3: 每项对应一个结构跳跃事件（半单分裂、复结构涌现、终端二元性），各贡献一份拓扑荷——系数 (1,1,1)，与直和项个数无关；步骤4: 由 CS₇ 的 transgression 显式表达（标准公式 CS₇ = ∫₀¹dt tr(F⁴)）在各自子段积分，每项 = 2π/3（由 CS₇ 显式表达与归一化两条独立路径联合锁定）；步骤5: 总和 γ = (2π/3)(1+1+1) = 2π，与定理 0.3.2.01 一致。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.4.3.01",
"source_agent": "article_scanner_0.4"
},
{
"formula_name": "定理 0.4.5.01（三扇区子回路部分圆满）",
"formula_content": "三个扇区子回路 Γ_M（物质，3 步）、Γ_C（因果，2 步）、Γ_I（信息，2 步）的 Berry 相位均为 2π/3——各自不满足圆满条件 2πn（n∈ℤ），但联合起来 3×(2π/3) = 2π 构成完整的圆满。三扇区各自是「部分圆满」的，必须联合才能构成完整的圆满。",
"derivation_chain": "步骤1: 由定理 0.4.3.01，CS₇ 三项 I₁, I₂, I₃ 的积分各为 2π/3；步骤2: 扇区子回路 Γ_M、Γ_C、Γ_I 的 Berry 相位分别等于 ∫I₁、∫I₂、∫I₃（子回路-子段对应，0.4 §2.1）；步骤3: 各子回路相位 = 2π/3 ∉ 2πℤ ⇒ 各自不满足圆满判据 ∮𝒜 = 2πn（定理 0.4.4.01）；步骤4: 联合 3×(2π/3) = 2π = 2π×1 满足判据（n=1）；步骤5: 三扇区部分圆满，联合圆满。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.4.5.01",
"source_agent": "article_scanner_0.4"
},
# ============ 0.5 结构常数的代数涌现 ============
{
"formula_name": "定理 0.5.0.01（E₈ 桥接定理）",
"formula_content": "设 Bott 周期为 8（Atiyah–Bott–Shapiro）。则素因子集 {2,3,5} 由以下证明链唯一确定为维度 8 的拓扑不变量：Bott 周期 → 维度 8 → E₈ 唯一 → h=30 → {2,3,5}。",
"derivation_chain": "步骤1: Bott 周期 → KO 群 8-周期性：Cl(n+8) ≅ Cl(n)⊗Mat(16,ℝ) 等价于 KO^{n+8}(X) ≅ KO^n(X)（Atiyah–Bott–Shapiro 1964）；步骤2: KO 8-周期 → 偶幺模格存在条件：ℝⁿ 中存在偶幺模格当且仅当 n ≡ 0 (mod 8)；E₈ 根格可旋量构造为 E₈ = D₈ ∪ (D₈ρ)（ρ 为 Spin(16) 半旋量权，来自 Clifford 旋量表示）；步骤3: 由定理 0.5.0.02（Minkowski–Serre），维度 8 中 E₈ 是唯一偶幺模格；步骤4: E₈ 的 Coxeter 数 h = |Φ(E₈)|/rank(E₈) = 240/8 = 30；步骤5: 30 = 2×3×5 素因子分解唯一 ⇒ 素因子集 {2,3,5}。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.5.0.01",
"source_agent": "article_scanner_0.5"
},
{
"formula_name": "定理 0.5.0.02（Minkowski–Serre）",
"formula_content": "在维度 8 中，E₈ 格是唯一的偶幺模格。偶性：∀v∈Λ, v·v ∈ 2ℤ；幺模性：det(Λ)=1。维度 < 8 无偶幺模格，维度 8 恰有一个（E₈），维度 16 有两个（E₈⊕E₈ 和 D₁₆⁺），维度 24 有 24 个（Niemeier 格）。",
"derivation_chain": "步骤1: 偶性要求 v·v ∈ 2ℤ 使二次型的整性约束与 KO 理论的特征类理论一致（定理 0.5.0.01 步骤2）；步骤2: 格论经典结果（Minkowski–Serre）：偶幺模格存在当且仅当维度 ≡ 0 (mod 8)；步骤3: 维度 8 时唯一解为 E₈（E₈ 根系的 Cartan 矩阵 det = 1 且所有根长平方 = 2，满足偶幺模条件）；步骤4: 唯一性：维度 8 的偶幺模格恰有一个（Niemeier 分类的边界情形）。∎",
"topology_class": "A1", "formula_type": "定理", "article_number": "0.5.0.02",
"source_agent": "article_scanner_0.5"
},
{
"formula_name": "定理 0.5.0.03（个体赋值）",
"formula_content": "E₈ Dynkin 图包含 D₄ 子图（Spin(8)），D₄ 具有 triality 对称 S₃。E₈ 最高根 θ = 2α₁+3α₂+4α₃+6α₄+5α₅+4α₆+3α₇+2α₈ 在 D₄ triality 轨道三个外节点 {α₂,α₃,α₅} 上的系数恰为 {3,4,5}，其素因子分别给出 Λ=3、k₀=2、ΔΘ=5。",
"derivation_chain": "步骤1: E₈ Dynkin 图（Bourbaki 编号）：α₄ 三价，子图 {α₂,α₃,α₄,α₅} 构成 D₄（so(8) ≅ Spin(8)）；步骤2: D₄ 是唯一具有 triality 对称 S₃ 的 Dynkin 图（标准 Lie 理论事实）；步骤3: E₈ 最高根 θ = 2α₁+3α₂+4α₃+6α₄+5α₅+4α₆+3α₇+2α₈，D₄ triality 轨道三节点系数 {3,4,5}（α₂:3、α₃:4、α₅:5）；步骤4: D₄ 嵌入 E₈ 时三条臂长不同（1,0,3），triality 被 E₈ 的整体结构破缺——个体赋值由此唯一确定；步骤5: 素因子分解：3 → Λ=3（半单分裂 Cl(3)），4 → 素因子 2 → k₀=2（终端二元性 Cl(7)），5 → ΔΘ=5（复结构涌现 Cl(5)）。∎",
"topology_class": "A0", "formula_type": "定理", "article_number": "0.5.0.03",
"source_agent": "article_scanner_0.5"
},
]

print(f"[BATCH] 共 {len(formulas)} 条，开始提交...", flush=True)

ids = []
for f in formulas:
    try:
        r = post("/v1/master/submit", f)
        sid = r.get("submission_id", "?")
        print(f"[SUBMIT] {f['formula_name']} → {sid}", flush=True)
        ids.append(sid)
    except Exception as e:
        print(f"[SUBMIT-ERR] {f['formula_name']}: {e}", flush=True)
        ids.append(None)
    time.sleep(1)

print(f"[BATCH] 提交完成，开始逐条验证（{len([i for i in ids if i])} 条）...", flush=True)

for sid in ids:
    if not sid:
        continue
    try:
        r = post("/v1/master/verify", {"submission_id": sid}, timeout=300)
        action = r.get("action", "?")
        print(f"[VERIFY] {sid} → {action}", flush=True)
        with open("master_ai/logs/batch_02_detail.jsonl", "a") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[VERIFY-ERR] {sid}: {e}", flush=True)
    time.sleep(2)

print("[BATCH] 全部处理完毕", flush=True)
