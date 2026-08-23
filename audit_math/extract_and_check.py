#!/usr/bin/env python3
"""数学运算审计管线 v4 —— 跨行合并强化 + 百分号上下文感知 + sympy 自由符号白名单
用法：python3 audit_math/extract_and_check.py [files...]
输出：audit_math/findings_v4.json
v4 相对 v3 的改进：
  1. 跨行合并强化：prev 以 '-'/'−' 结尾且 cur 以数字/括号开头；prev 以数字/括号结尾
     且 cur 以 × * / + 开头或 '-' 后跟数字/括号 → 合并。消除 "= 1 − / 0.209" 类残片。
  2. 百分号上下文：\\% 转义归一；每条 finding 标记 pct_ctx（rhs 或上下文含 %），
     供 LLM 判别 100 倍陷阱是"百分号未换算"还是"真值错误"。
  3. sympy 自由符号白名单：val.free_symbols / rval.free_symbols 非空即跳过，
     替代字符串级 is_pure_numeric 的漏洞（θ_C^0 → 1、S(1/3,1/3,1/3) 等）。
"""
import re, sys, json, glob, math, bisect

# ---------- 单位词表（长优先；% 已移除——百分号感知） ----------
UNITS = ['GeV', 'MeV', 'keV', 'TeV', 'eV', 'm/s', 'm/s²', 'cm', 'mm', 'nm', 'pm', 'fm',
         'km', 'Gyr', 'Myr', 'yr', 'ms', 'ns', 'ps', 'fs', 'mol', 'rad', 'deg',
         'Hz', 'kg', 'g', 'J', 'W', 'C', 'A', 'K', 's', 'm', 'h', 'd', 'L', 'T',
         'N', 'Pa', 'V', 'F', 'H', 'Å']
UNITS.sort(key=len, reverse=True)
MULTI_UNITS = [u for u in UNITS if len(u) >= 2]          # 多字母单位：全局剥离
SINGLE_UNITS = [u for u in UNITS if len(u) == 1]         # 单字母单位：仅数字后剥离
UNIT_ALT = '|'.join(map(re.escape, UNITS))
MULTI_ALT = '|'.join(map(re.escape, MULTI_UNITS))

FUNC_NAMES = ['exp', 'log', 'ln', 'sqrt', 'sin', 'cos', 'tan', 'abs', 'floor', 'ceiling',
              'sign', 'Max', 'Min', 'Rational', 'gamma', 'EulerGamma', 'sinh', 'cosh',
              'tanh', 'asin', 'acos', 'atan']

UNIT_SCALE = {'eV': 1, 'keV': 1e3, 'MeV': 1e6, 'GeV': 1e9,
              's': 1, 'ms': 1e-3, 'ns': 1e-9, 'ps': 1e-12,
              'm': 1, 'cm': 1e-2, 'mm': 1e-3, 'nm': 1e-9, 'pm': 1e-12, 'km': 1e3}

def _units_in(text):
    # 提取文本中的单位（词边界，避免 eV 子串匹配进 MeV/keV/GeV）
    found = []
    for u in UNIT_SCALE:
        if re.search(r'(?<![A-Za-z])' + re.escape(u) + r'(?![A-Za-z])', text):
            found.append(u)
    return found

def is_pure_numeric(expr_str: str) -> bool:
    """仅含数字/运算符/pi/e/白名单函数 → True；含变量/希腊字母 → False"""
    if not expr_str:
        return False
    s = re.sub(r'[0-9.eE+\-*/()\[\],\s]', '', expr_str)
    s = s.replace('pi', '').replace('oo', '')
    for fn in FUNC_NAMES:
        s = s.replace(fn, '')
    s = s.replace('**', '')
    return s == ''

def strip_units(t: str) -> str:
    """单位剥离：
    1. \\mathrm{单位}[^{上标}] 整体删
    2. 裸多字母单位[^{上标}] 全局删
    3. 裸单字母单位 仅紧贴数字时删
    """
    sup = r'(?:\^\{[^{}]*\}|\^.)?'
    # 1. \mathrm{单位}[上标]（先于 text/mathbf 转换）
    t = re.sub(r'\\mathrm\{(' + UNIT_ALT + r')\}' + sup, '', t)
    # 2. 裸多字母单位[上标]
    t = re.sub(r'\b(' + MULTI_ALT + r')\b' + sup, '', t)
    # 3. 裸单字母单位：仅数字紧邻后（10 s → 10，但 (d-1) 的 d 保留）
    t = re.sub(r'(?<=\d)\s*(' + '|'.join(map(re.escape, SINGLE_UNITS)) + r')\b', '', t)
    return t

def latex_to_expr(s: str):
    """LaTeX -> sympy 可解析字符串。失败返回 None。"""
    if not s or len(s) > 3000:
        return None
    t = s
    t = re.sub(r'\\left|\\right', '', t)
    t = t.replace('\\,', '').replace('\\!', '').replace('\\;', '').replace('\\ ', ' ')
    t = t.replace('\\qquad', '').replace('\\quad', '')
    t = re.sub(r'\\text\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\mathit\{([^}]*)\}', r'\1', t)
    # \mathrm{非单位} 保留内容；\mathrm{单位} 由 strip_units 删（此处先保留 \mathrm{} 供 strip_units 识别）
    t = t.replace('\\times', '*').replace('\\cdot', '*')
    t = t.replace('\\approx', '==APPROX==').replace('\\simeq', '==APPROX==')
    t = t.replace('\\pm', '+-').replace('\\mp', '-+')
    t = t.replace('\\to', '->').replace('\\rightarrow', '->').replace('\\Rightarrow', '->')
    t = t.replace('\\propto', '==PROP==')
    # 分式（平衡花括号，支持嵌套）
    def _frac_all(tt):
        while True:
            m = re.search(r'\\frac', tt)
            if not m:
                return tt
            j = tt.find('{', m.end())
            if j == -1:
                return tt
            depth, k = 0, j
            while k < len(tt):
                if tt[k] == '{': depth += 1
                elif tt[k] == '}':
                    depth -= 1
                    if depth == 0: break
                k += 1
            a = tt[j+1:k]
            k2 = k + 1
            while k2 < len(tt) and tt[k2] in ' \t': k2 += 1
            if k2 >= len(tt) or tt[k2] != '{':
                return tt
            depth, k3 = 0, k2
            while k3 < len(tt):
                if tt[k3] == '{': depth += 1
                elif tt[k3] == '}':
                    depth -= 1
                    if depth == 0: break
                k3 += 1
            b = tt[k2+1:k3]
            tt = tt[:m.start()] + f'(({a})/({b}))' + tt[k3+1:]
    t = _frac_all(t)
    t = re.sub(r'\^\{([^{}]*)\}', r'**(\1)', t)
    t = re.sub(r'\^([0-9a-zA-Z])', r'**(\1)', t)
    t = re.sub(r'_\{([^{}]*)\}', r'_\1', t)
    t = re.sub(r'_([0-9a-zA-Z])', r'_\1', t)
    t = t.replace('\\left(', '(').replace('\\right)', ')')
    t = t.replace('\\left[', '[').replace('\\right]', ']')
    t = t.replace('\\left{', '(').replace('\\right}', ')')
    greek = {'\\pi': 'pi', '\\alpha': 'alpha', '\\beta': 'beta', '\\gamma': 'gamma',
             '\\delta': 'delta', '\\Delta': 'Delta', '\\sigma': 'sigma', '\\Sigma': 'Sigma',
             '\\eta': 'eta', '\\theta': 'theta', '\\lambda': 'lambda', '\\mu': 'mu',
             '\\nu': 'nu', '\\omega': 'omega', '\\Omega': 'Omega', '\\rho': 'rho',
             '\\phi': 'phi', '\\varphi': 'phi', '\\epsilon': 'eps', '\\varepsilon': 'eps',
             '\\tau': 'tau', '\\kappa': 'kappa', '\\chi': 'chi', '\\psi': 'psi',
             '\\zeta': 'zeta', '\\Gamma': 'Gamma', '\\Lambda': 'Lambda', '\\xi': 'xi',
             '\\Theta': 'Theta', '\\Phi': 'Phi', '\\Psi': 'Psi', '\\Upsilon': 'Upsilon'}
    for k, v in greek.items():
        t = t.replace(k, v)
    t = t.replace('\\hbar', 'hbar').replace('\\hat', '').replace('\\bar', '')
    t = t.replace('\\tilde', '').replace('\\vec', '').replace('\\sqrt', 'sqrt')
    t = t.replace('\\partial', '').replace('\\nabla', '').replace('\\infty', 'oo')
    t = t.replace('\\equiv', '==').replace('\\ne', '!=').replace('\\le', '<=').replace('\\ge', '>=')
    t = t.replace('\\ldots', '').replace('\\dots', '').replace('\\cdots', '')
    t = t.replace('×', '*').replace('⋅', '*').replace('·', '*')
    t = t.replace('−', '-').replace('–', '-')
    # LaTeX 转义百分号归一（在 % 正则前）
    t = t.replace('\\%', '%')
    # Unicode 上标 → **（2⁷ → 2**7，10⁻¹⁶ → 10**-16）
    sup_map = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
               '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁻': '-', '⁺': '+'}
    def _sup_repl(m):
        sgn = ''
        body = m.group(1)
        if body.startswith('⁻'):
            sgn = '-'; body = body[1:]
        elif body.startswith('⁺'):
            body = body[1:]
        digits = ''.join(sup_map.get(c, '') for c in body)
        return '**' + sgn + (digits or '0')
    t = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)', _sup_repl, t)
    # 百分号感知：数字% → 数字/100
    t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', t)
    # 单位剥离（重构版）
    t = strip_units(t)
    if '\\' in t:
        return None
    t = re.sub(r'(\d)(pi|e|E)\b', r'\1*\2', t)
    t = re.sub(r'[\*\+/\-]\s*$', '', t)
    t = re.sub(r'\(\s*$', '', t)
    if t.strip() in ('', '(', '*', '+', '-'):
        return None
    return t

def sympify_val(expr_str):
    import sympy as sp
    return sp.sympify(expr_str)

# ---------- 跨行合并（v4 强化） ----------
def should_merge(prev: str, cur: str) -> bool:
    p = prev.rstrip()
    if not p:
        return False
    last = p[-1]
    if last in '=≈×*+(,':
        return True
    # prev 以 -/− 结尾（表达式未完，如 "= 1 −"）
    if last in '-−' and (cur[0].isdigit() or cur[0] == '('):
        return True
    # prev 以 / 结尾（如 "4096/" 接 "27"）
    if last == '/' and (cur[0].isdigit() or cur[0] == '('):
        return True
    # 括号不平衡
    if p.count('(') > p.count(')'):
        return True
    if cur[0] in '=≈':
        return True
    # 跨行连乘/连加：prev 数字/括号结尾，cur 以运算符开头
    if (last.isdigit() or last in ')]}') and cur[0] in '×*/+':
        return True
    # 跨行减号：cur 以 - 开头且后随数字/括号（避免误并 markdown 列表 "- 文本"）
    if (last.isdigit() or last in ')]}') and re.match(r'^[−-]\s*[\d(]', cur):
        return True
    return False

def merge_lines(lines):
    blocks = []
    n_merged = 0
    cur, cur_start, offsets = [], 1, [0]
    for i, ln in enumerate(lines, 1):
        stripped = ln.strip()
        if not stripped:
            if cur:
                blocks.append((cur_start, ' '.join(cur), offsets))
            cur, cur_start, offsets = [], i + 1, [0]
            continue
        if cur and should_merge(cur[-1], stripped):
            joined = ' '.join(cur + [stripped])
            offsets.append(len(joined) - len(stripped))
            cur.append(stripped)
            n_merged += 1
        else:
            if cur:
                blocks.append((cur_start, ' '.join(cur), offsets))
            cur, cur_start, offsets = [stripped], i, [0]
    if cur:
        blocks.append((cur_start, ' '.join(cur), offsets))
    return blocks, n_merged

# ---------- 段分割核算 ----------
TRAIL_PUNCT = re.compile(r'[,.;，。；）)\]$]+\s*$')
def clean_dollars(s: str) -> str:
    """去掉数学环境标记 $$ / $（段首段尾）"""
    s = re.sub(r'^\$\$?', '', s)
    s = re.sub(r'\$\$?$', '', s)
    return s

def parse_precision(rhs_str: str):
    """从 rhs 原始字符串提取书写精度容差：10^(指数 - 尾数小数位)。
    例：0.002322 → 1e-6；6.581e-16 → 1e-25；367.7345 → 1e-4。
    返回 None 表示无法解析（用相对阈值兜底）。"""
    s0 = rhs_str.replace(' ', '')
    m = re.match(r'([-+]?\d+(?:\.\d+)?)', s0)
    if not m:
        return None
    mant = m.group(1)
    exp = 0
    # 优先 LaTeX \times 10^{k}，再裸 ×10^k，再 e±k
    m2 = (re.search(r'\\times\s*10\s*\^?\{?([-+]?\d+)\}?', rhs_str)
          or re.search(r'[×x*]\s*10\s*\^?\{?([-+]?\d+)\}?', s0)
          or re.search(r'[eE]([-+]?\d+)', s0))
    if m2:
        exp = int(m2.group(1))
    frac = mant.split('.')[1] if '.' in mant else ''
    return 10.0 ** (exp - len(frac))

def classify(val_f, rhs_val, rhs_str):
    rel = abs(val_f - rhs_val) / abs(rhs_val)
    if rel <= 1e-6:
        return None
    tol = parse_precision(rhs_str)
    if rel <= 1e-3 or (tol is not None and abs(val_f - rhs_val) <= tol):
        return 'rounding'
    if val_f != 0 and rhs_val != 0:
        ratio = val_f / rhs_val
        lg = math.log10(abs(ratio))
        if abs(lg - 2) < 0.02 or abs(lg + 2) < 0.02:
            return 'pct_candidate'
        if abs(lg - round(lg)) < 0.02 and abs(lg) >= 2:
            return 'unit_candidate'
    return 'value_mismatch'

def lineno_at(offsets, pos, start):
    idx = bisect.bisect_right(offsets, pos) - 1
    return start + max(0, idx)

def split_segments(t):
    """按 '=' 切段，返回 [(seg_text, start, end)]；end 为 '=' 前位置（保留 offset 映射）"""
    segs = []
    last = 0
    for mm in re.finditer(r'=', t):
        segs.append((t[last:mm.start()], last, mm.start()))
        last = mm.end()
    segs.append((t[last:], last, len(t)))
    return segs

def check_block(block, fname, start, offsets, out, lines):
    t = block.replace('≈', '=').replace('≃', '=')   # 等长替换，保持位置映射
    segs = split_segments(t)
    seen = set()
    for i in range(len(segs) - 1):
        lhs_raw, ls, _le = segs[i]
        rhs_raw, _rs, _re2 = segs[i + 1]
        # 去标点 → 去 $ 环境标记
        lhs = TRAIL_PUNCT.sub('', lhs_raw.strip()).strip()
        rhs = TRAIL_PUNCT.sub('', rhs_raw.strip()).strip()
        lhs = clean_dollars(lhs).strip()
        rhs = clean_dollars(rhs).strip()
        rhs_norm = re.sub(r'\\pm|\\mp', '±', rhs)
        rhs_main = re.split(r'\s*[±+-]\s*\d', rhs_norm, maxsplit=1)[0].strip()  # ± 误差带取主值
        if rhs_main and re.search(r'\d', rhs_main):
            rhs = rhs_main
        if not re.search(r'\d', lhs) or not re.search(r'\d', rhs):
            continue
        # 列表序号误报
        if re.match(r'^\s*\d+\.\s*(#|\d|[a-zA-Z])', lhs) and not re.search(r'[×x*/\\^]', lhs):
            continue
        # v4: lhs 以运算符开头（含减号）→ 续行残片
        if re.match(r'^[+×*/−-]', lhs):
            continue
        # v4.1: 分子分母不同单位的比值（(1 cm / 265 nm)²）→ 单位剥离破坏数值，跳过
        if re.search(r'(cm|mm|nm|pm|fm|km|MeV|GeV|keV|eV)', lhs_raw) and re.search(r'/|\\div|\\frac', lhs_raw):
            continue
        # lhs → sympy（free_symbols 白名单：符号变量一律跳过，堵住 θ_C^0→1、S(...) 漏洞）
        expr = latex_to_expr(lhs)
        if expr is None:
            continue
        if not is_pure_numeric(expr):
            continue
        try:
            val = sympify_val(expr)
            if not val.is_number or val.free_symbols:
                continue
            val_f = float(val)
        except Exception:
            continue
        # rhs → 数值（% 与 ×10^k、Unicode 上标由 latex_to_expr 统一处理）
        rexpr = latex_to_expr(rhs)
        if rexpr is None or not is_pure_numeric(rexpr):
            continue
        try:
            rval = sympify_val(rexpr)
            if not rval.is_number or rval.free_symbols:
                continue
            rhs_val = float(rval)
        except Exception:
            continue
        if abs(rhs_val) < 1e-300:
            continue
        kind = classify(val_f, rhs_val, rhs)
        if kind == 'unit_candidate':
            lu = _units_in(lhs_raw)
            ru = _units_in(rhs)
            if len(lu) == 1 and len(ru) == 1 and lu[0] != ru[0]:
                expect = UNIT_SCALE[ru[0]] / UNIT_SCALE[lu[0]]
                if abs(math.log10(abs(val_f / rhs_val) / expect)) < 0.02:
                    kind = 'unit_convert'   # 合法单位换算（keV→MeV 等）
        if kind is None:
            continue
        key = lhs[:60] + '|' + rhs[:30]
        if key in seen:
            continue
        seen.add(key)
        lineno = lineno_at(offsets, ls, start)
        ctx = '\n'.join(lines[max(0, lineno - 4):lineno + 1])
        out.append({
            'file': fname, 'line': lineno, 'op': '=',
            'lhs': lhs[:200], 'rhs': rhs[:200], 'pct': '%' in rhs,
            'pct_ctx': '%' in rhs or '%' in ctx,
            'merged': lineno != start,
            'computed': val_f, 'rel_diff': abs(val_f - rhs_val) / abs(rhs_val),
            'kind': kind, 'ctx': ctx
        })

# ---------- 特殊语义检查 ----------
SPECIAL_PATTERNS = [
    (re.compile(r'\(4\\pi\\sigma[^)]*\)\^\{?-1/4\}'), 'gauss_norm_4pi',
     '高斯归一化常数疑为 (4πσ²)^(−1/4)：∫|Ψ|² = √2/2 ≠ 1，应为 (2πσ²)^(−1/4)'),
    (re.compile(r'\(4\\pi\s*\\sigma[^)]*\)\^\{-1/2\}'), 'gauss_norm_4pi_half',
     '扩散核 (4πDτ)^(-1/2) 若写作 (4πσ²)^(-1/2) 且 σ²=Dτ/2 则归一；请人工确认'),
]

def special_checks(text: str, fname: str, out: list):
    for pat, kind, msg in SPECIAL_PATTERNS:
        for m in pat.finditer(text):
            line_no = text[:m.start()].count('\n') + 1
            out.append({
                'file': fname, 'line': line_no, 'op': 'special',
                'lhs': m.group(0), 'rhs': None, 'computed': None,
                'rel_diff': None, 'kind': kind, 'note': msg,
                'ctx': '\n'.join(text.split('\n')[max(0, line_no - 3):line_no + 1])
            })

# ---------- 主流程 ----------
def main():
    files = sys.argv[1:] or sorted(glob.glob('app/articles/*.md'))
    out = []
    n_checked = n_blocks = n_merged = 0
    for f in files:
        try:
            with open(f, encoding='utf-8') as fh:
                lines = fh.readlines()
            text = ''.join(lines)
        except Exception as e:
            print(f'[SKIP] {f}: {e}', file=sys.stderr)
            continue
        n_checked += 1
        for start, block, offsets in merge_lines(lines)[0]:
            n_blocks += 1
            if '=' not in block and '≈' not in block:
                continue
            check_block(block, f, start, offsets, out, lines)
        special_checks(text, f, out)
    # 重新统计合并次数（简单起见：单独跑一遍 merge_lines 统计）
    for f in files:
        try:
            with open(f, encoding='utf-8') as fh:
                lines = fh.readlines()
        except Exception:
            continue
        n_merged += merge_lines(lines)[1]
    kinds = {}
    for it in out:
        kinds[it['kind']] = kinds.get(it['kind'], 0) + 1
    high = [it for it in out if it['kind'] not in ('rounding', 'unit_convert')]
    pct_ctx_n = sum(1 for it in out if it.get('pct_ctx'))
    print(json.dumps({'files_checked': n_checked, 'blocks': n_blocks,
                      'lines_merged': n_merged, 'total_found': len(out),
                      'high_value': len(high), 'pct_ctx': pct_ctx_n,
                      'by_kind': kinds},
                     ensure_ascii=False, indent=1))
    with open('audit_math/findings_v4.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    # 打印高价值前 25 条（省 token：一行式）
    order = {'pct_candidate': 0, 'unit_candidate': 1, 'value_mismatch': 2, 'rounding': 3}
    out_sorted = sorted(high, key=lambda x: order.get(x['kind'], 9))
    print('\n--- 高价值候选（前 25 条）---')
    for it in out_sorted[:25]:
        pct = ' [%]' if it.get('pct_ctx') else ''
        print(f"[{it['kind']}{pct}] {it['file']}:{it['line']}"
              + ("  [merged]" if it.get('merged') else ""))
        print(f"    {it['lhs'][:90]} = {it['rhs'][:50]}  → 算得 {it.get('computed'):.6g}  rel={it.get('rel_diff'):.2e}")
        if it.get('note'): print(f"    NOTE: {it['note']}")

if __name__ == '__main__':
    main()
