# -*- coding: utf-8 -*-
"""把 zenodo_260808_all.json 清单同步到 zenodo_中英文对照表.md（三个副本）"""
import json, re, glob

# 1. 读清单
items = json.load(open('zenodo_tools/zenodo_260808_all.json'))
by_no = {it['no']: it for it in items}

# 2. 读对照表
path = 'app/articles/ZH/zenodo_中英文对照表.md'
txt = open(path, encoding='utf-8').read()

# 3. 逐行替换中文DOI（第三列）
lines = txt.split('\n')
new_lines = []
stats = {'updated': 0, 'unchanged': 0}
for ln in lines:
    if ln.startswith('| ') and len(ln.split('|')) >= 6:
        parts = ln.split('|')
        no = parts[1].strip()
        if no in by_no and by_no[no]['mode'] == 'update':
            old_doi = parts[3].strip()
            new_doi = '10.5281/zenodo.' + str(by_no[no]['record_id'])
            if old_doi != new_doi:
                parts[3] = ' ' + new_doi + ' '
                ln = '|'.join(parts)
                stats['updated'] += 1
            else:
                stats['unchanged'] += 1
    new_lines.append(ln)

# 4. 追加 17 行 create 条目（插在表格末尾、'## 重复发布的 DOI' 之前）
create_items = [it for it in items if it['mode'] == 'create']
create_items.sort(key=lambda it: tuple(int(x) for x in it['no'].split('.')))

new_rows = []
for it in create_items:
    no = it['no']
    md_files = glob.glob(f'app/articles/ZH/{no}_*_CN_260808.md')
    title = ''
    if md_files:
        m = re.search(r'^#\s+(.+)$', open(md_files[0], encoding='utf-8').read(), re.M)
        title = m.group(1).strip() if m else ''
    else:
        print(f'  [警告] 未找到 {no} 的 md 文件')
    doi = '10.5281/zenodo.' + str(it['record_id'])
    new_rows.append(f'| {no} | {title} | {doi} |  |  |')

# 找插入位置：'## 重复发布的 DOI' 之前，紧贴最后一行表格行
idx = next(i for i, ln in enumerate(new_lines) if ln.startswith('## 重复发布的 DOI'))
j = idx - 1
while j >= 0 and not new_lines[j].startswith('|'):
    j -= 1
new_lines[j+1:j+1] = new_rows

txt2 = '\n'.join(new_lines)

# 5. 更新文件头统计
old_hdr = '共 **117** 篇，中英文各 **117** 条记录，全部配对。'
new_hdr = ('共 **134** 篇中文、**117** 篇英文记录。'
           '中文 117 篇于 2026-08-08 更新至 260808 版（version=260808），'
           '并新增 17 篇（10.21~10.36、11.12，暂无英文版）。')
if old_hdr in txt2:
    txt2 = txt2.replace(old_hdr, new_hdr)
else:
    print('  [警告] 未找到文件头统计行，请手动检查')

# 6. 写回三个副本
for p in ['app/articles/ZH/zenodo_中英文对照表.md',
          'app/articles/zenodo_中英文对照表.md',
          'zenodo_中英文对照表.md']:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(txt2)
    print('已更新:', p)

print('DOI 替换:', stats['updated'], '| 未变:', stats['unchanged'], '| 新增行:', len(new_rows))
