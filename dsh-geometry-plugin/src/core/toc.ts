/**
 * toc.ts — 章节定位：字符偏移 ↔ 章节标题；章节关键词 → 章节原文。
 */
import fs from 'node:fs'
import path from 'node:path'
import type { TocEntry } from './loader.js'

/** 找包含 offset 的章节（最近的 level<=2 标题），无标题返回 null */
export function sectionAt(toc: TocEntry[] | undefined, offset: number): { title: string; level: number } | null {
  if (!toc || toc.length === 0) return null
  let cur: TocEntry | null = null
  for (const e of toc) {
    if (e.offset > offset) break
    if (e.level <= 2) cur = e
  }
  return cur ? { title: cur.title, level: cur.level } : null
}

export interface SectionMatch {
  tocIndex: number
  entry: TocEntry
}

/** 按关键词定位章节：title 包含 keyword（大小写不敏感），优先最小 level、最小偏移 */
export function locateSection(toc: TocEntry[] | undefined, keyword: string): SectionMatch | null {
  if (!toc || toc.length === 0) return null
  const kw = keyword.toLowerCase()
  let best: SectionMatch | null = null
  for (let i = 0; i < toc.length; i++) {
    const e = toc[i]
    if (e.title.toLowerCase().includes(kw)) {
      if (!best || e.level < best.entry.level || (e.level === best.entry.level && e.offset < best.entry.offset)) {
        best = { tocIndex: i, entry: e }
      }
    }
  }
  return best
}

/** 从章节表索引 i 开始，取到下一个 level <= 该级别标题的偏移 */
export function sectionEnd(toc: TocEntry[] | undefined, fromIndex: number): number | null {
  if (!toc) return null
  const level = toc[fromIndex].level
  for (let i = fromIndex + 1; i < toc.length; i++) {
    if (toc[i].level <= level) return toc[i].offset
  }
  return null
}

/** 读取章节原文（md 的 [start, end) 区间） */
export function readSectionRaw(mdPath: string, start: number, end: number | null): string {
  const md = fs.readFileSync(mdPath, 'utf-8')
  const s = Math.max(0, start)
  const e = end === null ? md.length : Math.min(md.length, end)
  return md.slice(s, e).trim()
}

/** 读取整篇（截断到 maxChars） */
export function readArticleRaw(mdPath: string, maxChars?: number): string {
  const md = fs.readFileSync(mdPath, 'utf-8')
  return maxChars ? md.slice(0, maxChars) : md
}

/** 安全拼接文章路径（防路径穿越：fname 必须是 basename 且文件存在） */
export function safeArticlePath(articlesDir: string, fname: string): string | null {
  if (!fname || fname.includes('..') || path.basename(fname) !== fname) return null
  const p = path.join(articlesDir, fname)
  return fs.existsSync(p) ? p : null
}
