import csv, math
from collections import Counter, defaultdict
import re

def parse_formula(f):
    toks = re.findall(r'([A-Z][a-z]?)(\d*\.?\d*)', f)
    return {el: float(n) if n else 1.0 for el, n in toks}

rows = []
with open("CD/data/mcmillan_rank_260803.csv", encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)
N = len(rows)
print(f"N = {N}")

def n_atoms(formula):
    return sum(parse_formula(formula).values())

def has_elem(formula, el):
    return el in parse_formula(formula)

def fam_id(r):
    sg = r["spacegroup_number"]
    na = n_atoms(r["formula"])
    f = r["formula"]
    tags = []
    if sg == "223": tags.append("A15")
    if sg == "227" and na == 7 and has_elem(f, "C"): tags.append("eta-carbide")
    if sg == "227" and na == 3: tags.append("C15")
    if sg == "136": tags.append("sigma")
    if sg == "166" and na == 13: tags.append("mu")
    if sg in ("212", "213"): tags.append("beta-Mn")
    if sg == "225": tags.append("B1")
    if sg == "191" and na == 3: tags.append("AlB2")
    if sg == "148" and na == 15: tags.append("Chevrel")
    return tags

fam_members = defaultdict(list)
for r in rows:
    for t in fam_id(r):
        fam_members[t].append(r)

ALL_FAMS = ["A15","eta-carbide","C15","sigma","mu","beta-Mn","B1","AlB2","Chevrel"]
print("\n--- 家族规模 ---")
for t in ALL_FAMS:
    print(f"{t}: {len(fam_members[t])}")
M_all = sum(len(fam_members[t]) for t in ALL_FAMS)
M_strict = M_all - len(fam_members["B1"])
print(f"M_all = {M_all}, M_strict = {M_strict}")

def rank_by(key):
    srt = sorted(rows, key=lambda r: float(r[key] or -1e9), reverse=True)
    return {r["formula"]: i+1 for i, r in enumerate(srt)}

rank_mc = rank_by("tc_mcmillan_k")
rank_lg = rank_by("tc_legacy_k")

def best_rank(fams, rank):
    best = {}
    for t in ALL_FAMS:
        rs = [rank[r["formula"]] for r in fams[t] if r["formula"] in rank]
        best[t] = (min(rs), len(rs)) if rs else (None, 0)
    return best

bm, bl = best_rank(fam_members, rank_mc), best_rank(fam_members, rank_lg)
print("\n--- 各家族最佳 rank (McMillan / legacy) ---")
for t in ALL_FAMS:
    print(f"{t:12s} mc={bm[t][0]} (m={bm[t][1]})   lg={bl[t][0]} (m={bl[t][1]})")

def hyp_p(x, K, m, Ntot):
    p = 0.0
    for i in range(x, min(m, K)+1):
        p += math.comb(m, i) * math.comb(Ntot-m, K-i) / math.comb(Ntot, K)
    return p

def topk_fams(rank_key, K, include_B1=True):
    srt = sorted(rows, key=lambda r: float(r[rank_key] or -1e9), reverse=True)[:K]
    cnt = 0
    fams_seen = Counter()
    for r in srt:
        for t in fam_id(r):
            if t == "B1" and not include_B1: continue
            cnt += 1
            fams_seen[t] += 1
    return cnt, fams_seen

print("\n--- 富集检验 (McMillan) ---")
for K in (10, 30, 100):
    for inc in (True, False):
        x, fs = topk_fams("tc_mcmillan_k", K, inc)
        M = M_all if inc else M_strict
        p = hyp_p(x, K, M, N)
        print(f"Top{K:3d} incB1={str(inc):5s} x={x} 期望={M*K/N:.2f}  P={p:.2e}  {dict(fs)}")

print("\n--- 富集检验 (legacy) ---")
for K in (10, 30, 100):
    for inc in (True, False):
        x, fs = topk_fams("tc_legacy_k", K, inc)
        M = M_all if inc else M_strict
        p = hyp_p(x, K, M, N)
        print(f"Top{K:3d} incB1={str(inc):5s} x={x} 期望={M*K/N:.2f}  P={p:.2e}  {dict(fs)}")

def first_member_p(m, r, Ntot):
    if r is None: return None
    return 1 - math.comb(Ntot-m, r)/math.comb(Ntot, r)

print("\n--- 单家族 p 值 (McMillan, Bonferroni x9) ---")
for t in ALL_FAMS:
    r, m = bm[t]
    if r is None: continue
    p = first_member_p(m, r, N)
    print(f"{t:12s} rank={r:5d} m={m:3d} p={p:.2e}  p_Bonf={min(1,p*9):.2e}")

print("\n--- eta-carbide 成员 ---")
for r_ in sorted(fam_members["eta-carbide"], key=lambda x: rank_mc[x["formula"]]):
    print(f"{r_['formula']:12s} mc_rank={rank_mc[r_['formula']]:5d} Tc_mc={float(r_['tc_mcmillan_k'] or 0):7.2f}K  lg_rank={rank_lg[r_['formula']]:5d}")

print("\n--- 盲区 Nb3Al2N / Nb3Al2C ---")
for f in ("Nb3Al2N", "Nb3Al2C"):
    for r_ in rows:
        if r_["formula"] == f:
            print(f"{f}: mc_rank={rank_mc.get(f)} Tc_mc={r_['tc_mcmillan_k']} lg_rank={rank_lg.get(f)} Tc_lg={r_['tc_legacy_k']} sg={r_['spacegroup_number']}")

print("\n--- 置换检验 (McMillan Top10, 剔B1, 10000次) ---")
import random
random.seed(42)
strict_flag = [1 if any(t != "B1" for t in fam_id(r)) else 0 for r in rows]
order_mc = sorted(range(N), key=lambda i: float(rows[i]["tc_mcmillan_k"] or -1e9), reverse=True)
obs = sum(strict_flag[i] for i in order_mc[:10])
cnt = 0
for _ in range(10000):
    perm = random.sample(range(N), 10)
    if sum(strict_flag[i] for i in perm) >= obs:
        cnt += 1
print(f"观察 = {obs}, 置换>=观察比例 = {cnt/10000}")

print("\n--- legacy Top30 家族成员明细 ---")
for i, r_ in enumerate(sorted(rows, key=lambda x: float(x["tc_legacy_k"] or -1e9), reverse=True)[:30]):
    t = fam_id(r_)
    if t:
        print(f"rank={i+1:2d} {r_['formula']:16s} {t}  lg={r_['tc_legacy_k']}")

print("\n--- McMillan Top10 明细 ---")
for i, r_ in enumerate(sorted(rows, key=lambda x: float(x["tc_mcmillan_k"] or -1e9), reverse=True)[:10]):
    t = fam_id(r_)
    print(f"rank={i+1:2d} {r_['formula']:16s} Tc_mc={r_['tc_mcmillan_k']:>7} 家族={t if t else '-'} sg={r_['spacegroup_number']}")
