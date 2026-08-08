#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格内 LaTeX → Unicode 转换器（知乎版）
=======================================
规则：只转换 Markdown 表格行（以 | 开头）单元格内的 LaTeX 公式算符为 Unicode；
     表格外的 LaTeX 一律不动。

用法: python3 tools/zh_convert.py <源文件.md> [<源文件.md> ...]
输出: app/articles/ZH/<同名文件>

v4 改进（相对 v3）：
 1. 修复 \frac{a}{b} / \binom{a}{b} 第二参数错误（den/b 曾包含起始 {）
 2. \frac 简写形式（\frac49 → 4/9）
 3. 装饰命令无花括号形式（\bar\theta → θ̄）
 4. 未知命令智能分割（\cdotVol → ⋅Vol、\partialS → ∂S）
 5. smallmatrix 环境 → [m; k]
 6. \mathcal/\mathbb 多字母逐字符
 7. \not 否定组合（\not\supset → ⊅）
 8. \tag{...} → (编号)
"""
import re, sys, os

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "app", "articles", "ZH")

# ---------- Unicode 映射表 ----------

SUP = {'0':'\u2070','1':'\u00b9','2':'\u00b2','3':'\u00b3','4':'\u2074','5':'\u2075',
       '6':'\u2076','7':'\u2077','8':'\u2078','9':'\u2079','+':'\u207a','-':'\u207b',
       '=':'\u207c','(':'\u207d',')':'\u207e','n':'\u207f','i':'\u2071',
       'a':'\u1d43','b':'\u1d47','c':'\u1d9c','d':'\u1d48','e':'\u1d49','f':'\u1da0',
       'g':'\u1d4d','h':'\u02b0','j':'\u02b2','k':'\u1d4f','l':'\u02e1','m':'\u1d50',
       'o':'\u1d52','p':'\u1d56','r':'\u02b3','s':'\u02e2','t':'\u1d57','u':'\u1d58',
       'v':'\u1d5b','w':'\u02b7','x':'\u02e3','y':'\u02b8','z':'\u1dbb',
       'T':'\u1d40','A':'\u1d2c','B':'\u1d2e','D':'\u1d30','E':'\u1d31','G':'\u1d33',
       'H':'\u1d34','I':'\u1d35','J':'\u1d36','K':'\u1d37','L':'\u1d38','M':'\u1d39',
       'N':'\u1d3a','O':'\u1d3c','P':'\u1d3e','R':'\u1d3f','U':'\u1d41','V':'\u2c7d',
       'W':'\u1d42',
       '\u03b1':'\u1d45','\u03b2':'\u1d5d','\u03b3':'\u1d5e','\u03b4':'\u1d5f',
       '\u03b8':'\u1dbf','\u03c6':'\u1d60','\u03c7':'\u1d61','\u03c1':'\u1d68'}

SUB = {'0':'\u2080','1':'\u2081','2':'\u2082','3':'\u2083','4':'\u2084','5':'\u2085',
       '6':'\u2086','7':'\u2087','8':'\u2088','9':'\u2089','+':'\u208a','-':'\u208b',
       '=':'\u208c','(':'\u208d',')':'\u208e',
       'a':'\u2090','e':'\u2091','h':'\u2095','i':'\u1d62','j':'\u2c7c','k':'\u2096',
       'l':'\u2097','m':'\u2098','n':'\u2099','o':'\u2092','p':'\u209a','r':'\u1d63',
       's':'\u209b','t':'\u209c','u':'\u1d64','v':'\u1d65','x':'\u2093',
       '\u03b2':'\u1d66','\u03b3':'\u1d67','\u03c1':'\u1d68','\u03c6':'\u1d69','\u03c7':'\u1d6a'}

MATHBB = {'A':'\U0001d538','B':'\U0001d539','C':'\u2102','D':'\U0001d53b','E':'\U0001d53c',
          'F':'\U0001d53d','G':'\U0001d53e','H':'\u210d','I':'\U0001d540','J':'\U0001d541',
          'K':'\U0001d542','L':'\U0001d543','M':'\U0001d544','N':'\u2115','O':'\U0001d546',
          'P':'\u2119','Q':'\u211a','R':'\u211d','S':'\U0001d54a','T':'\U0001d54b',
          'U':'\U0001d54c','V':'\U0001d54d','W':'\U0001d54e','X':'\U0001d54f',
          'Y':'\U0001d550','Z':'\u2124'}

MATHCAL_U = {
    'A':'\U0001d49c','B':'\u212c','C':'\U0001d49e','D':'\U0001d49f','E':'\u2130',
    'F':'\u2131','G':'\U0001d4a2','H':'\u210b','I':'\u2110','J':'\U0001d4a5',
    'K':'\U0001d4a6','L':'\u2112','M':'\u2133','N':'\U0001d4a9','O':'\U0001d4aa',
    'P':'\U0001d4ab','Q':'\U0001d4ac','R':'\u211b','S':'\U0001d4ae','T':'\U0001d4af',
    'U':'\U0001d4b0','V':'\U0001d4b1','W':'\U0001d4b2','X':'\U0001d4b3',
    'Y':'\U0001d4b4','Z':'\U0001d4b5',
    'a':'\U0001d4b6','b':'\U0001d4b7','c':'\U0001d4b8','d':'\U0001d4b9','e':'\u212f',
    'f':'\U0001d4bb','g':'\u210a','h':'\U0001d4bd','i':'\U0001d4be','j':'\U0001d4bf',
    'k':'\U0001d4c0','l':'\U0001d4c1','m':'\U0001d4c2','n':'\U0001d4c3','o':'\u2134',
    'p':'\U0001d4c5','q':'\U0001d4c6','r':'\U0001d4c7','s':'\U0001d4c8','t':'\U0001d4c9',
    'u':'\U0001d4ca','v':'\U0001d4cb','w':'\U0001d4cc','x':'\U0001d4cd',
    'y':'\U0001d4ce','z':'\U0001d4cf',
}

def mathcal(ch):
    return MATHCAL_U.get(ch, ch)

MATHFRAK_U = {'A':'\U0001d504','B':'\U0001d505','C':'\u212d','D':'\U0001d507','E':'\U0001d508',
              'F':'\U0001d509','G':'\U0001d50a','H':'\u210c','I':'\u2111','J':'\U0001d50d',
              'K':'\U0001d50e','L':'\U0001d50f','M':'\U0001d510','N':'\U0001d511','O':'\U0001d512',
              'P':'\U0001d513','Q':'\U0001d514','R':'\u211c','S':'\U0001d516','T':'\U0001d517',
              'U':'\U0001d518','V':'\U0001d519','W':'\U0001d51a','X':'\U0001d51b','Y':'\U0001d51c',
              'Z':'\u2128'}

def mathfrak(ch):
    if 'A' <= ch <= 'Z':
        return MATHFRAK_U.get(ch, ch)
    if 'a' <= ch <= 'z':
        return chr(0x1d51e + ord(ch) - ord('a'))
    return ch

SYM = {
 # 希腊小写
 '\\alpha':'\u03b1','\\beta':'\u03b2','\\gamma':'\u03b3','\\delta':'\u03b4',
 '\\epsilon':'\u03b5','\\varepsilon':'\u03b5','\\zeta':'\u03b6','\\eta':'\u03b7',
 '\\theta':'\u03b8','\\vartheta':'\u03d1','\\iota':'\u03b9','\\kappa':'\u03ba',
 '\\varkappa':'\u03f0','\\lambda':'\u03bb','\\mu':'\u03bc','\\nu':'\u03bd',
 '\\xi':'\u03be','\\omicron':'\u03bf','\\pi':'\u03c0','\\varpi':'\u03d6',
 '\\rho':'\u03c1','\\varrho':'\u03f1','\\sigma':'\u03c3','\\varsigma':'\u03c2',
 '\\tau':'\u03c4','\\upsilon':'\u03c5','\\phi':'\u03c6','\\varphi':'\u03c6',
 '\\chi':'\u03c7','\\psi':'\u03c8','\\omega':'\u03c9',
 # 希腊大写
 '\\Gamma':'\u0393','\\Delta':'\u0394','\\Theta':'\u0398','\\Lambda':'\u039b',
 '\\Xi':'\u039e','\\Pi':'\u03a0','\\Sigma':'\u03a3','\\Upsilon':'\u03a5',
 '\\Phi':'\u03a6','\\Psi':'\u03a8','\\Omega':'\u03a9',
 # 关系符
 '\\cong':'\u2245','\\simeq':'\u2243','\\approx':'\u2248','\\equiv':'\u2261',
 '\\neq':'\u2260','\\ne':'\u2260','\\leq':'\u2264','\\le':'\u2264','\\geq':'\u2265',
 '\\ge':'\u2265','\\ll':'\u226a','\\gg':'\u226b','\\sim':'\u223c','\\propto':'\u221d',
 '\\subset':'\u2282','\\supset':'\u2283','\\subseteq':'\u2286','\\supseteq':'\u2287',
 '\\subsetneq':'\u228a','\\supsetneq':'\u228b','\\nsubseteq':'\u2288','\\nsupseteq':'\u2289',
 '\\in':'\u2208','\\notin':'\u2209','\\ni':'\u220b','\\nmid':'\u2224','\\nparallel':'\u2226',
 '\\ncong':'\u2247','\\nequiv':'\u2262','\\nleq':'\u2270','\\ngeq':'\u2271','\\nsim':'\u2241',
 '\\nless':'\u226e','\\ngtr':'\u226f',
 # 二元算符
 '\\times':'\u00d7','\\cdot':'\u00b7','\\pm':'\u00b1','\\mp':'\u2213','\\div':'\u00f7',
 '\\otimes':'\u2297','\\oplus':'\u2295','\\ominus':'\u2296','\\odot':'\u2299','\\oslash':'\u2298',
 '\\wedge':'\u2227','\\vee':'\u2228','\\cap':'\u2229','\\cup':'\u222a','\\setminus':'\u2216',
 '\\ast':'\u2217','\\star':'\u22c6','\\circ':'\u2218','\\bullet':'\u2022','\\dagger':'\u2020',
 '\\ddagger':'\u2021','\\dag':'\u2020','\\ddag':'\u2021','\\amalg':'\u2a3f','\\diamond':'\u22c4',
 '\\triangleleft':'\u25c1','\\triangleright':'\u25b7','\\lhd':'\u22b2','\\rhd':'\u22b3',
 '\\unlhd':'\u22b4','\\unrhd':'\u22b5','\\bigoplus':'\u2a01','\\bigotimes':'\u2a02',
 '\\bigwedge':'\u22c0','\\bigvee':'\u22c1','\\bigcup':'\u22c3','\\bigcap':'\u22c2',
 '\\boxplus':'\u229e','\\boxtimes':'\u22a0',
 # 箭头
 '\\to':'\u2192','\\rightarrow':'\u2192','\\leftarrow':'\u2190','\\leftrightarrow':'\u2194',
 '\\Rightarrow':'\u21d2','\\Leftarrow':'\u21d0','\\Leftrightarrow':'\u21d4','\\iff':'\u21d4',
 '\\mapsto':'\u21a6','\\longrightarrow':'\u27f6','\\longleftarrow':'\u27f5',
 '\\Longrightarrow':'\u27f9','\\Longleftarrow':'\u27f8','\\implies':'\u27f9','\\impliedby':'\u27f8',
 '\\uparrow':'\u2191','\\downarrow':'\u2193','\\updownarrow':'\u2195','\\nearrow':'\u2197',
 '\\searrow':'\u2198','\\nwarrow':'\u2196','\\swarrow':'\u2199','\\hookrightarrow':'\u21aa',
 '\\hookleftarrow':'\u21a9','\\rightsquigarrow':'\u21dd','\\leadsto':'\u21dd',
 '\\twoheadrightarrow':'\u21a0','\\twoheadleftarrow':'\u219e',
 # 括号与定界符
 '\\langle':'\u27e8','\\rangle':'\u27e9','\\lceil':'\u2308','\\rceil':'\u2309',
 '\\lfloor':'\u230a','\\rfloor':'\u230b','\\lvert':'\u007c','\\rvert':'\u007c',
 '\\lVert':'\u2016','\\rVert':'\u2016','\\Vert':'\u2016','\\vert':'\u007c',
 '\\{':'\u007b','\\}':'\u007d','\\backslash':'\u005c',
 # 杂项符号
 '\\infty':'\u221e','\\emptyset':'\u2205','\\varnothing':'\u2205','\\forall':'\u2200',
 '\\exists':'\u2203','\\nexists':'\u2204','\\neg':'\u00ac','\\top':'\u22a4','\\bot':'\u22a5',
 '\\perp':'\u22a5','\\parallel':'\u2225','\\mid':'\u007c','\\partial':'\u2202',
 '\\nabla':'\u2207','\\sum':'\u2211','\\prod':'\u220f','\\int':'\u222b','\\oint':'\u222e',
 '\\iint':'\u222c','\\iiint':'\u222d','\\sqrt':'\u221a','\\hbar':'\u210f','\\ell':'\u2113',
 '\\Re':'Re','\\Im':'Im','\\aleph':'\u2135','\\wp':'\u2118','\\angle':'\u2220',
 '\\triangle':'\u25b3','\\square':'\u25a1','\\blacksquare':'\u25a0','\\Box':'\u25a1',
 '\\Diamond':'\u25c7','\\prime':'\u2032','\\degree':'\u00b0','\\dots':'\u2026',
 '\\ldots':'\u2026','\\cdots':'\u22ef','\\vdots':'\u22ee','\\ddots':'\u22f1',
 '\\therefore':'\u2234','\\because':'\u2235','\\checkmark':'\u2713','\\triangleq':'\u225c',
 '\\doteq':'\u2250','\\fallingdotseq':'\u2252','\\risingdotseq':'\u2253','\\approxeq':'\u224a',
 '\\prec':'\u227a','\\succ':'\u227b','\\preceq':'\u227c','\\succeq':'\u227d',
 '\\lll':'\u22d8','\\ggg':'\u22d9','\\vDash':'\u22a8','\\models':'\u22a8','\\vdash':'\u22a2',
 '\\dashv':'\u22a3','\\upharpoonright':'\u21be','\\downharpoonright':'\u21c2',
 # 函数名（去反斜杠）
 '\\log':'log','\\ln':'ln','\\dim':'dim','\\exp':'exp','\\sin':'sin','\\cos':'cos',
 '\\tan':'tan','\\cot':'cot','\\sec':'sec','\\csc':'csc','\\arcsin':'arcsin',
 '\\arccos':'arccos','\\arctan':'arctan','\\sinh':'sinh','\\cosh':'cosh','\\tanh':'tanh',
 '\\coth':'coth','\\max':'max','\\min':'min','\\ker':'ker','\\det':'det','\\tr':'tr',
 '\\arg':'arg','\\deg':'deg','\\hom':'hom','\\mod':'mod','\\bmod':'mod','\\Pr':'Pr',
 '\\sup':'sup','\\inf':'inf','\\lim':'lim','\\limsup':'lim sup','\\liminf':'lim inf',
 '\\gcd':'gcd','\\argmax':'argmax','\\argmin':'argmin','\\minwt':'min wt',
 '\\displaystyle':'','\\textstyle':'','\\scriptstyle':'','\\scriptscriptstyle':'',
 '\\nolimits':'','\\limits':'',
 # 文本转义
 '\\%':'\u0025','\\&':'\u0026','\\_':'\u005f','\\#':'\u0023','\\$':'\u0024',
 '\\,':'\u0020','\\:':'\u0020','\\;':'\u0020','\\quad':'\u0020','\\qquad':'\u0020',
 '\\!':'','\\ ':'\u0020',
 '\\rm':'','\\it':'','\\bf':'','\\mathit':'','\\mathbf':'','\\boldsymbol':'','\\bm':'',
 '\\left.':'','\\right.':'','\\bigl':'','\\bigr':'','\\Bigl':'','\\Bigr':'',
 '\\biggl':'','\\biggr':'','\\Biggl':'','\\Biggr':'','\\big':'','\\Big':'',
 '\\bigg':'','\\Bigg':'','\\left':'','\\right':'',
}

# 去前缀命令（\left( → ( 等）
STRIP_PREFIX = re.compile(r'\\(?:left|right|big|Big|bigg|Bigg|bigl|bigr|Bigl|Bigr|biggl|biggr|Biggl|Biggr)(?=[\(\[\{\|\]\}\.\<\\])')

# 装饰命令 → 组合字符
ACCENT = {
    'overline': '\u0305',
    'vec':      '\u20d7',
    'tilde':    '\u0303',
    'hat':      '\u0302',
    'ddot':     '\u0308',
    'dot':      '\u0307',
    'bar':      '\u0304',
}

# \not 否定组合
NOT_MAP = {
    '\\supset': '\u2285', '\\subset': '\u2284',
    '\\subseteq': '\u2288', '\\supseteq': '\u2289',
    '=': '\u2260', '<': '\u226e', '>': '\u226f',
    '\\in': '\u2209', '\\ni': '\u220c',
    '\\leq': '\u2270', '\\geq': '\u2271',
    '\\approx': '\u2249', '\\sim': '\u2241', '\\simeq': '\u2244',
    '\\equiv': '\u2262', '\\parallel': '\u2226', '\\mid': '\u2224',
    '\\prec': '\u2280', '\\succ': '\u2281',
}

def find_braces(s, i):
    """s[i] == '{'，返回匹配的右括号下标（不含）"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return j
    return -1

def convert_sup_sub(t):
    """处理 ^{...} _{...} ^x _x；全部可映射才转换；单字符失败降级；^{∘} → °"""
    def try_convert(content, table):
        out = []
        for ch in content:
            if ch in table:
                out.append(table[ch])
            else:
                return None
        return ''.join(out)

    def repl_sup(m):
        content = m.group(1)
        if content == '\u2218':          # ^{∘} → °（角度）
            return '\u00b0'
        r = try_convert(content, SUP)
        if r is not None:
            return r
        if len(content) == 1:
            return content                # 单字符降级：去 ^ 直接输出
        return m.group(0)

    def repl_sub(m):
        content = m.group(1)
        r = try_convert(content, SUB)
        if r is not None:
            return r
        if len(content) == 1:
            return content                # 单字符降级：去 _ 直接输出
        return m.group(0)

    t = re.sub(r'\^\{([^{}]*)\}', repl_sup, t)
    t = re.sub(r'_\{([^{}]*)\}', repl_sub, t)
    t = re.sub(r'\^([^\s^{}\(\)]|\\[a-zA-Z]+)', lambda m: repl_sup(re.match(r'\^\{([^{}]*)\}', '^{' + m.group(1) + '}')), t)
    t = re.sub(r'_([^\s_{}\(\)]|\\[a-zA-Z]+)', lambda m: repl_sub(re.match(r'_\{([^{}]*)\}', '_{' + m.group(1) + '}')), t)
    return t

def tex_to_unicode(t, math=True):
    """LaTeX 片段 → Unicode。math=True（公式上下文）：\| → ‖；False（裸文本）：保留 markdown 转义管道。"""
    if not t:
        return t
    if math:
        t = t.replace(r'\|', '\u2016')
    # 1. 文本命令：\text{...} \mathrm{...} 等
    def repl_text(m):
        return tex_to_unicode(m.group(1))
    t = re.sub(r'\\(?:text|mathrm|operatorname|mathbf|mathit|textrm)\{([^{}]*)\}', repl_text, t)
    # 2. 装饰命令花括号形式 \bar{...} \hat{...} 等（长的在前，find_braces 配对嵌套）
    for _ in range(10):
        m = re.search(r'\\(?:overline|vec|tilde|hat|ddot|dot|bar)\{', t)
        if not m:
            break
        cmd = m.group(0)[1:-1]
        j = find_braces(t, m.end() - 1)
        if j == -1:
            break
        inner = tex_to_unicode(t[m.end():j])
        t = t[:m.start()] + inner + ACCENT[cmd] + t[j + 1:]
        continue
    # 2b. 装饰命令无花括号形式 \bar\theta、\barθ
    def repl_accent2(m):
        return tex_to_unicode(m.group(2)) + ACCENT[m.group(1)]
    t = re.sub(r'\\(overline|vec|tilde|hat|ddot|dot|bar)\s*((?:\\[a-zA-Z]+)|[^\s{}\\])', repl_accent2, t)
    # 3. 去定界符前缀
    t = STRIP_PREFIX.sub('', t)
    # 4. 结构命令循环（frac/binom/sqrt/pmod/smallmatrix，find_braces 配对）
    for _ in range(10):
        m = re.search(r'\\(?:frac|dfrac|tfrac)\{', t)
        if m:
            j = find_braces(t, m.end() - 1)
            if j == -1:
                break
            num = t[m.end():j]
            k = find_braces(t, j + 1)
            if k == -1:
                break
            den = t[j + 2:k]             # j+1 是 '{'，内容从 j+2 开始
            t = t[:m.start()] + tex_to_unicode(num) + '/' + tex_to_unicode(den) + t[k + 1:]
            continue
        m = re.search(r'\\(?:binom|tbinom|dbinom)\{', t)
        if m:
            j = find_braces(t, m.end() - 1)
            if j == -1:
                break
            a = t[m.end():j]
            k = find_braces(t, j + 1)
            if k == -1:
                break
            b = t[j + 2:k]               # j+1 是 '{'，内容从 j+2 开始
            t = t[:m.start()] + 'C(' + tex_to_unicode(a) + ', ' + tex_to_unicode(b) + ')' + t[k + 1:]
            continue
        m = re.search(r'\\sqrt(?:\[[^{}]*\])?\{', t)
        if m:
            j = find_braces(t, m.end() - 1)
            if j == -1:
                break
            inner = tex_to_unicode(t[m.end():j])
            if len(inner) > 1 and re.search(r'[+\-*/=<>≤≥±×]', inner):
                inner = '(' + inner + ')'
            t = t[:m.start()] + '\u221a' + inner + t[j + 1:]
            continue
        m = re.search(r'\\pmod\{', t)
        if m:
            j = find_braces(t, m.end() - 1)
            if j == -1:
                break
            inner = tex_to_unicode(t[m.end():j])
            t = t[:m.start()] + '(mod ' + inner + ')' + t[j + 1:]
            continue
        m = re.search(r'\\begin\{smallmatrix\}(.*?)\\end\{smallmatrix\}', t)
        if m:
            content = m.group(1).replace('\\\\', '; ').replace('&', ', ')
            content = re.sub(r'\s+', ' ', content).strip()
            t = t[:m.start()] + tex_to_unicode(content) + t[m.end():]
            continue
        break
    # 4b. \frac 简写形式：\frac49 → 4/9、\frac ab → a/b
    def repl_frac_short(m):
        return tex_to_unicode(m.group(1)) + '/' + tex_to_unicode(m.group(2))
    t = re.sub(r'\\frac(?!\{)\s*((?:\\[a-zA-Z]+)|[^\s{}\\ ])\s*((?:\\[a-zA-Z]+)|[^\s{}\\ ])', repl_frac_short, t)
    # 4c. \tag{编号} → (编号)
    t = re.sub(r'\\tag\{([^{}]*)\}', lambda m: '(' + m.group(1) + ')', t)
    # 5. \mathbb / \mathcal / \mathfrak（多字母逐字符）
    t = re.sub(r'\\mathbb\{([A-Za-z]+)\}', lambda m: ''.join(MATHBB.get(c, c) for c in m.group(1)), t)
    t = re.sub(r'\\(?:mathcal|mathscr)\{([A-Za-z]+)\}', lambda m: ''.join(mathcal(c) for c in m.group(1)), t)
    t = re.sub(r'\\mathfrak\{([A-Za-z]+)\}', lambda m: ''.join(mathfrak(c) for c in m.group(1)), t)
    # 5b. \not 否定组合（须在符号映射前，\not\supset → ⊅）
    def repl_not(m):
        key = m.group(1)
        return NOT_MAP.get(key, m.group(0))
    t = re.sub(r'\\not(\\[a-zA-Z]+|[^\s{}\\])', repl_not, t)
    # 6. 符号命令映射（未知命令：智能分割，否则跳过继续）
    def split_unknown(cmd):
        for i in range(len(cmd) - 1, 1, -1):
            prefix = cmd[:i]
            if prefix in SYM:
                return SYM[prefix] + cmd[i:]
        return None
    pos = 0
    for _ in range(200):
        m = re.search(r'\\[a-zA-Z]+', t[pos:])
        if not m:
            break
        cmd = m.group(0)
        if cmd in SYM:
            t = t[:pos + m.start()] + SYM[cmd] + t[pos + m.end():]
        else:
            r = split_unknown(cmd)
            if r is not None:
                t = t[:pos + m.start()] + r + t[pos + m.end():]
            else:
                pos += m.end()
    # 7. 上下标
    t = convert_sup_sub(t)
    # 8. 清理残留
    t = t.replace('~', '\u0020')
    t = re.sub(r'\s+', '\u0020', t)
    return t.strip()

def process_dollar_pairs(line):
    """手工 $ 配对：$$ 相邻（空公式占位）删除；\$ 转义保护；奇数 $ 保留。"""
    PL = '\x01'
    line = line.replace('\\$', PL)
    idxs = [j for j, c in enumerate(line) if c == '$']
    if not idxs:
        return line.replace(PL, '$')
    out = []
    last = 0
    i = 0
    while i < len(idxs):
        a = idxs[i]
        if i + 1 < len(idxs):
            b = idxs[i + 1]
            if b == a + 1:
                # $$ 相邻：空公式占位 → 删除
                out.append(line[last:a])
                last = b + 1
                i += 2
                continue
            out.append(line[last:a])
            content = line[a + 1:b]
            out.append(tex_to_unicode(content))
            last = b + 1
            i += 2
            continue
        # 奇数个 $：剩余原样保留
        out.append(line[last:])
        last = len(line)
        i += 1
    out.append(line[last:])
    line = ''.join(out)
    return line.replace(PL, '$')

def convert_line(line):
    """转换一个表格行：$ 配对 + 公式转换 + 裸命令处理（保留行尾换行符）"""
    nl = "\n" if line.endswith("\n") else ""
    body = line[:-1] if nl else line
    body = process_dollar_pairs(body)
    body = tex_to_unicode(body, math=False)
    return body + nl

def is_table_row(line):
    s = line.strip()
    return s.startswith('|') and s.count('|') >= 2

def convert_file(src):
    with open(src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    out = []
    in_code = False
    n_tables = 0
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            out.append(line)
            continue
        if not in_code and is_table_row(line):
            out.append(convert_line(line))
            n_tables += 1
        else:
            out.append(line)
    os.makedirs(OUT_DIR, exist_ok=True)
    dst = os.path.join(OUT_DIR, os.path.basename(src))
    with open(dst, 'w', encoding='utf-8') as f:
        f.writelines(out)
    return dst, n_tables

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 tools/zh_convert.py <源文件.md> [...]')
        sys.exit(1)
    for src in sys.argv[1:]:
        dst, n = convert_file(src)
        print(f'✓ {os.path.basename(src)}: {n} 表格行已转换 → {dst}')
