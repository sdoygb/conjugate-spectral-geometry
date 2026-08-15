# -*- coding: utf-8 -*-
"""扩大验证：94 种已知超导材料 vs 定理 9.1.12.01 对称筛选判据
材料清单来源：维基百科 List of superconductors (2026-08 抓取)
空间群：标准晶体学知识；关键材料用 COD (crystallography.net) 独立确认
"""
import spglib

CANDIDATE_PGS = {'D6h','D3h','D3d','Oh','Td','C3i','C3v','C3h','C6h','C6v','Th'}

def build_sg2pg():
    m = {}
    for hall in range(1, 531):
        try:
            t = spglib.get_spacegroup_type(hall)
            n = t['number']; pg = t['pointgroup_schoenflies']
            if n not in m:
                m[n] = pg
        except Exception:
            pass
    return m

SG2PG = build_sg2pg()

def is_candidate(sg):
    return SG2PG.get(sg) in CANDIDATE_PGS

# (材料, 类, Tc, 空间群号, COD确认)
M = [
 # 元素类
 ('Al','Element',1.20,225),('Bi','Element',5.3e-4,166),('Cd','Element',0.52,194),
 ('Diamond:B','Element',11.4,227),('Ga','Element',1.083,64),('Ge:Ga','Element',3.5,227),
 ('Hf','Element',0.165,194),('Hg(a)','Element',4.15,166),('Hg(b)','Element',3.95,166),
 ('In','Element',3.4,139),('Ir','Element',0.14,225),('La(a)','Element',4.9,194),
 ('La(b)','Element',6.3,225),('Li','Element',4e-4,229),('Mo','Element',0.92,229),
 ('Nb','Element',9.26,229),('Os','Element',0.65,194),('Pa','Element',1.4,139),
 ('Pb','Element',7.19,225),('Re','Element',2.4,194),('Rh','Element',3.25e-4,225),
 ('Ru','Element',0.49,194),('Si:B','Element',0.4,227),('Sn(b)','Element',3.72,141),
 ('Ta','Element',4.48,229),('Tc','Element',9.25,194),('Th(a)','Element',1.37,225),
 ('Ti','Element',0.39,194),('Tl','Element',2.39,194),('U(a)','Element',0.68,63),
 ('U(b)','Element',1.8,136),('V','Element',5.03,229),('W(a)','Element',0.015,229),
 ('W(b)','Element',2.5,223),('Yb','Element',1.4,225),('Zn','Element',0.855,194),
 ('Zr','Element',0.55,194),
 # Clathrate / 插层
 ('Ba8Si46','Clathrate',8.07,223,'COD:223'),
 ('C6Ca','Intercalated',11.5,194),('C6Li3Ca2','Intercalated',11.15,194),
 ('C8K','Intercalated',0.14,194),('C8KHg','Intercalated',1.4,194),
 ('C6K','Intercalated',1.5,194),('C3K','Intercalated',3.0,194),
 ('C3Li','Intercalated',0.35,194),('C2Li','Intercalated',1.9,194),
 ('C3Na','Intercalated',3.05,194),('C2Na','Intercalated',5.0,194),
 ('C8Rb','Intercalated',0.025,194),('C6Sr','Intercalated',1.65,194),
 ('C6Yb','Intercalated',6.5,194),
 # 化合物
 ('Sr2RuO4','Compound',0.93,139),('C60Cs2Rb','Compound',33,225),
 ('C60K3','Compound',19.8,204),('C60RbX','Compound',28,225),('C60Cs3','Compound',38,225),
 ('FeB4','Compound',2.9,58),('InN','Compound',3,186),('In2O3','Compound',3.3,206),
 ('LaB6','Compound',0.45,221),('MgB2','Compound',39,191),('Nb3Al','Compound',18,223),
 ('NbC1-xNx','Compound',17.8,225),('Nb3Ge','Compound',23.2,223),('NbO','Compound',1.38,221),
 ('NbN','Compound',16,225),('Nb3Sn','Compound',18.3,223,'COD:223'),('NbTi','Compound',10,229),
 ('SiC:B','Compound',1.4,216),('SiC:Al','Compound',1.5,216),('TiN','Compound',5.6,225),
 ('V3Si','Compound',17,223),('YB6','Compound',8.4,221),('ZrN','Compound',10,225),
 ('ZrB12','Compound',6.0,225),('UTe2','Compound',2.10,71),
 ('CuBa0.15La1.85O4','Cuprate',52.5,139),
 # 铜基
 ('YBCO','Cuprate',95,47,'COD:47'),('EuBCO','Cuprate',93,47),('GdBCO','Cuprate',91,47),
 ('BSCCO','Cuprate',104,64),('HBCCO','Cuprate',135,123),
 # 铁基
 ('SmFeAs(O,F)','Iron-based',55,129),('CeFeAs(O,F)','Iron-based',41,129),
 ('LaFeAs(O,F)','Iron-based',26,129),('LaFeSiH','Iron-based',11,129),
 ('LaFePO','Iron-based',4,129),('FeSe:SrTiO3','Iron-based',80,129),
 ('(Ba,K)Fe2As2','Iron-based',38,139),('NaFeAs','Iron-based',20,129),
 # 镍基
 ('La3Ni2O7','Oxonickelate',80,63,'COD:63'),
 # 氢化物 (高压相, COD 无记录, 文献值)
 ('H3S','Polyhydride',203,229),('LaH10','Polyhydride',250,225),('CaH6','Polyhydride',215,229),
]

rows = []
for item in M:
    name, cls, tc, sg = item[0], item[1], item[2], item[3]
    src = item[4] if len(item) > 4 else ''
    pg = SG2PG.get(sg, '?')
    cand = pg in CANDIDATE_PGS
    rows.append((name, cls, tc, sg, pg, '候选' if cand else '非候选', src))

print(f"{'材料':<20}{'类':<14}{'Tc(K)':<10}{'sg':<5}{'点群':<6}{'判定':<6}确认源")
print('-'*76)
for r in rows:
    print(f"{r[0]:<20}{r[1]:<14}{str(r[2]):<10}{r[3]:<5}{r[4]:<6}{r[5]:<6}{r[6]}")

n_cand = sum(1 for r in rows if r[5]=='候选')
print(f'\n总计 {len(rows)} 种: 候选空间群 {n_cand} ({n_cand/len(rows)*100:.1f}%), 非候选 {len(rows)-n_cand} ({(len(rows)-n_cand)/len(rows)*100:.1f}%)')
print(f'\n非候选清单 (判据排除拓扑超导候选, 需区分 S1 体超导路径):')
for r in rows:
    if r[5]=='非候选':
        print(f'  {r[0]:<20} sg={r[3]:<4} {r[4]:<6} Tc={r[2]}')
