/**
 * summary.ts — 结构摘要视图（对标中间层 B2：元信息 + 章节目录 + 核心结论速览）。
 * geo_read 默认返回此摘要而非正文，省 token 且让 Agent 一眼看到文章要点。
 */
import fs from 'node:fs'
import type { TocEntry } from './loader.js'
import { sectionAt, sectionEnd, readSectionRaw, locateSection } from './toc.js'

export interface SummaryOptions {
  headChars?: number
  tocLimit?: number
  coreLines?: number
}

/**
 * 构建结构摘要视图：
 *   1. 头部元信息块（开头到第一个 ## 前的正文，含版本/依赖/摘要/核心结果）
 *   2. 增强章节目录（每个 ## 标题带 offset + 预估字数）
 *   3. 核心结论速览（头部块中含数字/结论词的短句）
 */
export function buildSummaryView(
  mdPath: string,
  toc: TocEntry[] | undefined,
  total: number,
  opts: SummaryOptions = {},
): string {
  const headChars = opts.headChars ?? 1400
  const tocLimit = opts.tocLimit ?? 40
  const coreLines = opts.coreLines ?? 5

  const md = fs.readFileSync(mdPath, 'utf-8')

  // 1) 头部块：开头到第一个 '## ' 章节标题之间
  const lines = md.split('\n')
  let headEnd = 0
  let firstSec = ''
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('## ') && i > 0) {
      headEnd = lines.slice(0, i).join('\n').length + 1
      firstSec = lines[i].trim()
      // 若首章节是「摘要」，把摘要正文并入头部（核心结论）
      const t = firstSec.replace(/^#+\s*/, '').trim()
      if (['摘要', 'Abstract', 'overview', '总览', 'abstract'].includes(t.toLowerCase())) {
        for (let j = i + 1; j < lines.length; j++) {
          if (lines[j].startsWith('## ')) {
            headEnd = lines.slice(0, j).join('\n').length + 1
            break
          }
        }
      }
      break
    }
  }
  if (headEnd === 0) headEnd = Math.min(md.length, 1600)
  let headBlock = md.slice(0, Math.min(headEnd, md.length)).trim()
  if (!headBlock) headBlock = md.slice(0, Math.min(1200, md.length))

  // 2) 增强目录：每个 ## 章节带 offset + 预估字数
  const tocLines = ['【章节目录】']
  const secs = (toc ?? []).filter((e) => e.level <= 2)
  if (secs.length > 0) {
    for (let i = 0; i < secs.length && i < tocLimit; i++) {
      const e = secs[i]
      const end = secs[i + 1] ? secs[i + 1].offset : total
      tocLines.push(`- ${e.title}  (offset=${e.offset}, ~${Math.max(end - e.offset, 0)}字)`)
    }
    if (secs.length > tocLimit) tocLines.push(`  ...共 ${secs.length} 个章节`)
  } else {
    tocLines.push('  (无 ## 章节标题)')
  }

  // 3) 核心结论速览：头部块中含数字/结论词的短句
  const coreLinesOut: string[] = []
  const coreRe = /\d+\.\d+|\d+[%％]|=|≈|定理|命题|结论|核心|关键|唯一|确定/
  for (const ln of headBlock.split('\n')) {
    const t = ln.trim()
    if (!t || t.startsWith('#')) continue
    if (coreRe.test(t) && t.length >= 15 && t.length <= 200) {
      coreLinesOut.push(t)
      if (coreLinesOut.length >= coreLines) break
    }
  }

  const headTrim = headBlock.length > headChars ? headBlock.slice(0, headChars) + '...[头部截断，见章节]' : headBlock

  let out = `===== 结构摘要（省 token，默认）=====\n${headTrim}\n\n` + tocLines.join('\n')
  if (coreLinesOut.length > 0) {
    out += `\n\n【核心结论速览】\n` + coreLinesOut.map((c) => `- ${c}`).join('\n')
  }
  out +=
    `\n\n【引导】需要某章节正文时，用 section='章节关键词'（如 section='公理'）精确拉取片段；` +
    `或 whole=true 整篇读取。全文一次性读取消耗大量 token，请只看需要的章节。`
  return out
}

/** 章节跳转读取（对标中间层 section 参数）：返回章节标题 + 原文片段 + 下一篇提示 */
export function readSectionWithHint(
  mdPath: string,
  toc: TocEntry[] | undefined,
  keyword: string,
  maxChars: number,
): { found: boolean; text: string } {
  const m = locateSection(toc, keyword)
  if (!m) {
    const titles = (toc ?? []).filter((e) => e.level <= 2).map((e) => e.title).slice(0, 20)
    return { found: false, text: `无章节匹配 "${keyword}"。可用章节：${titles.join(' / ')}` }
  }
  const end = sectionEnd(toc, m.tocIndex)
  const raw = readSectionRaw(mdPath, m.entry.offset, end)
  const next = (toc ?? [])[m.tocIndex + 1]
  const nextHint = next ? `\n下一篇: ${next.title} (offset=${next.offset})` : ''
  return {
    found: true,
    text: `## ${m.entry.title}\n位置: ${m.entry.offset}-${end ?? 'EOF'}${nextHint}\n\n${raw.slice(0, maxChars)}`,
  }
}

export { sectionAt }
