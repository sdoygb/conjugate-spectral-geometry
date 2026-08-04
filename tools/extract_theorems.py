#!/usr/bin/env python3
"""卷1-卷10 定理提取脚本（复用 article_scanner 的提取逻辑）
输出: tools/theorem_candidates.json
"""
import os, re, json, glob

ARTICLES_DIR = 'app/articles'
OUT = 'tools/theorem_candidates.json'

# 提取正则（与 article_scanner.py 一致）
BOLD_PATTERN = re.compile(
    r'^\*\*(定理|命题|公理|引理|推论)\s*([\d\.]*)\s*(?:[（(]([^）)]*)[）)])?[。．.]?\*\*',
    re.MULTILINE
)
HEAD_PATTERN = re.compile(
    r'^(?:#{1,3})\s*(定理|命题|公理|引理|推论)\s*([\d\.]*)\s*(?:[（(]([^）)]*)[）)])?',
    re.MULTILINE
)

def extract_from_md(text):
    """返回 [(type, number, title, content)]"""
    results = []
    matches = list(BOLD_PATTERN.finditer(text))
    matches += list(HEAD_PATTERN.finditer(text))
    matches.sort(key=lambda m: m.start())
    # 去重（同一位置的 bold 和 head 都匹配时取 bold）
    dedup = []
    seen_pos = set()
    for m in matches:
        if m.start() in seen_pos:
            continue
        seen_pos.add(m.start())
        dedup.append(m)
    for i, m in enumerate(dedup):
        t, num, title = m.group(1), m.group(2).strip(), (m.group(3) or '').strip()
        end = dedup[i+1].start() if i+1 < len(dedup) else min(m.end() + 1500, len(text))
        content = text[m.end():end].strip()
        if len(content) > 1200:
            content = content[:1200] + '…'
        results.append({'type': t, 'number': num, 'title': title, 'content': content})
    return results

def main():
    candidates = []
    # 卷1-卷10：ZH 版在根目录（1.x~10.x），EN 版在 EN/N/
    zh_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, '[1-9]*.md')) +
                      glob.glob(os.path.join(ARTICLES_DIR, '10*.md')))
    en_dirs = [os.path.join(ARTICLES_DIR, 'EN', str(i)) for i in range(1, 11)]
    en_files = []
    for d in en_dirs:
        en_files += sorted(glob.glob(os.path.join(d, '*.md')))
    en_files = [f for f in en_files if not f.endswith('00_总索引.md')]

    def num_of(fn):
        m = re.match(r'(\d+)\.(\d+)', os.path.basename(fn))
        return (int(m.group(1)), int(m.group(2))) if m else (99, 99)

    def sort_key(fn):
        v, s = num_of(fn)
        lang_prio = 0 if 'CN' in os.path.basename(fn) else 1  # ZH 优先
        return (v, s, lang_prio)

    processed = set()
    all_files = sorted(set(zh_files + en_files), key=sort_key)
    for f in all_files:
        base = os.path.basename(f)
        v = num_of(f)[0]
        # 排除 0.x 和 11+
        if v == 0 or v > 10:
            continue
        # ZH 优先：EN 同名跳过（如 1.1_..._EN 与 1.1_..._CN）
        key = f'{v}.{num_of(f)[1]}'
        is_en = '/EN/' in f
        if key in processed:
            continue
        processed.add(key)
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        for cand in extract_from_md(text):
            cand['article'] = base
            cand['volume'] = v
            cand['lang'] = 'EN' if is_en else 'ZH'
            candidates.append(cand)

    # 汇总
    by_vol = {}
    for c in candidates:
        by_vol.setdefault(c['volume'], []).append(c)
    print(f'总候选: {len(candidates)} 条')
    for v in sorted(by_vol):
        types = {}
        for c in by_vol[v]:
            types[c['type']] = types.get(c['type'], 0) + 1
        print(f'  卷{v}: {len(by_vol[v])} 条 {types}')
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(candidates, fh, ensure_ascii=False, indent=1)
    print(f'已保存: {OUT}')

if __name__ == '__main__':
    main()
