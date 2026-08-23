# -*- coding: utf-8 -*-
"""定点修补 replace_37.py 中 R12c 的跨行字符串"""
p = "tools/replace_37.py"
s = open(p, encoding="utf-8").read()

a = 'r"| 21 cm 线频率 | 1418.83 MHz | 1420.406 MHz | 0.11% |'
b = 'r"""| 21 cm 线频率 | 1418.83 MHz | 1420.406 MHz | 0.11% |'
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)

t = "其几何形式待建立）。\"),"
u = "其几何形式待建立）。\"\"\"),"
assert s.count(t) == 1, s.count(t)
s = s.replace(t, u)

open(p, "w", encoding="utf-8").write(s)
print("patched OK")
