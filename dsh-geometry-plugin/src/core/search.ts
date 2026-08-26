/**
 * search.ts — 纯 BM25 检索（无向量路径）。
 * 命中块附带所在章节标题（toc 定位），供 geo_read 深入阅读。
 *
 * 检索增强：
 *   - 查询端用 queryTokenize（中文单字前缀扩展，B1）
 *   - RM3 风格查询扩展（B3）：首轮命中 top-3 块的高频非查询 token 回注，
 *     再做第二轮检索，缓解术语变体与稀疏查询漏召。
 */
import type { ArticleChunk, LoadedIndex, TruthRecord } from './loader.js'
import { Tokenizer } from './tokenize.js'
import { buildIndex, queryIndex, type Bm25Index } from './bm25.js'
import { sectionAt } from './toc.js'

export interface SearchHit<T> {
  score: number
  record: T
  section?: string
}

export interface SearchEngine {
  searchArticles(query: string, topK: number): SearchHit<ArticleChunk>[]
  searchTruth(query: string, topK: number): SearchHit<TruthRecord>[]
  /** 预热：构建文章/真理两套 BM25 索引（插件激活时调用，避免首次工具调用卡顿） */
  warm(): void
  stats(): { articles: number; truth: number; dictTerms: number; buildMs: number }
}

/** RM3 查询扩展：返回补充 token（top-3 块的高频非查询 token，最多 8 个） */
function expandQuery(
  tok: Tokenizer,
  index: Bm25Index,
  queryTokens: string[],
  getText: (i: number) => string,
): string[] {
  const first = queryIndex(index, queryTokens, 3)
  if (first.length === 0) return []
  const qset = new Set(queryTokens)
  const freq = new Map<string, number>()
  for (const h of first) {
    for (const t of tok.tokenize(getText(h.i))) {
      if (qset.has(t)) continue
      // 过滤单字母与纯数字（噪声）
      if (t.length === 1 && !/[a-z]/.test(t)) continue
      if (/^\d+(\.\d+)?$/.test(t)) continue
      freq.set(t, (freq.get(t) ?? 0) + 1)
    }
  }
  // 出现 ≥2 次的 token 才有资格（跨块共识），按频率降序取前 8
  return [...freq.entries()]
    .filter(([, c]) => c >= 2)
    .sort((a, b) => b[1] - a[1] || a[0].length - b[0].length)
    .slice(0, 8)
    .map(([t]) => t)
}

export function createEngine(index: LoadedIndex): SearchEngine {
  const tok = new Tokenizer(index.dictTerms)
  let articlesIdx: Bm25Index | null = null
  let truthIdx: Bm25Index | null = null
  let buildMs = 0

  function ensureArticles(): Bm25Index {
    if (!articlesIdx) {
      const t0 = Date.now()
      articlesIdx = buildIndex(index.chunks, (c) => c.text, tok)
      buildMs += Date.now() - t0
    }
    return articlesIdx
  }

  function ensureTruth(): Bm25Index {
    if (!truthIdx) {
      const t0 = Date.now()
      truthIdx = buildIndex(index.truth, (r) => `${r.formula_name ?? ''} ${r.text}`, tok)
      buildMs += Date.now() - t0
    }
    return truthIdx
  }

  return {
    warm() {
      ensureArticles()
      ensureTruth()
    },

    searchArticles(query: string, topK: number): SearchHit<ArticleChunk>[] {
      const q = tok.queryTokenize(query)
      if (q.length === 0) return []
      const idx = ensureArticles()
      const expanded = [...q, ...expandQuery(tok, idx, q, (i) => index.chunks[i].text)]
      return queryIndex(idx, expanded, topK).map((h) => {
        const c = index.chunks[h.i]
        const sec = sectionAt(index.toc[c.fname], c.start ?? 0)
        return { score: h.score, record: c, section: sec?.title }
      })
    },

    searchTruth(query: string, topK: number): SearchHit<TruthRecord>[] {
      const q = tok.queryTokenize(query)
      if (q.length === 0) return []
      const idx = ensureTruth()
      const expanded = [...q, ...expandQuery(tok, idx, q, (i) => `${index.truth[i].formula_name ?? ''} ${index.truth[i].text}`)]
      return queryIndex(idx, expanded, topK).map((h) => ({
        score: h.score,
        record: index.truth[h.i],
      }))
    },

    stats() {
      return {
        articles: index.chunks.length,
        truth: index.truth.length,
        dictTerms: index.dictTerms.length,
        buildMs,
      }
    },
  }
}
