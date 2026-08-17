/**
 * tokenize.ts — 混合分词器（几何论语料的 BM25 专用）
 *
 * 策略：
 *   1. 拉丁/希腊/数字串原样保留为 token（θ_M, η_K, N_dec, 10.8, 0.19, sin, pr_geo…）
 *   2. 中文串：术语词典最长匹配优先（"编码轨道" > "码轨道" > bigram）
 *   3. 剩余中文走 bigram 兜底，过滤显式虚词组合
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

/** 拉丁字母 + 希腊字母 + 数字 + 下划线（保留原样 token） */
const LATIN_GREEK = /[a-z_\u0370-\u03ff]+/g
const NUMBER = /\d+(?:\.\d+)+|\d+/g
/** 连续中文串 */
const CJK_RUN = /[\u4e00-\u9fff]{2,}/g

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

  /** 全文/查询共用的入口 */
  tokenize(text: string): string[] {
    const out: string[] = []
    const lower = text.toLowerCase()
    // 1. 拉丁/希腊 token（保留原样，单字母也保留——idf 自有区分力）
    for (const m of lower.matchAll(LATIN_GREEK)) {
      const t = m[0]
      if (t.length > 0) out.push(t)
    }
    // 2. 数字（含小数，覆盖文章编号 10.8、数值 0.19/137.036）
    for (const m of lower.matchAll(NUMBER)) out.push(m[0])
    // 3. 中文串：词典最长匹配 + bigram 兜底
    for (const seg of text.matchAll(CJK_RUN)) {
      this.tokenizeCjk(seg[0], out)
    }
    return out
  }

  private tokenizeCjk(s: string, out: string[]): void {
    const n = s.length
    let i = 0
    while (i < n) {
      const candidates = this.byFirst.get(s[i])
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
