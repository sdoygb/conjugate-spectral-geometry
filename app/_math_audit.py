# -*- coding: utf-8 -*-
"""
math_audit.py - 全库「数学运算断言」零 token 扫描器。

思路：历史文件的心算错误集中在「纯数值链式等式」（A = B = C 或 expr = 数字），
这类可被 LaTeX→sympy 自动解析并逐段验证，无需 LLM。
本脚本只报告「能被完整机解 且 验证失败」的可疑点，供后续定点修正。

用法：
    python3 _math_audit.py [文件或目录] [--threshold 1e-5] [--top N]
"""
import os
import re
import sys
import argparse
import glob

import sympy
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, convert_xor, implicit_multiplication,
    rationalize, auto_symbol, split_symbols, implicit_multiplication_application,
)

_trans = tuple(standard_transformations) + (
    convert_xor, implicit_multiplication, rationalize)

# 相对误差分档：<OK_REL 舍入噪声（视为正确）；<=GRID_REL 灰色（LLM/人工复核）；>=BAD_REL 显著错误（几乎必错）
_OK_REL   = 1e-5
_GRID_REL = 5e-4
_BAD_REL  = 1e-2

# 允许出现在行内但在 sympy 中应去除/忽略的噪声
_RM_PATS = [
    (r"\$", ""),
    (r"\,", ""),
    (r"\cdot", "*"),
    (r"×", "*"),
    (r"\times", "*"),
    (r"÷", "/"),
    (r"−", "-"),
    (r"—", ""), (r"—", ""),
    (r"\ ", ""),
]

def _conv_frac(tex: str) -> str:
    """把 \frac{a}{b} 递归转成 (a)/(b)。"""
    while r"\frac" in tex:
        m = re.search(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", tex)
        if not m:
            break
        tex = tex[:m.start()] + f"({m.group(1)})/({m.group(2)})" + tex[m.end():]
    return tex

def _conv_sqrt(tex: str) -> str:
    while r"\sqrt" in tex:
        m = re.search(r"\\sqrt(?:\[([^{}]*)\])?\{([^{}]*)\}", tex)
        if not m:
            break
        n = m.group(1) or "Rational(1,2)"
        inner = m.group(2)
        tex = tex[:m.start()] + f"({inner})**({n})" + tex[m.end():]
    return tex

def _clean(tex: str) -> str:
    tex = _conv_frac(tex)
    tex = _conv_sqrt(tex)
    for pat, rep in _RM_PATS:
        tex = tex.replace(pat, rep)
    tex = tex.replace("\\left", "").replace("\\right", "")
    # 末尾 '°' 等角标移除
    tex = tex.strip()
    return tex

def _try_parse(part: str):
    """尝试把一段 LaTeX 解析为 sympy 表达式；失败返回 None。"""
    p = _clean(part).strip()
    if not p:
        return None
    # 去除首尾孤立的括号不平衡导致的杂项
    try:
        e = parse_expr(p, transformations=_trans, local_dict={"pi": sympy.pi, "Pi": sympy.pi, "E": sympy.E})
    except Exception:
        return None
    if not isinstance(e, sympy.Expr) or isinstance(e, sympy.Tuple):
        return None
    if e.is_number:
        return e
    # 允许含常见无量纲符号(pi/sqrt数字)之外，含自由符号则不要乱判数值
    fs = e.free_symbols
    if fs and not fs <= {sympy.pi}:
        return None
    return e.evalf() if fs else e

def _digits_sum_int(x):
    """整数逐位数字和；非整数返回 None。"""
    if not isinstance(x, sympy.Expr) or not x.is_Integer:
        return None
    s = str(abs(int(x)))
    return sum(int(c) for c in s)


def _is_concat(big, small):
    """拼接数字串启发式：big 为连写枚举（如 43210），其逐位数字和 == small（如 10）。
    这类是 LaTeX 里 4+3+2+1+0 被连写成一个整数，不是真心算错误。"""
    bs = _digits_sum_int(big)
    if bs is None:
        return False
    try:
        if small.is_number and abs(sympy.N(small, 15) - bs) < 1e-6 \
                and (not small.is_Integer or int(small) != int(big)):
            return True
    except Exception:
        return False
    return False


def validate_line(line: str):
    """返回列表 [(lhs, rhs, rel)]，只针对可机解段。空段返回 None 表示无机解内容。"""
    if "=" not in line and "≈" not in line and not re.search(r"\d", line):
        return None
    # 只取 LaTeX 数学段（$...$ 或 $$...$$），无 $ 时用整行
    segs = re.findall(r"\$\$(.*?)\$\$", line, re.S)
    if not segs:
        segs = re.findall(r"\$(.*?)\$", line, re.S)
    if not segs:
        segs = [line]
    out = []
    for seg in segs:
        # LaTeX 内若含 \begin{align} 等块，跳过（太复杂）
        if r"\begin" in seg or r"\text{" in seg:
            continue
        raw_parts = re.split(r"[=≈]", seg)
        # [过滤1] 列表序号剥离：首个 part 是 1~3 位纯整数，且次 part 含非数值文本 => 是"6." 这类序号
        if len(raw_parts) >= 2 and re.fullmatch(r"\d{1,3}", raw_parts[0].strip()) \
                and re.search(r"[^\d.,;:\-\s]|[#—→：]", raw_parts[1]):
            raw_parts = raw_parts[1:]
        # 只验证「相邻两侧都是纯数值、且两侧原文都不含非 ASCII 记号」的子对，保住 recall 且信号干净
        for i in range(len(raw_parts) - 1):
            if re.search(r"[^\x00-\x7f]", raw_parts[i]) or re.search(r"[^\x00-\x7f]", raw_parts[i + 1]):
                continue  # 任一侧含 unicode（中国/希腊字母、带下标量）=> 记号对，跳过
            a = _try_parse(raw_parts[i])
            b = _try_parse(raw_parts[i + 1])
            if a is None or b is None:
                continue
            # [过滤2] 拼接数字串：连写枚举（43210 = 10）视为正确写法，跳过
            if _is_concat(a, b) or _is_concat(b, a):
                continue
            try:
                va = sympy.N(a, 15)
                vb = sympy.N(b, 15)
            except Exception:
                continue
            if not (va.is_real and vb.is_real):
                continue
            rel = 0.0
            if not (va == vb):
                denom = abs(vb)
                rel = abs(va - vb) / (denom if denom else 1.0)
            out.append((sympy.sstr(a)[:40], sympy.sstr(b)[:40], rel))
    return out

def audit_file(path: str, threshold: float):
    findings = []
    total_chained = 0
    n_grid = 0      # 灰色（1e-5 ~ 5e-4）
    n_bad = 0       # 显著错误（5e-4 ~ 1e-2）
    n_severe = 0    # 重大错误（>= 1e-2）
    try:
        content = open(path, encoding="utf-8").read()
    except Exception as e:
        return findings, total_chained, n_grid, n_bad, n_severe
    for ln_no, line in enumerate(content.split("\n"), 1):
        r = validate_line(line)
        if not r:
            continue
        for a, b, rel in r:
            total_chained += 1
            if rel <= _OK_REL:
                continue
            grade = "grid" if rel <= _GRID_REL else ("bad" if rel <= _BAD_REL else "severe")
            findings.append((ln_no, line.strip(), a, b, rel, grade))
            if grade == "grid":
                n_grid += 1
            elif grade == "bad":
                n_bad += 1
            else:
                n_severe += 1
    return findings, total_chained, n_grid, n_bad, n_severe

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="articles")
    ap.add_argument("--threshold", type=float, default=1e-5)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--grid", action="store_true",
                    help="也打印灰色(1e-5~5e-4)舍入候选；默认只打印显著(>=5e-4)错误")
    args = ap.parse_args()

    if os.path.isdir(args.path):
        files = sorted(glob.glob(os.path.join(args.path, "**", "*.md"), recursive=True))
    else:
        files = [args.path]

    tot_chain = tot_grid = tot_bad = tot_severe = 0
    per_file = []
    for f in files:
        finds, ch, ng, nb, ns = audit_file(f, args.threshold)
        tot_chain += ch
        tot_grid += ng
        tot_bad += nb
        tot_severe += ns
        # 只统计要展示的错误（默认不含灰色）
        shown = finds if args.grid else [x for x in finds if x[4] > _GRID_REL]
        if shown:
            per_file.append((f, finds))
    per_file.sort(key=lambda x: -max((fd[4] for fd in x[1]), default=0))

    print(f"== 扫描 {len(files)} 个文件 ==")
    print(f"可机解链式等式段: {tot_chain}  |  失败点: 灰色={tot_grid} 显著={tot_bad} 重大={tot_severe}")
    print()
    shown_files = 0
    for f, finds in per_file:
        to_show = finds if args.grid else [x for x in finds if x[4] > _GRID_REL]
        if not to_show:
            continue
        if shown_files >= args.top:
            print(f"... (另有 {len(per_file)-shown_files} 个文件含误差点，未全部显示)")
            break
        shown_files += 1
        print(f"### {f}  ({len(to_show)} 处≥灰色)")
        for ln, line, a, b, rel, grade in to_show:
            tag = {"severe": "[重大]", "bad": "[显著]", "grid": "[灰色]"}[grade]
            print(f"  L{ln} {tag} rel={rel:.1e}  原文: {line[:100]}")
            print(f"        {a}  ≠ {b}")
        print()
    print(f"汇总: 文件数={len(files)}, 链式段={tot_chain}, "
          f"灰色={tot_grid}, 显著={tot_bad}, 重大={tot_severe}")

if __name__ == "__main__":
    main()