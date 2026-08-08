# -*- coding: utf-8 -*-
import io

p = 'zhihu_publish/zhihu_convert.py'
s = io.open(p, encoding='utf-8').read()

old = '''def inline_parse(text):
    """行内解析：公式/代码先保护，再处理粗体/斜体/链接，最后还原。"""
    # 1. 行内公式（先保护；保留定界符内侧首尾空白）
    text = INLINE_MATH_RE.sub(lambda m: _hold(math_img(m.group(1), 1)), text)
    # 2. 行内代码
    text = CODE_RE.sub(lambda m: _hold('<code>' + _esc_attr(m.group(1)) + '</code>'), text)
    # 3. 粗体（递归解析内容，共享全局占位符池）
    text = BOLD_RE.sub(lambda m: '<b>' + inline_parse(m.group(1)) + '</b>', text)
    # 4. 斜体
    text = ITALIC_RE.sub(lambda m: '<i>' + inline_parse(m.group(1)) + '</i>', text)
    # 5. 链接（仅 http/https）
    def link(m):
        url = m.group(2)
        if url.startswith(('http://', 'https://')):
            return f'<a href="{_esc_attr(url)}">{m.group(1)}</a>'
        return m.group(0)
    text = LINK_RE.sub(link, text)
    # 6. 剩余文本 HTML 转义
    text = html_mod.escape(text, quote=False)
    # 7. 还原占位符（公式/代码不转义）
    return _restore(text)'''

new = '''def inline_parse(text):
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
    return _restore(text)'''

assert old in s, 'old block not found'
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('fixed OK')
