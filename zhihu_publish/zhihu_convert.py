#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共扼谱几何文章库 md → 知乎 OpenAPI 发布格式转换器
按 zhihu-publisher v0.1.10 conversion.md 规范实现（文章类型）。
规则要点：
  # → <h2>；## → <h3>；### → <h3>；####/##### → 加粗段落
  段落 → <p>；空行块 → <p><br></p>；hr → <hr />
  **b** → <b>；*i* → <i>；`c` → <code>；[t](u) → <a>
  列表 → <ul>/<ol><li>；引用 → <blockquote>（多段 <br>）
  行内公式 $..$ → <img eeimg="1" src="//www.zhihu.com/equation?tex=..." alt=".."/>
  块级公式 $$..$$ → <img eeimg="2" .../>（alt 保留定界符内侧首尾空白）
  表格 → <table data-draft-node="block" data-draft-type="table" ...><tbody>（仅 tbody）
用法:
  python3 zhihu_convert.py <input.md>            # 输出 validate 产物（candidate → finalize → latest.json）
  python3 zhihu_convert.py <input.md> --dry      # 只打印转换结果，不写文件
"""
import re
import sys
import os
import json
import html as html_mod
import urllib.parse
import subprocess

# ---------------- 常量 ----------------
HERE = os.path.dirname(os.path.abspath(__file__))
FINALIZE_SCRIPT = os.path.join(HERE, 'finalize_validate_json.py')
TITLE_MAX = 100
BODY_MIN = 9
BODY_MAX = 100000

# ---------------- 行内元素 ----------------
# 占位符（公式、代码先保护，避免被 b/i 正则误伤）
_PH = '\x00{}\x00'

BLOCK_MATH_RE = re.compile(r'\$\$(.+?)\$\$', re.S)
INLINE_MATH_RE = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', re.S)
BOLD_RE = re.compile(r'\*\*(.+?)\*\*(?!\*)', re.S)
ITALIC_RE = re.compile(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)')
CODE_RE = re.compile(r'`([^`\n]+?)`')
LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')


def _esc_attr(s):
    return html_mod.escape(s, quote=True)


def math_img(latex, eeimg):
    """公式 → <img eeimg>。alt 保留 LaTeX 原文（含首尾空白）；src = URL 编码。"""
    src = '//www.zhihu.com/equation?tex=' + urllib.parse.quote(latex, safe='')
    return f'<img eeimg="{eeimg}" src="{src}" alt="{_esc_attr(latex)}" />'


_HOLDERS = []  # 全局占位符池（编号全局唯一，支持递归）


def _hold(s):
    _HOLDERS.append(s)
    return _PH.format(len(_HOLDERS) - 1)


def _restore(text):
    def r(m):
        return _HOLDERS[int(m.group(1))]
    return re.sub(_PH.format(r'(\d+)'), r, text)


def inline_parse(text):
    """行内解析：公式/代码/粗体/斜体/链接均先占位，最后统一还原；
    剩余原始文本才做 HTML 转义，避免转义已生成的标签。"""
    # 1. 行内公式（先保护；保留定界符内侧首尾空白）
    text = INLINE_MATH_RE.sub(lambda m: _hold(math_img(m.group(1), 1)), text)
    # 2. 行内代码
    text = CODE_RE.sub(lambda m: _hold('<code>' + _esc_attr(m.group(1)) + '</code>'), text)
    # 3. 粗体（递归解析内容，结果整体占位）
    text = BOLD_RE.sub(lambda m: _hold('<b>' + inline_parse(m.group(1)) + '</b>'), text)
    # 4. 斜体（结果整体占位）
    text = ITALIC_RE.sub(lambda m: _hold('<i>' + inline_parse(m.group(1)) + '</i>'), text)
    # 5. 链接（仅 http/https；结果整体占位）
    def link(m):
        url = m.group(2)
        if url.startswith(('http://', 'https://')):
            return _hold(f'<a href="{_esc_attr(url)}">{inline_parse(m.group(1))}</a>')
        return m.group(0)
    text = LINK_RE.sub(link, text)
    # 6. 剩余文本 HTML 转义
    text = html_mod.escape(text, quote=False)
    # 7. 还原占位符（公式/代码/标签不转义）
    return _restore(text)


# ---------------- 块级解析 ----------------
def parse_table(lines):
    """表格块：第1行表头(th)，第2行分隔(跳过)，其余 td。单元格仅纯文本+公式。"""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    if len(rows) < 2:
        return ''
    sep = rows[1]
    if all(re.fullmatch(r'[\s:\-]*', c) for c in sep):
        header, data = rows[0], rows[2:]
    else:
        header, data = [], rows  # 无表头行
    out = ['<table data-draft-node="block" data-draft-type="table" data-size="normal" data-row-style="normal"><tbody>']
    if header:
        out.append('<tr>' + ''.join(f'<th>{cell_parse(c)}</th>' for c in header) + '</tr>')
    for r in data:
        out.append('<tr>' + ''.join(f'<td>{cell_parse(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return ''.join(out)


def cell_parse(cell):
    """单元格：仅公式转 img，其余纯文本转义（规范：单元格内仅纯文本）。"""
    holders = []

    def hold(s):
        holders.append(s)
        return _PH.format(len(holders) - 1)

    cell = INLINE_MATH_RE.sub(lambda m: hold(math_img(m.group(1), 1)), cell)
    cell = html_mod.escape(cell, quote=False)
    for i, h in enumerate(holders):
        cell = cell.replace(_PH.format(i), h)
    return cell


def block_math_line(line):
    """独立成行的 $$..$$ 块级公式；返回 img 或 None。"""
    m = BLOCK_MATH_RE.fullmatch(line.strip())
    if m:
        return math_img(m.group(1), 2)
    return None


def split_blocks(lines):
    """按行切块：返回 [(type, content)]，type ∈ heading/h1..h5/para/hr/table/ul/ol/quote/math/list"""
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == '':
            # 空行：统计连续空行；2+ 个 → 输出空段落 <p><br></p>
            j = i
            while j < n and lines[j].strip() == '':
                j += 1
            if j - i >= 2 and blocks:
                blocks.append(('empty', ''))
            i = j
            continue
        # 标题
        m = re.match(r'^(#{1,5})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            blocks.append((f'h{level}', m.group(2).strip()))
            i += 1
            continue
        # 分割线
        if re.fullmatch(r'-{3,}|\*{3,}|_{3,}', line.strip()):
            blocks.append(('hr', ''))
            i += 1
            continue
        # 块级公式（独立行 $$..$$）
        bm = block_math_line(line)
        if bm:
            blocks.append(('math', bm))
            i += 1
            continue
        # 表格
        if line.strip().startswith('|'):
            j = i
            while j < n and lines[j].strip().startswith('|'):
                j += 1
            blocks.append(('table', '\n'.join(lines[i:j])))
            i = j
            continue
        # 引用
        if line.strip().startswith('>'):
            j = i
            quote_parts = []
            while j < n:
                s = lines[j].strip()
                if s == '':
                    # 引用内空行：若后面还是引用 → <br>
                    k = j + 1
                    while k < n and lines[k].strip() == '':
                        k += 1
                    if k < n and lines[k].strip().startswith('>'):
                        quote_parts.append('<br>')
                        j = k
                        continue
                    break
                if s.startswith('>'):
                    quote_parts.append(s.lstrip('>').strip())
                    j += 1
                else:
                    break
            blocks.append(('quote', '\n'.join(quote_parts)))
            i = j
            continue
        # 无序列表
        if re.match(r'^[-*]\s+', line):
            j = i
            items = []
            while j < n and re.match(r'^[-*]\s+', lines[j]):
                items.append(re.sub(r'^[-*]\s+', '', lines[j]).strip())
                j += 1
            blocks.append(('ul', '\n'.join(items)))
            i = j
            continue
        # 有序列表
        if re.match(r'^\d+\.\s+', line):
            j = i
            items = []
            while j < n and re.match(r'^\d+\.\s+', lines[j]):
                items.append(re.sub(r'^\d+\.\s+', '', lines[j]).strip())
                j += 1
            blocks.append(('ol', '\n'.join(items)))
            i = j
            continue
        # 代码块
        if line.strip().startswith('```'):
            j = i + 1
            code_lines = []
            while j < n and not lines[j].strip().startswith('```'):
                code_lines.append(lines[j])
                j += 1
            lang = line.strip()[3:].strip()
            blocks.append(('code', (lang, '\n'.join(code_lines))))
            i = j + 1
            continue
        # 普通段落（连续非空行）
        j = i
        para = []
        while j < n:
            s = lines[j]
            if s.strip() == '':
                break
            if re.match(r'^(#{1,5})\s+', s) or re.fullmatch(r'-{3,}|\*{3,}|_{3,}', s.strip()):
                break
            if s.strip().startswith(('|', '>', '```')):
                break
            if re.match(r'^[-*]\s+', s) or re.match(r'^\d+\.\s+', s):
                break
            if block_math_line(s):
                break
            para.append(s.strip())
            j += 1
        blocks.append(('para', ' '.join(para)))
        i = j
    return blocks


def render_blocks(blocks):
    out = []
    for typ, content in blocks:
        if typ == 'empty':
            out.append('<p><br></p>')
        elif typ == 'hr':
            out.append('<hr />')
        elif typ == 'h1':
            out.append(f'<h2>{inline_parse(content)}</h2>')
        elif typ == 'h2':
            out.append(f'<h3>{inline_parse(content)}</h3>')
        elif typ == 'h3':
            out.append(f'<h3>{inline_parse(content)}</h3>')
        elif typ in ('h4', 'h5'):
            out.append(f'<p><b>{inline_parse(content)}</b></p>')
        elif typ == 'math':
            out.append(content)
        elif typ == 'para':
            if content:
                out.append(f'<p>{inline_parse(content)}</p>')
        elif typ == 'table':
            out.append(parse_table(content.split('\n')))
        elif typ == 'quote':
            parts = [inline_parse(p) for p in content.split('\n')]
            out.append('<blockquote>' + '<br>'.join(parts) + '</blockquote>')
        elif typ in ('ul', 'ol'):
            tag = 'ul' if typ == 'ul' else 'ol'
            items = [f'<li>{inline_parse(it)}</li>' for it in content.split('\n') if it.strip()]
            out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>')
        elif typ == 'code':
            lang, code = content
            out.append(f'<pre lang="{_esc_attr(lang)}">{_esc_attr(code)}</pre>')
    return ''.join(out)


# ---------------- 安全与长度检查 ----------------
DANGEROUS_RE = re.compile(
    r'<\s*(script|iframe|object|embed|form|input|style|link|meta)\b|'
    r'on\w+\s*=|javascript\s*:',
    re.I,
)


def text_len(html_str):
    return len(re.sub(r'<[^>]+>', '', html_str))


# ---------------- 主流程 ----------------
def convert(md_path):
    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    # 标题：第一个 # 行
    title = ''
    for line in lines:
        m = re.match(r'^#\s+(.*)', line)
        if m:
            title = m.group(1).strip()
            break
    if not title:
        title = os.path.basename(md_path).replace('.md', '')
    # 标题内公式：去定界符保留文本
    title = re.sub(r'\$\$(.+?)\$\$', r'\1', title, flags=re.S)
    title = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', r'\1', title, flags=re.S)
    title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)

    blocks = split_blocks(lines)
    body = render_blocks(blocks)

    # 长度检查
    if len(title) > TITLE_MAX:
        raise ValueError(f'标题超长: {len(title)} > {TITLE_MAX}')
    n = text_len(body)
    if n < BODY_MIN or n > BODY_MAX:
        raise ValueError(f'正文长度越界: {n}（要求 {BODY_MIN}~{BODY_MAX}）')
    # 安全检查
    if DANGEROUS_RE.search(body):
        raise ValueError('正文包含危险标签/属性，已拒绝')
    # config
    has_heading = bool(re.search(r'<h[23]>', body))
    config = {
        'topics': [],
        'tableOfContentsEnabled': has_heading,
        'creationStatement': {'disclaimer_type': 'none', 'disclaimer_status': 'close'},
        'commentPermission': 'all',
    }
    payload = {
        'type': 'article',
        'title': title,
        'body': body,
        'media': [],
        'linkCard': None,
        'config': config,
    }
    return payload


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry' in sys.argv[1:]
    if not args:
        print('用法: python3 zhihu_convert.py <input.md> [--dry]')
        return 1
    md = args[0]
    if not os.path.exists(md):
        print(f'!! 文件不存在: {md}')
        return 1
    try:
        payload = convert(md)
    except ValueError as e:
        print(f'!! 转换失败: {e}')
        return 1
    if dry:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    # 写 validate 产物：.candidate.json → finalize 脚本 → latest.json
    out_dir = os.path.join(HERE, '.zhihu-publish-output', 'validate')
    os.makedirs(out_dir, exist_ok=True)
    cand = os.path.join(out_dir, '.candidate.json')
    with open(cand, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    if not os.path.exists(FINALIZE_SCRIPT):
        print(f'!! 缺少 finalize_validate_json.py: {FINALIZE_SCRIPT}')
        return 1
    r = subprocess.run(['python3', FINALIZE_SCRIPT, cand], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print('!! finalize 失败:', r.stderr.strip())
        return 1
    print(f'✓ 转换完成: {os.path.join(out_dir, "latest.json")}')
    print(f'  标题: {payload["title"]}')
    print(f'  正文纯文本 {text_len(payload["body"])} 字, HTML {len(payload["body"])} 字符')
    return 0


if __name__ == '__main__':
    sys.exit(main())
