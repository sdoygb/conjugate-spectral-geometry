/**
 * loader.ts — 加载离线索引（articles.jsonl / truth.jsonl / articles_toc.json / dict.json / 全文）
 * 零运行时依赖。数据目录可用环境变量 GEO_DATA_DIR 覆盖。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export interface ArticleChunk {
  chunk_id: string
  fname: string
  article_id: string
  start: number
  end: number
  text: string
  [k: string]: unknown
}

export interface TruthRecord {
  chunk_id: string
  permanent_number?: string
  formula_name?: string
  text: string
  [k: string]: unknown
}

export interface TocEntry {
  level: number
  title: string
  offset: number
}

export interface ArticleMeta {
  id: string
  fname: string
  title: string
  chunks: number
  size: number
}

export interface LoadedIndex {
  chunks: ArticleChunk[]
  truth: TruthRecord[]
  toc: Record<string, TocEntry[]>
  dictTerms: string[]
  articleList: ArticleMeta[]
  dataDir: string
  articlesDir: string
}

const __dirname = path.dirname(fileURLToPath(import.meta.url))

function loadJsonl<T>(file: string): T[] {
  const raw = fs.readFileSync(file, 'utf-8')
  const out: T[] = []
  for (const line of raw.split('\n')) {
    if (line.trim()) out.push(JSON.parse(line) as T)
  }
  return out
}

export function resolveDataDir(dataDir?: string): { dataDir: string; articlesDir: string } {
  const dir = dataDir ?? process.env.GEO_DATA_DIR ?? path.join(__dirname, '..', '..', 'data')
  return { dataDir: dir, articlesDir: path.join(dir, 'articles') }
}

export function loadIndex(dataDir?: string): LoadedIndex {
  const { dataDir: dir, articlesDir } = resolveDataDir(dataDir)
  const chunks = loadJsonl<ArticleChunk>(path.join(dir, 'articles.jsonl'))
  const truth = loadJsonl<TruthRecord>(path.join(dir, 'truth.jsonl'))
  const toc = JSON.parse(fs.readFileSync(path.join(dir, 'articles_toc.json'), 'utf-8')) as Record<string, TocEntry[]>
  const dict = JSON.parse(fs.readFileSync(path.join(dir, 'dict.json'), 'utf-8')) as { terms: string[] }

  // 文章清单：按 article_id 去重（与全文目录核对存在性）
  const byId = new Map<string, ArticleMeta>()
  for (const c of chunks) {
    const id = c.article_id || c.fname
    const prev = byId.get(id)
    if (prev) {
      prev.chunks++
    } else {
      const fname = c.fname || ''
      const size = fs.existsSync(path.join(articlesDir, fname)) ? fs.statSync(path.join(articlesDir, fname)).size : 0
      byId.set(id, { id, fname, title: firstHeading(c.text), chunks: 1, size })
    }
  }
  const articleList = [...byId.values()].sort((a, b) => a.id.localeCompare(b.id, 'zh-Hans-CN', { numeric: true }))

  return { chunks, truth, toc, dictTerms: dict.terms ?? [], articleList, dataDir: dir, articlesDir }
}

function firstHeading(text: string): string {
  for (const line of text.split('\n')) {
    const m = line.match(/^\s*#+\s*(.+?)\s*$/)
    if (m) return m[1].trim()
  }
  return ''
}
