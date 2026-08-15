"""用 MP API 独立确认关键超导材料的空间群与磁性（Q3）
用法: python3 query_materials.py <起始> <结束>  # 对 MATERIALS[start:end] 查询
"""
import requests, json, time, os, sys

KEY = 'dAZ3RHLu70nSi1SFo4a75MPY9Zzkm8Ia'
HEADERS = {'X-API-KEY': KEY, 'Accept': 'application/json',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'}
BASE = 'https://api.materialsproject.org/materials/summary/'
OUT = os.path.join(os.path.dirname(__file__), 'mp_materials_check.json')

# (材料名, 化学式查询, 预期空间群号, 类别)
MATERIALS = [
    # 拓扑超导候选组（正向覆盖）
    ('Bi2Se3', 'Bi2Se3', 166, 'topo_SC_candidate'),
    ('Bi2Te3', 'Bi2Te3', 166, 'topo_SC_candidate'),
    ('Sb2Te3', 'Sb2Te3', 166, 'topo_SC_candidate'),
    ('MnBi2Te4', 'MnBi2Te4', 164, 'topo_SC_candidate'),
    ('SnTe', 'SnTe', 225, 'topo_SC_candidate'),
    ('YPtBi', 'YPtBi', 216, 'topo_SC_candidate'),
    ('LuPtBi', 'LuPtBi', 216, 'topo_SC_candidate'),
    ('UPt3', 'UPt3', 194, 'topo_SC_candidate'),
    ('PrOs4Sb12', 'PrOs4Sb12', 204, 'topo_SC_candidate'),
    ('Bi2Pd', 'Bi2Pd', 227, 'topo_SC_candidate'),
    # 排除预言组
    ('Sr2RuO4', 'Sr2RuO4', 139, 'exclusion_prediction'),
    ('UTe2', 'UTe2', 71, 'exclusion_prediction'),
    # 代表性 BCS（对照）
    ('MgB2', 'MgB2', 191, 'BCS'),
    ('Nb3Sn', 'Nb3Sn', 223, 'BCS'),
    ('YBCO', 'YBa2Cu3O7', 47, 'cuprate'),
    ('FeSe', 'FeSe', 129, 'iron_based'),
    ('La3Ni2O7', 'La3Ni2O7', 63, 'nickelate'),
    ('Ba8Si46', 'Ba8Si46', 223, 'clathrate'),
    ('LaH10', 'LaH10', 225, 'hydride'),
    ('H3S', 'H3S', 229, 'hydride'),
    ('LiFeAs', 'LiFeAs', 129, 'iron_based'),
    ('CaKFe4As4', 'CaKFe4As4', 139, 'iron_based'),
]

def load():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return {}

def save(res):
    with open(OUT, 'w') as f:
        json.dump(res, f, indent=1, ensure_ascii=False)

def query_formula(formula):
    for attempt in range(4):
        try:
            r = requests.get(BASE + f'?formula={formula}&_fields=material_id,formula_pretty,symmetry,ordering,is_magnetic',
                             headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json().get('data', [])
            elif r.status_code == 429:
                time.sleep(5)
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return None

def main():
    start, end = int(sys.argv[1]), int(sys.argv[2])
    results = load()
    for i in range(start, min(end, len(MATERIALS))):
        name, formula, exp_sg, cat = MATERIALS[i]
        if name in results:
            continue
        data = query_formula(formula)
        if data is not None:
            phases = [{'sg': d.get('symmetry',{}).get('number'), 'sym': d.get('symmetry',{}).get('symbol'),
                       'ordering': d.get('ordering'), 'mag': d.get('is_magnetic'),
                       'mid': d['material_id'], 'formula': d['formula_pretty']} for d in data]
            results[name] = {'expected_sg': exp_sg, 'category': cat, 'phases': phases}
            save(results)
            print(f'== {name} (预期 sg{exp_sg}) ==', flush=True)
            for p in phases[:6]:
                print(f'   sg{p["sg"]} {p["sym"]} | {p["ordering"]} | {p["mid"]} {p["formula"]}', flush=True)
        time.sleep(0.4)
    print(f'完成 {start}-{end}, 已收集 {len(results)} 个', flush=True)

if __name__ == '__main__':
    main()
