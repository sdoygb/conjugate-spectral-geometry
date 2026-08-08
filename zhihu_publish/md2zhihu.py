#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md → 知乎兼容HTML 转换器
用法: python3 md2zhihu.py <input.md> [output.html]
特性:
- $...$ / $$...$$ 公式 → 知乎公式图片 (https://www.zhihu.com/equation?tex=...)
- markdown 表格 → HTML table (extra 扩展)
- 引用块 → blockquote
- 第一行 # 标题 → 提取为文章标题（从正文移除）
"""
import sys, re
from urllib.parse import quote
import markdown

ZH_EQUATION = 'https://www.zhihu.com/equation?tex={}'


def protect_math(text):
    """把 $$...$$ 和 $...$ 替换为知乎公式图片 <img>（先块级后行内）"""
    # 块级 $$...$$
    def blk(m):
        tex = m.group(1).strip()
        return '\n\n<center><img src="%s" alt="公式" /></center>\n\n' % (
            ZH_EQUATION.format(quote(tex, safe='')))
    text = re.sub(r'\$\$(.+?)\$\$', blk, text, flags=re.S)
    # 行内 $...$
    def inl(m):
        tex = m.group(1).strip()
        return '<img src="%s" alt="公式" />' % (
            ZH_EQUATION.format(quote(tex, safe='')))
    text = re.sub(r'(?<!\$)\$([^$\n]+?)\$(?!\$)', inl, text)
    return text


def convert(md_path):
    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    # 提取标题（第一行 # ...）
    title = ''
    m = re.match(r'^#\s+(.+?)\s*$', text, re.M)
    if m:
        title = m.group(1).strip()
        text = text.replace(m.group(0), '', 1)
    text = protect_math(text)
    body = markdown.markdown(text, extensions=['extra', 'sane_lists', 'tables'])
    return title, body


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    md_path = sys.argv[1]
    title, body = convert(md_path)
    out_path = sys.argv[2] if len(sys.argv) > 2 else md_path.replace('.md', '_zhihu.html')
    html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head><meta charset="utf-8"><title>%s</title></head>\n<body>\n%s\n</body>\n</html>' % (title, body)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('标题:', title)
    print('正文长度:', len(body))
    print('已保存:', out_path)
