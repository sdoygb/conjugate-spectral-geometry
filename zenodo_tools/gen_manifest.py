# -*- coding: utf-8 -*-
"""生成更新/新建清单：对照表(117中文DOI) × 本地PDF(134个260808版)"""
import re, json, os

# 1. 解析对照表
rows = []
with open('app/articles/zenodo_中英文对照表.md', encoding='utf-8') as f:
    for line in f:
        m = re.match(r'\|\s*([\d.]+)\s*\|\s*([^|]+?)\s*\|\s*10\.5281/zenodo\.(\d+)\s*\|', line)
        if m:
            rows.append({'no': m.group(1), 'title_zh': m.group(2).strip(), 'recid': m.group(3)})
print(f'对照表解析: {len(rows)} 条')

# 2. 本地 PDF 列表
pdfs = sorted(os.listdir('app/articles/PDF'))
pdfs = [p for p in pdfs if p.endswith('.pdf') and '_CN_260808' in p]
print(f'本地 PDF(CN_260808): {len(pdfs)} 个')

# 3. 匹配更新清单
update_manifest = []
missing = []
for row in rows:
    no, title, recid = row['no'], row['title_zh'], row['recid']
    # 匹配：编号一致 + CN_260808
    cands = [p for p in pdfs if p.startswith(no + '_') and p.endswith('_CN_260808.pdf')]
    if len(cands) == 1:
        update_manifest.append({'no': no, 'title': title, 'recid': recid, 'pdf': cands[0]})
    elif len(cands) > 1:
        print(f'  [多匹配] {no}: {cands}')
    else:
        missing.append({'no': no, 'title': title, 'recid': recid})

print(f'更新清单: {len(update_manifest)} 条, 缺失PDF: {len(missing)}')
for x in missing:
    print('  缺:', x['no'], x['title'], x['recid'])

# 4. 新建清单：PDF 中未被更新清单覆盖的
covered = set(m['pdf'] for m in update_manifest)
new_pdfs = [p for p in pdfs if p not in covered]
print(f'未覆盖 PDF（潜在新建）: {len(new_pdfs)}')
for p in new_pdfs:
    print('  NEW:', p)

json.dump(update_manifest, open('zenodo_tools/update_manifest.json', 'w'), ensure_ascii=False, indent=2)
json.dump(new_pdfs, open('zenodo_tools/create_pdfs.json', 'w'), ensure_ascii=False, indent=2)
print('清单已保存: zenodo_tools/update_manifest.json, zenodo_tools/create_pdfs.json')
