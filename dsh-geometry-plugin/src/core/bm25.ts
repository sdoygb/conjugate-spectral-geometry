/**
 * bm25.ts — 标准 BM25（k1=1.5, b=0.75），索引惰性构建。
 * 内存优化：文档频率 df 全局统计；每文档 TF 用 Map（唯一 token 稀疏存储）。
 */
import type { Tokenizer } from './tokenize.js'

export interface Bm25Index {
  n: number
  avgDl: number
  dl: Float32Array
  tfList: Map<string, number>[]
  df: Map<string, number>
}

export interface Bm25Hit {
  i: number
  score: number
}

export function buildIndex<T>(docs: readonly T[], getText: (d: T) => string, tok: Tokenizer): Bm25Index {
  const n = docs.length
  const dl = new Float32Array(n)
  const tfList: Map<string, number>[] = new Array(n)
  const df = new Map<string, number>()
  let totalLen = 0
  for (let i = 0; i < n; i++) {
    const toks = tok.tokenize(getText(docs[i]))
    dl[i] = toks.length || 1
    totalLen += toks.length
    const tf = new Map<string, number>()
    const seen = new Set<string>()
    for (const t of toks) {
      tf.set(t, (tf.get(t) ?? 0) + 1)
      if (!seen.has(t)) {
        seen.add(t)
        df.set(t, (df.get(t) ?? 0) + 1)
      }
    }
    tfList[i] = tf
  }
  return { n, avgDl: n > 0 ? totalLen / n : 1, dl, tfList, df }
}

export function queryIndex(index: Bm25Index, queryTokens: string[], topK: number): Bm25Hit[] {
  const { n, avgDl, dl, tfList, df } = index
  const scores = new Float64Array(n)
  const k1 = 1.5
  const b = 0.75
  for (const t of queryTokens) {
    const nT = df.get(t) ?? 0
    if (nT === 0) continue
    const idf = Math.log(1 + (n - nT + 0.5) / (nT + 0.5))
    for (let i = 0; i < n; i++) {
      const f = tfList[i].get(t)
      if (!f) continue
      scores[i] += idf * ((f * (k1 + 1)) / (f + k1 * (1 - b + (b * dl[i]) / avgDl)))
    }
  }
  const idx = Array.from({ length: n }, (_, i) => i)
  idx.sort((a, b2) => scores[b2] - scores[a])
  const out: Bm25Hit[] = []
  for (let k = 0; k < topK && k < n; k++) {
    if (scores[idx[k]] <= 0) break
    out.push({ i: idx[k], score: scores[idx[k]] })
  }
  return out
}
