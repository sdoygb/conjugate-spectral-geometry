/**
 * search.ts — 纯 BM25 检索（无向量路径）。
 * 命中块附带所在章节标题（toc 定位），供 geo_read 深入阅读。
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
      const q = tok.tokenize(query)
      if (q.length === 0) return []
      return queryIndex(ensureArticles(), q, topK).map((h) => {
        const c = index.chunks[h.i]
        const sec = sectionAt(index.toc[c.fname], c.start ?? 0)
        return { score: h.score, record: c, section: sec?.title }
      })
    },

    searchTruth(query: string, topK: number): SearchHit<TruthRecord>[] {
      const q = tok.tokenize(query)
      if (q.length === 0) return []
      return queryIndex(ensureTruth(), q, topK).map((h) => ({
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
