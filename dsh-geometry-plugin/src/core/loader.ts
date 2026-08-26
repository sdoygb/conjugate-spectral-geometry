/**
 * loader.ts — 加载离线索引（articles.jsonl / truth.jsonl / articles_toc.json / dict.json / 全文）
 * 零运行时依赖。
 *
 * 数据目录解析优先级（高 → 低）：
 *   1. 插件配置 dataDir（cordis.patch.yml 的 config.dataDir）
 *   2. 环境变量 GEO_DATA_DIR
 *   3. 工作目录覆盖 <cwd>/geo-data/（须为完整数据副本，自动检测）
 *   4. 包内内置数据 data/
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
  verified_at?: string
  source?: string
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
  articleSize: Record<string, number>
  dataDir: string
  articlesDir: string
}

export type DataSource = 'config' | 'env' | 'cwd' | 'package'

export interface ResolvedDataDir {
  dataDir: string
  articlesDir: string
  source: DataSource
}

/** 工作目录覆盖目录名：安装者把完整 data/ 副本放到 <cwd>/geo-data/ 即自动生效 */
export const CWD_OVERRIDE_DIR = 'geo-data'

/** 判定一个目录是否为完整数据副本（缺任一核心文件则视为无效，回退包内数据） */
const REQUIRED_FILES = ['articles.jsonl', 'truth.jsonl', 'articles_toc.json', 'dict.json']

function isValidDataDir(dir: string): boolean {
  try {
    return REQUIRED_FILES.every((f) => fs.existsSync(path.join(dir, f)))
  } catch {
    return false
  }
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

export function resolveDataDir(dataDir?: string): ResolvedDataDir {
  // 1) 插件配置 dataDir（最高优先级，显式指定）
  if (dataDir) return { dataDir, articlesDir: path.join(dataDir, 'articles'), source: 'config' }
  // 2) 环境变量 GEO_DATA_DIR
  const env = process.env.GEO_DATA_DIR
  if (env) return { dataDir: env, articlesDir: path.join(env, 'articles'), source: 'env' }
  // 3) 工作目录覆盖：<cwd>/geo-data/（安装者把完整 data/ 副本放工作目录即自动生效）
  const cwdOverride = path.join(process.cwd(), CWD_OVERRIDE_DIR)
  if (isValidDataDir(cwdOverride)) {
    return { dataDir: cwdOverride, articlesDir: path.join(cwdOverride, 'articles'), source: 'cwd' }
  }
  // 4) 包内内置数据（默认）
  const dir = path.join(__dirname, '..', '..', 'data')
  return { dataDir: dir, articlesDir: path.join(dir, 'articles'), source: 'package' }
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
  const articleSize: Record<string, number> = {}
  for (const a of articleList) articleSize[a.fname] = a.size

  return { chunks, truth, toc, dictTerms: dict.terms ?? [], articleList, articleSize, dataDir: dir, articlesDir }
}

function firstHeading(text: string): string {
  for (const line of text.split('\n')) {
    const m = line.match(/^\s*#+\s*(.+?)\s*$/)
    if (m) return m[1].trim()
  }
  return ''
}
