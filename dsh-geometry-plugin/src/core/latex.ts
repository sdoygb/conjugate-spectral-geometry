/**
 * latex.ts — 轻量 LaTeX → Unicode 显示转换（C2）。
 *
 * 几何论文章用 LaTeX 数学（$\theta_M$、$\Lambda_H$、\frac{a}{b}…），纯文本
 * 输出难读。本模块做**保守**转换：只替换明确映射的命令/分隔符，未知命令
 * 保留原样（不破坏内容、不引入错误）。
 *
 * 覆盖：
 *   - 希腊字母命令（\theta → θ，含大小写）
 *   - 常用黑体/花体/空心体（\mathbb{R} → ℝ、\mathcal{L} → ℒ、\mathbf{v} → 𝐯 降级为 v）
 *   - \frac{a}{b}（单层）、\sqrt{x}、\cdot、\times、\pm、\leq、\geq、\approx…
 *   - 上标/下标（^{...}、_{...} 做最简扁平化：x^{2} → x^2）
 *   - 去掉 $ / \( \) / \[ \] 分隔符
 *
 * 零运行时依赖。
 */

const GREEK_CMD: Record<string, string> = {
  alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε',
  zeta: 'ζ', eta: 'η', theta: 'θ', vartheta: 'ϑ', iota: 'ι', kappa: 'κ',
  lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', omicron: 'ο', pi: 'π', varpi: 'ϖ',
  rho: 'ρ', varrho: 'ϱ', sigma: 'σ', varsigma: 'ς', tau: 'τ', upsilon: 'υ',
  phi: 'φ', varphi: 'ϕ', chi: 'χ', psi: 'ψ', omega: 'ω',
  Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π',
  Sigma: 'Σ', Upsilon: 'Υ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
}

const MATH_SYMBOL: Record<string, string> = {
  cdot: '·', times: '×', pm: '±', mp: '∓', leq: '≤', geq: '≥', neq: '≠',
  le: '≤', ge: '≥', ne: '≠', approx: '≈', propto: '∝', infty: '∞', partial: '∂', nabla: '∇',
  sum: '∑', prod: '∏', int: '∫', sqrt: '√', ell: 'ℓ', in: '∈',
  notin: '∉', subset: '⊂', supset: '⊃', subseteq: '⊆', supseteq: '⊇',
  cap: '∩', cup: '∪', oplus: '⊕', otimes: '⊗', equiv: '≡', sim: '∼',
  simeq: '≃', cong: '≅', qquad: '  ', quad: ' ', text: '', overline: '¯',
  rightarrow: '→', leftarrow: '←', mapsto: '↦', to: '→', implies: '⇒',
  Leftrightarrow: '⇔', ldots: '…', cdots: '⋯', vdots: '⋮', prime: '′',
  hbar: 'ħ', Re: 'ℜ', Im: 'ℑ', aleph: 'ℵ',
  // 函数/运算符命令：去掉反斜杠（\max → max、\sin → sin）
  max: 'max', min: 'min', sup: 'sup', inf: 'inf', lim: 'lim', det: 'det',
  sin: 'sin', cos: 'cos', tan: 'tan', cot: 'cot', sec: 'sec', csc: 'csc',
  log: 'log', ln: 'ln', exp: 'exp', mod: 'mod', arg: 'arg', dim: 'dim',
  ker: 'ker', Tr: 'Tr', Pr: 'Pr', deg: 'deg',
  // 声明式字体命令（无花括号形式）：\rm geo → geo
  rm: '', bf: '', it: '', cal: '',
}

/** 数学分隔符（只删 $ 与 LaTeX 分隔符对 \( \) \[ \]；普通括号保留） */
const DELIMS = /\$|\\\(|\\\)|\\\[|\\\]/g

/** 黑体字降级映射（无 Unicode 直接对应时保留字母） */
const MATHBB: Record<string, string> = {
  R: 'ℝ', Z: 'ℤ', N: 'ℕ', Q: 'ℚ', C: 'ℂ', P: 'ℙ', H: 'ℍ', F: '𝔽',
}

/**
 * 保守转换一段文本中的 LaTeX 数学为 Unicode。
 * 未知命令保留原样（含反斜杠），保证不破坏内容。
 */
export function latexToUnicode(text: string): string {
  let out = text
  // 0. 上标/下标扁平化**提前**：x^{2} → x^2、x_{i} → x_i，去掉嵌套花括号，
  //    使 \frac{n \Lambda_{\max}^{(n-1)/n} - 1}{...} 这类实参含上标的分数可被匹配
  out = out.replace(/\^\{([^{}]*)\}/g, '^$1').replace(/_\{([^{}]*)\}/g, '_$1')
  // 1. \frac{a}{b}（单层，非嵌套）
  out = out.replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, (_, a: string, b: string) => `(${a})/(${b})`)
  // 2. \mathbb{X} → ℝ（降级为普通字母若不在表）
  out = out.replace(/\\mathbb\{([A-Za-z])\}/g, (_, c: string) => MATHBB[c] ?? c)
  // 3. \mathcal{X} / \mathbf{x} / \mathrm{x} / \text{...} → 内容本身（花体/正体降级）
  out = out.replace(
    /\\(mathcal|mathbf|mathrm|mathit|mathtt|mathsf|boldsymbol|bm|text|mbox|textrm)\{([^{}]*)\}/g,
    (_, __, body: string) => body,
  )
  // 4. \sqrt{x} → √(x)（非嵌套）
  out = out.replace(/\\sqrt\{([^{}]*)\}/g, (_, x: string) => `√(${x})`)
  // 5. 希腊字母命令与数学符号
  out = out.replace(/\\([A-Za-z]+)/g, (m, cmd: string) => GREEK_CMD[cmd] ?? MATH_SYMBOL[cmd] ?? m)
  // 6. 去掉分隔符 $ \( \) \[ \]
  out = out.replace(DELIMS, '')
  return out
}

/** 是否含可转换的 LaTeX 标记（快速判断，避免无谓处理） */
export function hasLatex(text: string): boolean {
  return /\\[A-Za-z]+|\$|\\\(|\\\[/.test(text)
}
