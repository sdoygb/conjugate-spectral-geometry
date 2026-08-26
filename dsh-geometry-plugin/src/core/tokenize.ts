/**
 * tokenize.ts — 混合分词器（几何论语料的 BM25 专用）
 *
 * 策略：
 *   1. 拉丁/希腊/数字串原样保留为 token（θ_M, η_K, N_dec, 10.8, 0.19, sin, pr_geo…），
 *      希腊字母同时输出拉丁别名（θ_M → theta_m），实现希腊↔拉丁术语互通（B2）。
 *   2. 中文串：术语词典最长匹配优先（"编码轨道" > "码轨道" > bigram）
 *   3. 剩余中文走 bigram 兜底，过滤显式虚词组合
 *   4. 查询端（queryTokenize）：在标准 token 之外，对中文单字做词典前缀扩展，
 *      使单字查询（"谱""格"）能命中含术语（"谱刚性""格密码"）的文档（B1）。
 *
 * 零运行时依赖。
 */

/** 显式虚词 bigram（两个字都在虚词表会误杀"几何""知道"，故用显式组合） */
const STOP_BIGRAM = new Set([
  '的了', '是在', '与和', '就不', '都一', '一个', '我们', '你们', '他们', '自己',
  '已经', '正在', '还是', '就是', '因为', '所以', '但是', '然而', '如果', '那么',
  '虽然', '并且', '而且', '或者', '以及', '关于', '对于', '通过', '由于', '根据',
  '按照', '随着', '作为', '成为', '可以', '可能', '应该', '必须', '需要', '没有',
  '不是', '而是', '这个', '那个', '什么', '怎么', '怎样', '为什么', '如何', '哪里',
  '何时', '多少', '几些', '许多', '大量', '少部', '分之', '之间', '之后', '之前',
  '其中', '以及', '并且', '这些', '那些', '所谓', '因此', '此外', '同时', '例如',
  '比如', '综上', '总之', '本文', '本节', '上述', '如下', '以下', '以下', '给出',
  '进行', '存在', '称为', '定义', '其中', '这里', '此时', '对于', '一个', '这种',
  '相关', '不同', '主要', '重要', '基本', '一般', '具体', '相应', '进一步', '可以',
])

/** 希腊字母 → 拉丁别名（查询/文档双向归一化，B2） */
const GREEK_ALIAS: Record<string, string> = {
  α: 'alpha', β: 'beta', γ: 'gamma', δ: 'delta', ε: 'epsilon', ζ: 'zeta',
  η: 'eta', θ: 'theta', ι: 'iota', κ: 'kappa', λ: 'lambda', μ: 'mu',
  ν: 'nu', ξ: 'xi', ο: 'omicron', π: 'pi', ρ: 'rho', σ: 'sigma',
  τ: 'tau', υ: 'upsilon', φ: 'phi', χ: 'chi', ψ: 'psi', ω: 'omega',
  Α: 'alpha', Β: 'beta', Γ: 'gamma', Δ: 'delta', Ε: 'epsilon', Ζ: 'zeta',
  Η: 'eta', Θ: 'theta', Ι: 'iota', Κ: 'kappa', Λ: 'lambda', Μ: 'mu',
  Ν: 'nu', Ξ: 'xi', Ο: 'omicron', Π: 'pi', Ρ: 'rho', Σ: 'sigma',
  Τ: 'tau', Υ: 'upsilon', Φ: 'phi', Χ: 'chi', Ψ: 'psi', Ω: 'omega',
}

/** 反向：拉丁 → 希腊（查询"theta"命中文档"θ"时，靠别名追加在文档端已覆盖，无需反向表） */

/** 虚词单字（unigram 索引时过滤，B1 兜底） */
const UNIGRAM_STOP = new Set(
  '的了是在与和就不都一我你他她它我们你们他们自己这那为因而后所被把让从对向到于等又再很最更也还或及并但若若使且虽即如若'.split(''),
)

/** 拉丁字母 + 希腊字母 + 数字 + 下划线（保留原样 token） */
const LATIN_GREEK = /[a-z_\u0370-\u03ff]+/g
const NUMBER = /\d+(?:\.\d+)+|\d+/g
/** 连续中文串（{1,}：单字也走 tokenizeCjk，输出 unigram+bigram） */
const CJK_RUN = /[\u4e00-\u9fff]+/g

/** 把 token 中的希腊字母替换为拉丁别名（无映射则返回原串） */
export function greekToLatin(token: string): string {
  let out = ''
  let changed = false
  for (const ch of token) {
    const alias = GREEK_ALIAS[ch]
    if (alias) {
      out += alias
      changed = true
    } else {
      out += ch
    }
  }
  return changed ? out : token
}

export class Tokenizer {
  /** 术语词典，按长度降序（最长匹配优先） */
  private readonly dict: string[]
  /** 按首字符分组的词典候选：把每个位置 O(600) 的全表扫描降为 O(该字符候选数) */
  private readonly byFirst: Map<string, string[]>

  constructor(terms: string[]) {
    this.dict = [...new Set(terms)].sort((a, b) => b.length - a.length)
    this.byFirst = new Map()
    for (const w of this.dict) {
      const arr = this.byFirst.get(w[0])
      if (arr) arr.push(w)
      else this.byFirst.set(w[0], [w])
    }
  }

  /** 文档/查询共用的基础分词（含希腊别名追加） */
  private baseTokenize(text: string): string[] {
    const out: string[] = []
    const lower = text.toLowerCase()
    // 1. 拉丁/希腊 token（保留原样，单字母也保留——idf 自有区分力；追加希腊别名）
    for (const m of lower.matchAll(LATIN_GREEK)) {
      const t = m[0]
      if (t.length > 0) {
        out.push(t)
        const alias = greekToLatin(t)
        if (alias !== t) out.push(alias)
      }
    }
    // 2. 数字（含小数，覆盖文章编号 10.8、数值 0.19/137.036）
    for (const m of lower.matchAll(NUMBER)) out.push(m[0])
    // 3. 中文串：unigram（B1 兜底）+ 词典最长匹配 + bigram 兜底
    for (const seg of text.matchAll(CJK_RUN)) {
      this.tokenizeCjk(seg[0], out)
    }
    return out
  }

  /** 文档端分词（含希腊别名，不含查询专用扩展） */
  tokenize(text: string): string[] {
    return this.baseTokenize(text)
  }

  /**
   * 查询端分词：基础 token + 中文单字词典前缀扩展（B1）。
   * 例：查询"谱" → "谱" + byFirst["谱"] 下所有词典词（谱刚性、谱刚性比…），
   * 使单字查询能命中含完整术语的文档；文档端无需索引单字，保持精确。
   * 注意：单字查询不匹配 CJK_RUN（{2,}），故此处用 {1,} 单独扫描。
   */
  queryTokenize(text: string): string[] {
    const out = this.baseTokenize(text)
    // 中文单字前缀扩展：对每个汉字，若它是某词典词的首字符，追加该词
    // （限制最多 8 个候选，避免单字查询爆炸）
    for (const seg of text.matchAll(CJK_RUN)) {
      const s = seg[0]
      for (let i = 0; i < s.length; i++) {
        const cands = this.byFirst.get(s[i])
        if (cands) {
          const picks = cands.slice(0, 8)
          for (const w of picks) out.push(w)
        }
      }
    }
    return out
  }

  private tokenizeCjk(s: string, out: string[]): void {
    const n = s.length
    let i = 0
    while (i < n) {
      const ch = s[i]
      // unigram（B1 兜底：单字查询直接命中；过滤虚词单字）
      if (!UNIGRAM_STOP.has(ch)) out.push(ch)
      const candidates = this.byFirst.get(ch)
      let matched = false
      if (candidates) {
        // 候选组内保持全局长度降序 → 语义与原线性扫描一致（最长匹配优先）
        for (const w of candidates) {
          if (s.startsWith(w, i)) {
            out.push(w)
            i += w.length
            matched = true
            break
          }
        }
      }
      if (matched) continue
      if (i + 1 < n) {
        const bg = s.slice(i, i + 2)
        if (!STOP_BIGRAM.has(bg)) out.push(bg)
        i += 1
      } else {
        i += 1
      }
    }
  }
}
