# -*- coding: utf-8 -*-
"""第三轮：引理3.5.3修正 → 定理3.5.4原样 → 定义2修正。串行提交，每条等结果后再提交下一条。"""
import json, time, urllib.request, subprocess, re, ast

BASE = "http://localhost:5001"
TOKEN = "master-ai-verify"
HDRS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def post(path, data, timeout=600):
    req = urllib.request.Request(BASE+path, data=json.dumps(data).encode(), headers=HDRS, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

FIELD_RE = re.compile(r'^"([^"]+)":\s*"(.*)",?\s*$')

def extract_block(src_path, name):
    src = open(src_path).read()
    lines = src.split('\n')
    for i, ln in enumerate(lines):
        if name in ln and '"formula_name"' in ln:
            d = {}
            j = i
            while j < len(lines):
                line = lines[j].strip()
                if line == '},':
                    break
                m = FIELD_RE.match(line)
                if m:
                    try:
                        d[m.group(1)] = ast.literal_eval('"' + m.group(2) + '"')
                    except Exception:
                        d[m.group(1)] = m.group(2)
                j += 1
            return d
    return None

def query_pending_status():
    """查询 pending 状态（通过 server 端 python3.11）"""
    out = subprocess.run(
        ["/usr/local/Cellar/python@3.11/3.11.15_3/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python", "-c", """
import chromadb
client = chromadb.PersistentClient(path='master_chroma_db')
col = client.get_collection('pending_submissions')
items = col.get(include=['metadatas'])
for mid, m in zip(items['ids'], items['metadatas']):
    print(mid, '|', m.get('formula_name','?'), '|', m.get('status','?'))
"""], capture_output=True, text=True, cwd="master_ai", timeout=30)
    out_map = {}
    for l in out.stdout.strip().split('\n'):
        if '|' in l:
            p = [x.strip() for x in l.split('|')]
            if len(p) >= 3:
                out_map[p[0]] = (p[1], p[2])
    return out_map

def query_truth():
    """查询真理层公式名列表（master_formulas）"""
    out = subprocess.run(
        ["/usr/local/Cellar/python@3.11/3.11.15_3/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python", "-c", """
import chromadb
client = chromadb.PersistentClient(path='master_chroma_db')
col = client.get_collection('master_formulas')
items = col.get(include=['metadatas'])
for m in items['metadatas']:
    print(m.get('formula_name','?'))
"""], capture_output=True, text=True, cwd="master_ai", timeout=30)
    return [l.strip() for l in out.stdout.strip().split('\n') if l.strip()]

def wait_truth(fname, timeout_min=15):
    """等待某公式出现在真理层"""
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        try:
            names = query_truth()
            if any(fname in n for n in names):
                print(f"  ✓ {fname} 已在真理层")
                return True
        except Exception as e:
            print("  真理层查询异常:", e)
        print(f"  [{time.strftime('%H:%M:%S')}] 等待 {fname} 入库...")
        time.sleep(30)
    return False

def wait_formula(fname, sid, timeout_min=10):
    """等待某 sid 状态变为 promoted/rejected/paused"""
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        time.sleep(25)
        try:
            st = query_pending_status()
            if sid in st:
                fn, s = st[sid]
                print(f"  [{time.strftime('%H:%M:%S')}] {fn}: {s}")
                if s in ('promoted', 'rejected', 'paused'):
                    return s
        except Exception as e:
            print("  查询异常:", e)
    return 'timeout'

# ---- 1. 引理 3.5.3 修正版 ----
lemma353 = extract_block("batch_0103.py", "引理 3.5.3")
lemma353["derivation_chain"] = ("步骤1: 设二元循环 A=抑制（第一区分），B=痕迹（记忆区分），B 记住了 A 的否定，但「B 记住了 A」没有被第三者对象化；"
"步骤2: 若只有两层（𝒵 与 δ(𝒵)），「无新事」意味着第二次操作与第一次无差别：δ² 与 δ 在 𝒵 上作用相同，即 δ∘δ = δ；"
"步骤3: 这与命题 0.1.3.01（非幂等性：δ∘δ ≠ δ）矛盾；"
"步骤4: 因此二元循环在 δ 框架中不自洽，δ 的非幂等性强制作了第三层的存在。∎\n\n"
"【依赖】命题 0.1.3.01（非幂等性）。\n"
"【共扼圆满】与命题 0.1.3.01 联合构成不可约性论证（二元循环被非幂等性排除，强制作出第三层）。")
print("[1/3] 提交引理 3.5.3（修正版）...")
r = post("/v1/master/submit", lemma353, timeout=120)
sid1 = r.get("submission_id")
print("  sid:", sid1)
s1 = wait_formula("引理 3.5.3", sid1)
print("  引理 3.5.3 结果:", s1)

# ---- 2. 定理 3.5.4（原样，依赖引理 3.5.3 现已入库）----
if s1 == 'promoted':
    th354 = extract_block("batch_0103.py", "定理 3.5.4")
    print("[2/3] 提交定理 3.5.4（原样）...")
    r = post("/v1/master/submit", th354, timeout=120)
    sid2 = r.get("submission_id")
    print("  sid:", sid2)
    s2 = wait_formula("定理 3.5.4", sid2)
    print("  定理 3.5.4 结果:", s2)
else:
    s2 = 'skipped'
    print("[2/3] 跳过（引理 3.5.3 未入库）")

# ---- 3. 定义2 修正版（依赖：原理3.5.5 + 定理0.3.2.01）----
if s2 == 'promoted':
    def2 = extract_block("batch_0103.py", "定义2")
    def2["derivation_chain"] = ("步骤1: 由原理 3.5.5（三层自指闭合）知抑制-痕迹-涌现是同一个事件的三张面孔（同时产生、互相制衡）；"
"步骤2: 无抑制→无区分→δ 平凡；无痕迹→区分瞬时→无累积；无涌现→来回振荡→无结构——三者缺一则区分崩解；"
"步骤3: 闭合=圆满：δ 迭代足够多次后回路闭合回自身（带回累积的模式）——闭合性是互扼平衡的标志，其精确化（Berry 相位 = 2π）由定理 0.3.2.01 给出；"
"步骤4: 总作用量为零是 δ 作为非满射自映射的内在属性（公理（零之动）§2.3）。∎\n\n"
"【依赖】原理 3.5.5（三层自指闭合原理）、公理（零之动）、定理 0.3.2.01（δ⁸ 回路的 Berry 相位）。\n"
"【共扼圆满】与原理 3.5.5 联合构成互扼平衡（闭合标志：回路回到自身带回累积模式，即圆满的原始形态）。")
    print("[3/3] 先确认 0.3.2.01 入库（定义2 依赖它）...")
    if not wait_truth("定理 0.3.2.01"):
        print("  0.3.2.01 未在限时内入库，跳过定义2")
        s3 = 'skipped_no_dep'
    else:
        print("[3/3] 提交定义2（修正版）...")
        r = post("/v1/master/submit", def2, timeout=120)
        sid3 = r.get("submission_id")
        print("  sid:", sid3)
        s3 = wait_formula("定义2", sid3)
        print("  定义2 结果:", s3)
else:
    s3 = 'skipped'
    print("[3/3] 跳过（定理 3.5.4 未入库）")

print("\n===== 汇总 =====")
print("引理 3.5.3:", s1)
print("定理 3.5.4:", s2)
print("定义2:", s3)
