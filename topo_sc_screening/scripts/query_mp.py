"""Materials Project 全库候选空间群统计（断点续跑）
用法: python3 query_mp.py <起始索引> <结束索引>   # 对 sg_numbers[start:end] 查询
结果累积保存到 mp_sg_stats.json
"""
import requests, json, time, os, sys

KEY = 'dAZ3RHLu70nSi1SFo4a75MPY9Zzkm8Ia'
HEADERS = {'X-API-KEY': KEY, 'Accept': 'application/json',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'}
BASE = 'https://api.materialsproject.org/materials/summary/'
OUT = os.path.join(os.path.dirname(__file__), 'mp_sg_stats.json')

CANDIDATE_PGS = ['D6h','D3h','D3d','Oh','Td','C3i','C3v','C3h','C6h','C6v','Th']

def build_sg2pg():
    import spglib
    sg2pg = {}
    for hall in range(1, 531):
        try:
            t = spglib.get_spacegroup_type(hall)
            num = t['number']
            if num not in sg2pg:
                sg2pg[num] = t['pointgroup_schoenflies']
        except Exception:
            pass
    return sg2pg

def load_results():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return {}

def save_results(res):
    with open(OUT, 'w') as f:
        json.dump(res, f, indent=1)

def query_sg(sg):
    for attempt in range(4):
        try:
            r = requests.get(BASE + f'?spacegroup_number={sg}&_fields=material_id', headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json().get('meta', {}).get('total_doc', 0)
            elif r.status_code == 429:
                time.sleep(5)
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return None

def main():
    start, end = int(sys.argv[1]), int(sys.argv[2])
    sg2pg = build_sg2pg()
    sg_numbers = sorted([sg for sg, pg in sg2pg.items() if pg in CANDIDATE_PGS])
    results = load_results()
    for i in range(start, min(end, len(sg_numbers))):
        sg = sg_numbers[i]
        if str(sg) in results:
            continue
        n = query_sg(sg)
        if n is not None:
            results[str(sg)] = n
            save_results(results)
            print(f'  sg{sg} ({sg2pg[sg]}): {n}', flush=True)
        time.sleep(0.3)
    print(f'完成 {start}-{end}, 已收集 {len(results)} 个', flush=True)

if __name__ == '__main__':
    main()
