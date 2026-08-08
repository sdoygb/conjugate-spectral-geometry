# -*- coding: utf-8 -*-
"""修复 zh_convert.py 的 convert_line：保留行尾换行符"""
p = 'tools/zh_convert.py'
s = open(p, encoding='utf-8').read()
old = '''def convert_line(line):
    """转换一个表格行：$ 配对 + 公式转换 + 裸命令处理"""
    line = process_dollar_pairs(line)
    line = tex_to_unicode(line, math=False)
    return line'''
new = '''def convert_line(line):
    """转换一个表格行：$ 配对 + 公式转换 + 裸命令处理（保留行尾换行符）"""
    nl = "\\n" if line.endswith("\\n") else ""
    body = line[:-1] if nl else line
    body = process_dollar_pairs(body)
    body = tex_to_unicode(body, math=False)
    return body + nl'''
assert old in s, 'convert_line pattern not found'
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('convert_line fixed')
