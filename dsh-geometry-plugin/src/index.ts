/**
 * index.ts — DeepSeek Harness 插件入口：几何论知识库（纯离线 BM25）。
 *
 * 安装：将本目录放入 DSH 插件扫描路径（如 scratch-plugin/），
 *       执行 pnpm dsh web 后 /plugin 中启用 geometry-knowledge。
 *
 * 提供四个工具：
 *   geo_list    — 文章清单（可按系列过滤）
 *   geo_search  — BM25 语义检索（文章分块，scope=articles|truth）
 *   geo_read    — 按文章编号/文件名读取原文（默认返回命中章节，whole=true 整篇）
 *   geo_truth   — 主库真理层检索（860 条已验证定理）
 *
 * 引用规范：所有检索结果必须标注文章编号（article_id/fname）与章节。
 */
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { loadIndex, type LoadedIndex } from './core/loader.js'
import { createEngine, type SearchEngine } from './core/search.js'
import { locateSection, sectionEnd, readSectionRaw, readArticleRaw, safeArticlePath } from './core/toc.js'

export const name = 'geometry-knowledge'
export const inject = ['tools']

const MAX_TEXT = 700 // geo_search 返回块文本截断
const MAX_SECTION = 6000 // geo_read 单次返回上限
const MAX_WHOLE = 12000 // whole=true 截断

function clampInt(v: unknown, def: number, min: number, max: number): number {
  const n = typeof v === 'number' ? v : Number(v)
  if (!Number.isFinite(n)) return def
  return Math.max(min, Math.min(max, Math.round(n)))
}

function textOut(text: string) {
  return [{ type: 'text' as const, text }]
}

export function apply(ctx: Context): void {
  let index: LoadedIndex | null = null
  let engine: SearchEngine | null = null

  function lazy(): { index: LoadedIndex; engine: SearchEngine } {
    if (!index || !engine) {
      index = loadIndex()
      engine = createEngine(index)
    }
    return { index, engine }
  }

  ctx.tools.register(defineTool({
    name: 'geo_list',
    description: '列出几何论知识库的文章清单（编号、标题、文件名、分块数）。可按系列过滤，如 series="10." 只看应用篇。',
    parameters: {
      series: { type: 'string', description: '文章编号前缀过滤，如 "10."、"0."、"5."，留空返回全部' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { series?: string }) {
      const { index } = lazy()
      const list = index.articleList
        .filter((a) => !args.series || a.id.startsWith(args.series))
        .map((a) => `${a.id} | ${a.title} | ${a.fname} | ${a.chunks}块`)
      const head = `几何论文章清单（共 ${list.length} 篇，过滤 series=${args.series ?? '全部'}）：\n`
      return head + list.join('\n')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_search',
    description:
      '在几何论知识库中检索（纯离线 BM25）。' +
      '查询建议先提取文章中的精确术语（如 θ_M、N_dec、η_K、Strouhal、谱刚性、弱混合角、Kolmogorov）。' +
      'scope=articles 检索 3224 个文章分块；scope=truth 检索主库 860 条已验证真理。' +
      '返回的 fname/article_id 用于 geo_read 深入阅读。',
    parameters: {
      query: { type: 'string', required: true, description: '检索词（精确术语效果最佳）' },
      top_k: { type: 'number', description: '返回条数，默认 5，最大 15' },
      scope: { type: 'string', description: 'articles | truth，默认 articles' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { query: string; top_k?: number; scope?: string }) {
      const { engine } = lazy()
      const topK = clampInt(args.top_k, 5, 1, 15)
      const scope = args.scope === 'truth' ? 'truth' : 'articles'
      if (scope === 'truth') {
        const hits = engine.searchTruth(args.query, topK)
        if (hits.length === 0) return `[truth] 无命中（查询: ${args.query}）。尝试改用文章中的精确术语。`
        const lines = hits.map((h, i) => {
          const r = h.record
          return `${i + 1}. [${h.score.toFixed(2)}] #${r.permanent_number ?? '?'} ${r.formula_name ?? ''}\n${(r.text ?? '').slice(0, MAX_TEXT)}`
        })
        return `[truth] ${hits.length} 条命中（query: ${args.query}）：\n\n` + lines.join('\n\n---\n\n')
      }
      const hits = engine.searchArticles(args.query, topK)
      if (hits.length === 0) return `[articles] 无命中（查询: ${args.query}）。尝试改用文章中的精确术语。`
      const lines = hits.map((h, i) => {
        const c = h.record
        return `${i + 1}. [${h.score.toFixed(2)}] ${c.article_id} §${h.section ?? '?'} (${c.fname})\n${(c.text ?? '').slice(0, MAX_TEXT)}`
      })
      return `[articles] ${hits.length} 条命中（query: ${args.query}）：\n\n` + lines.join('\n\n---\n\n')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_read',
    description:
      '读取几何论文章原文。article 接受文章编号（如 "10.8"）或文件名（如 "10.8_精密结构常数..."）。' +
      'section 为章节关键词（如 "Strouhal"、"推导"、"数值表"），命中后返回该章节完整原文；' +
      '不传 section 返回文章开头；whole=true 返回整篇（截断 12000 字符）。',
    parameters: {
      article: { type: 'string', required: true, description: '文章编号或文件名' },
      section: { type: 'string', description: '章节关键词' },
      whole: { type: 'boolean', description: 'true=整篇，默认 false' },
      max_chars: { type: 'number', description: '返回上限，默认 6000' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { article: string; section?: string; whole?: boolean; max_chars?: number }) {
      const { index } = lazy()
      const q = args.article.trim()
      const meta = index.articleList.find((a) => a.id === q || a.fname === q || a.fname.startsWith(q))
      if (!meta) {
        const prefix = index.articleList.filter((a) => a.id.startsWith(q)).slice(0, 8)
        const hint = prefix.length > 0 ? `相近编号：${prefix.map((a) => a.id).join('、')}` : '用 geo_list 查看全部文章。'
        return `未找到文章 "${q}"。${hint}`
      }
      const p = safeArticlePath(index.articlesDir, meta.fname)
      if (!p) return `文章 ${meta.id} 原文缺失（data/articles/ 未打包该文件）。`
      const toc = index.toc[meta.fname] ?? []
      const maxChars = clampInt(args.max_chars, MAX_SECTION, 500, 50000)

      if (args.whole) {
        return `# ${meta.id} ${meta.title}\n\n${readArticleRaw(p, Math.min(MAX_WHOLE, maxChars))}`
      }
      if (args.section) {
        const m = locateSection(toc, args.section)
        if (!m) {
          const titles = toc.filter((e) => e.level <= 2).map((e) => e.title).slice(0, 20)
          return `文章 ${meta.id} 无章节匹配 "${args.section}"。可用章节：${titles.join(' / ')}`
        }
        const end = sectionEnd(toc, m.tocIndex)
        const raw = readSectionRaw(p, m.entry.offset, end)
        return `# ${meta.id} ${meta.title}\n## ${m.entry.title}\n\n${raw.slice(0, maxChars)}`
      }
      // 无 section：文章开头
      return `# ${meta.id} ${meta.title}\n\n${readArticleRaw(p, maxChars)}`
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_truth',
    description:
      '检索主库真理层（860 条已验证绝对真理，含永久编号 #N、公式名、证明摘要）。' +
      '用于确认某个定理是否已通过主库圆满验证；推导时应优先引用 #N 编号。',
    parameters: {
      query: { type: 'string', required: true, description: '检索词，如 "谱刚性"、"Berry 相位"、"互锁常数"' },
      top_k: { type: 'number', description: '默认 5，最大 10' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { query: string; top_k?: number }) {
      const { engine } = lazy()
      const topK = clampInt(args.top_k, 5, 1, 10)
      const hits = engine.searchTruth(args.query, topK)
      if (hits.length === 0) return `[truth] 无命中（查询: ${args.query}）。`
      const lines = hits.map((h, i) => {
        const r = h.record
        return `${i + 1}. [${h.score.toFixed(2)}] #${r.permanent_number ?? '?'} — ${r.formula_name ?? ''}\n${(r.text ?? '').slice(0, 1200)}`
      })
      return `[truth] ${hits.length} 条命中（query: ${args.query}）：\n\n` + lines.join('\n\n---\n\n')
    },
  }))

  // 预加载索引：插件激活时完成 BM25 构建，首次工具调用零延迟
  const s = lazy().engine.stats()
  ctx.logger.info(`[geometry-knowledge] 就绪：${s.articles} 分块 / ${s.truth} 真理 / ${s.dictTerms} 词典词，索引构建 ${s.buildMs}ms`)
}
