# -*- coding: utf-8 -*-
"""批量提交 0.1 系列公式到主库（从0.1开始积累）"""
import json, time, urllib.request

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
    # ---- 公理（零之动）：体系唯一公理 ----
    {
        "formula_name": "公理（零之动）",
        "formula_content": "公理（零之动）：𝒵 上存在非平凡自映射 δ: 𝒵 → 𝒵，满足 δ(𝒵) ⊊ 𝒵。这是整个体系唯一的公理，后续所有结构（Clifford 代数、Bott 周期、三个结构常数、物理常数）都从这一条公理推导出来。特征：(1) 非创造性——δ 不从外部引入任何东西，它是 𝒵 上的自映射；(2) 非平凡性——δ(𝒵) ≠ 𝒵，动产生了差异；(3) 景观生成性——δ 生成所有满足非平凡有限周期自映射的代数实现的景观。第一区分：δ(𝒵) ≠ 𝒵 产生最原初的二元性（动之前 vs 动之后）。",
        "derivation_chain": "公理，无需推导。δ 的非满射性（δ(𝒵) ⊊ 𝒵）是总作用量守恒且守恒值为零的根源：δ 只在 𝒵 内部重新分配，总账始终为零（零之动的双重含义：存在论之零与动力学之零 S_total = 0）。",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "公理",
        "article_number": "公理（零之动）",
        "priority_hint": True,
    },
    # ---- 定义1（未分化潜势）----
    {
        "formula_name": "定义1（未分化潜势）",
        "formula_content": "定义1（未分化潜势）：设 𝒵 是一个集合（ZFC 内的合法数学对象）。δ: 𝒵 → 𝒵 是非平凡自映射——δ(𝒵) ≠ 𝒵。𝒵 先于一切概念化、一切性质归属：它不是虚无（虚无已被概念化从而已被区分），不是空集 ∅（空集已带「空」这一性质），而是能够产生东西的原始潜势。",
        "derivation_chain": "步骤1: 由公理（零之动）知 𝒵 上存在非平凡自映射 δ；步骤2: 定义1 将 𝒵 数学定位为 ZFC 内的集合，并明确 δ 的非平凡性 δ(𝒵)≠𝒵；步骤3: 未分化性质仅为哲学动机（密着拓扑类比），数学推导不依赖任何拓扑学性质。",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "定义1",
    },
    # ---- 命题 0.1.3.01（非幂等性）----
    {
        "formula_name": "命题 0.1.3.01（非幂等性）",
        "formula_content": "命题 0.1.3.01（非幂等性）：δ ∘ δ ≠ δ——δ 不是幂等的。δ 的每次迭代都做了新的工作，δ 的轨道是一条路径而非一个点：𝒵, δ(𝒵), δ²(𝒵), δ³(𝒵), … 每一项都不同于前一项。",
        "derivation_chain": "步骤1: 反证法，假设 δ∘δ = δ，则 δ(δ(𝒵)) = δ(𝒵)，δ 在第一次迭代后停止做事；步骤2: 但公理（零之动）的非平凡性（δ ≠ id，δ 产生区分）要求结构涌现需要持续操作，若第二次迭代就停止，第一次产生的区分未被加工，结构无法累积；步骤3: 矛盾，故 δ∘δ ≠ δ。∎",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "0.1.3.01",
    },
    # ---- 定义 3.5.1（δ-域类型）----
    {
        "formula_name": "定义 3.5.1（δ-域类型）",
        "formula_content": "定义 3.5.1（δ-域类型）：对于 𝒵 的子集 A, B ⊆ 𝒵，定义 A 与 B 具有相同的 δ-域类型（记作 A ∼ B），当且仅当存在双射 φ: A → B 和 ψ: δ(A) → δ(B) 使得交换图成立：ψ∘δ|_A = δ|_B∘φ。域类型刻画 δ 在一个子集上的「行为模式」——两个子集在 δ 作用下表现得一样（只差重命名），则它们同型。",
        "derivation_chain": "步骤1: 由公理（零之动）中 δ 的自映射结构定义等价关系；步骤2: 命题 0.1.3.01（非幂等性）保证轨道非单步，域类型是 δ 迭代轨道结构的等价关系刻画。",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "3.5.1",
    },
    # ---- 引理 3.5.2（前三个域类型彼此不同）----
    {
        "formula_name": "引理 3.5.2（前三个域类型彼此不同）",
        "formula_content": "引理 3.5.2：type(𝒵) ≠ type(δ(𝒵)) ≠ type(δ²(𝒵)) ≠ type(𝒵)。前三个 δ-域类型彼此不同。",
        "derivation_chain": "步骤1: 𝒵 完全未分化——在 δ 作用之前没有任何内部结构，δ 对 𝒵 是首次区分（产生 δ(𝒵) ⊊ 𝒵）；步骤2: δ(𝒵) 带有 δ 的印记（非满射性保证 δ(𝒵) ⊊ 𝒵），δ 对 δ(𝒵) 是第二次区分（产生 δ²(𝒵) ⊊ δ(𝒵)）；步骤3: 假设 type(𝒵) = type(δ(𝒵))，则由定义 3.5.1 存在双射 φ: 𝒵 → δ(𝒵) 保持 δ 行为；但 𝒵 中无元素带 δ 印记而 δ(𝒵) 中所有元素都带 δ 印记，「新鲜度」不同，不存在这样的双射；步骤4: 类似论证得 type(δ(𝒵)) ≠ type(δ²(𝒵))。∎",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "3.5.2",
    },
    # ---- 引理 3.5.3（二元循环无结构累积）----
    {
        "formula_name": "引理 3.5.3（二元循环无结构累积）",
        "formula_content": "引理 3.5.3：二元互扼——A 约束 B，B 约束 A——不能产生不可逆的结构累积。",
        "derivation_chain": "步骤1: 设二元循环 A=抑制（第一区分），B=痕迹（记忆区分），B 记住了 A 的否定，但「B 记住了 A」没有被第三者对象化；步骤2: 若只有两层，δ² 之后 δ³ 应 = δ（无新事），则 δ² = id；步骤3: 这与命题 0.1.3.01（非幂等性：δ∘δ ≠ δ）矛盾；步骤4: 因此二元循环在 δ 框架中不自洽，δ 的非幂等性强制作了第三层的存在。∎",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "3.5.3",
    },
    # ---- 定理 3.5.4（δ³ 的自指性质）----
    {
        "formula_name": "定理 3.5.4（δ³的自指性质）",
        "formula_content": "定理 3.5.4：δ³ 是 δ 的迭代中首个操作域包含 δ 自身历史的迭代。",
        "derivation_chain": "步骤1: δ³ = δ∘δ²；步骤2: δ²(𝒵) 的内部区分——δ(𝒵)\\δ²(𝒵)（第一次被触及但第二次未被再触及的「纯粹痕迹」）和 δ²(𝒵)\\δ³(𝒵)（第二次新触及的）——完全由 δ 的前两次操作定义；步骤3: δ 作用于 δ²(𝒵) 时，操作行为受 δ²(𝒵) 内部结构约束，而这个结构是 δ 自身前两次操作的完整记录，印记影响 δ 的行为；步骤4: δ¹ 和 δ² 的操作域（𝒵 和 δ(𝒵)）不包含 δ 的完整历史，因此 δ³ 是首个实现自指的迭代。∎",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "定理",
        "article_number": "3.5.4",
    },
    # ---- 原理 3.5.5（三层自指闭合原理）----
    {
        "formula_name": "原理 3.5.5（三层自指闭合原理）",
        "formula_content": "原理 3.5.5（三层自指闭合原理）：δ³ 实现自指后，三个维度——第一区分（抑制）、记忆区分（痕迹）、自指模式化（涌现）——形成最小不可约互扼循环。δ 的后续迭代（δ⁴, δ⁵, …）不引入新的语义维度；它们在三个已有维度的框架内产生更精细的结构，最终在 δ⁸ 实现拓扑闭合（Bott 周期，Berry 相位 = 2π，由 0.3 严格证明）。三层自指闭合蕴含零和约束：S₁ + S₂ + S₃ = 0（抑制、痕迹、涌现的编码作用量之和为零，这是总作用量为零在三层自指闭合中的具体表达）。",
        "derivation_chain": "步骤1: 由引理 3.5.2（前三个域类型彼此不同）与引理 3.5.3（二元循环无结构累积）知三元不可约：二元不自洽，强制作出第三层；步骤2: 由定理 3.5.4（δ³自指性质）知自指在第三步实现；步骤3: 三元互扼循环为最小不可约——去掉任一维度则区分崩解（无抑制→δ平凡；无痕迹→区分瞬时；无涌现→来回振荡）；步骤4: δ 非满射（公理（零之动））保证总作用量为零，三层编码贡献 S₁+S₂+S₃ = 0（零和约束是贯穿整个编码轨道的刚性边界条件）；步骤5: 「三元之上无新语义维度」的结构类型闭合为方向性断言，其严格拓扑验证（δ⁸ 闭合、Berry 相位=2π）由 0.3（Bott 周期）完成。",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "定理",
        "article_number": "3.5.5",
    },
    # ---- 定义2（互扼）----
    {
        "formula_name": "定义2（互扼）",
        "formula_content": "定义2（互扼）：三个维度互相制衡、互相成全的状态称为互扼——抑制恰好被痕迹记住（否则抑制无效）、痕迹恰好被涌现模式化（否则痕迹只是死记）、涌现恰好被抑制约束（否则涌现无界膨胀）。三者缺一则区分崩解。互扼平衡的标志是闭合——回路回到自身：当 δ 迭代足够多次后，如果回路能闭合（回到出发点但带回了累积的模式），则互扼平衡达成。互扼平衡的数学表达是总作用量为零：S_ℳ + S_𝒞 + S_ℐ = 0。",
        "derivation_chain": "步骤1: 由原理 3.5.5（三层自指闭合）知抑制-痕迹-涌现是同一个事件的三张面孔（同时产生、互相制衡）；步骤2: 无抑制→无区分→δ 平凡；无痕迹→区分瞬时→无累积；无涌现→来回振荡→无结构——三者缺一则区分崩解；步骤3: 闭合=圆满：δ 迭代闭合回自身（Berry 相位=2π，由 0.4 精确化）；步骤4: 总作用量为零是 δ 作为非满射自映射的内在属性（公理（零之动）§2.3）。",
        "source_agent": "article_scanner_0.1",
        "topology_class": "A0",
        "formula_type": "命题",
        "article_number": "定义2",
    },
]

# ============ 提交 ============
ids = []
for f in formulas:
    try:
        r = post("/v1/master/submit", f)
        sid = r.get("submission_id", "?")
        print(f"[SUBMIT] {f['formula_name']} → {sid}", flush=True)
        ids.append(sid)
    except Exception as e:
        print(f"[SUBMIT-ERR] {f['formula_name']}: {e}", flush=True)
    time.sleep(1)

print(f"[INFO] 提交完成，共 {len(ids)} 条", flush=True)

# ============ 逐条验证 ============
for sid in ids:
    if not sid or sid == "?":
        continue
    try:
        r = post("/v1/master/verify", {"submission_id": sid}, timeout=300)
        act = r.get("action", "?")
        print(f"[VERIFY] {sid} → {act}", flush=True)
        with open("master_ai/logs/batch_01_detail.jsonl", "a") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[VERIFY-ERR] {sid}: {e}", flush=True)
    time.sleep(2)

print("[DONE] 0.1 系列全部处理完毕", flush=True)
