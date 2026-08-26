/**
 * index.ts — DeepSeek Harness 插件入口：几何论知识库（纯离线 BM25）。
 *
 * 安装：将本目录放入 DSH 插件扫描路径（如 scratch-plugin/），
 *       执行 pnpm dsh web 后 /plugin 中启用 geometry-knowledge。
 *
 * 提供五个工具：
 *   geo_list    — 文章清单（可按系列过滤）
 *   geo_search  — BM25 语义检索（文章分块，scope=articles|truth）
 *   geo_read    — 读取文章（默认结构摘要视图 + section 跳转 + whole 整篇 + 翻页防护）
 *   geo_calc    — 精确数学计算（纯 JS 安全求值，会话内中间变量保留）
 *   geo_truth   — 主库真理层检索（860 条已验证定理）
 *
 * 引用规范：所有检索结果必须标注文章编号（article_id/fname）与章节。
 */
import type { Context } from '@deepseek-ai/cordis'
import { defineTool, type ToolRunContext } from '@deepseek-ai/dsh-tools'
import { loadIndex, resolveDataDir, type LoadedIndex } from './core/loader.js'
import { createEngine, type SearchEngine } from './core/search.js'
import { locateSection, sectionEnd, readSectionRaw, readArticleRaw, safeArticlePath } from './core/toc.js'
import { buildSummaryView, readSectionWithHint } from './core/summary.js'
import { calcResult, getNs, resetNs } from './core/calc.js'
import { recordRead, resetReadState } from './core/guard.js'
import { buildRefChain, extractArticleNumber } from './core/refchain.js'
import { latexToUnicode, hasLatex } from './core/latex.js'

export const name = 'geometry-knowledge'
export const inject = ['tools']

/**
 * 插件配置（cordis.patch.yml 的 config 字段）：
 *   dataDir — 显式指定数据目录（优先级最高；缺省时依次回退 GEO_DATA_DIR、
 *             工作目录 ./geo-data/ 覆盖、包内内置数据）
 */
export interface GeometryKnowledgeConfig {
  dataDir?: string
}

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

export function apply(ctx: Context, config: GeometryKnowledgeConfig = {}): void {
  let index: LoadedIndex | null = null
  let engine: SearchEngine | null = null
  let refChain: ReturnType<typeof buildRefChain> | null = null

  function lazy(): { index: LoadedIndex; engine: SearchEngine; refChain: ReturnType<typeof buildRefChain> } {
    if (!index || !engine || !refChain) {
      index = loadIndex(config.dataDir)
      engine = createEngine(index)
      refChain = buildRefChain(index)
    }
    return { index, engine, refChain }
  }

  // 预取计数（描述动态化，A2：避免硬编码 3224/860 过期）
  const pre = lazy()
  const COUNTS = pre.engine.stats()

  /** 会话 key：优先取工具执行上下文的 agent id（零注入，A1），退化到全局 */
  function sessionKey(exec: ToolRunContext): string {
    return exec.agent?.id ?? 'default'
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
      '在几何论知识库中检索（纯离线 BM25，含单字扩展 + 查询扩展）。' +
      '查询建议先提取文章中的精确术语（如 θ_M、N_dec、η_K、Strouhal、谱刚性、弱混合角、Kolmogorov）。' +
      `scope=articles 检索 ${COUNTS.articles} 个文章分块；scope=truth 检索主库 ${COUNTS.truth} 条已验证真理（推荐用专用入口 geo_truth）。` +
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
      const { index, engine } = lazy()
      const topK = clampInt(args.top_k, 5, 1, 15)
      const scope = args.scope === 'truth' ? 'truth' : 'articles'
      if (scope === 'truth') {
        const hits = engine.searchTruth(args.query, topK)
        if (hits.length === 0) return `[truth] 无命中（查询: ${args.query}）。尝试改用文章中的精确术语。`
        const lines = hits.map((h, i) => {
          const r = h.record
          return `${i + 1}. [${h.score.toFixed(2)}] #${r.permanent_number ?? '?'} ${r.formula_name ?? ''}\n${(r.text ?? '').slice(0, MAX_TEXT)}`
        })
        return `[truth] ${hits.length} 条命中（query: ${args.query}）（完整字段见 geo_truth）：\n\n` + lines.join('\n\n---\n\n')
      }
      const hits = engine.searchArticles(args.query, topK)
      if (hits.length === 0) return `[articles] 无命中（查询: ${args.query}）。尝试改用文章中的精确术语。`
      const titleOf = (c: { article_id?: string; fname?: string }): string => {
        const meta = index.articleList.find((a) => a.id === c.article_id || a.fname === c.fname)
        return meta?.title ? `《${meta.title}》` : ''
      }
      const lines = hits.map((h, i) => {
        const c = h.record
        const text = hasLatex(c.text ?? '') ? latexToUnicode(c.text ?? '') : (c.text ?? '')
        return `${i + 1}. [${h.score.toFixed(2)}] ${c.article_id} §${h.section ?? '?'} ${titleOf(c)} (${c.fname})\n${text.slice(0, MAX_TEXT)}`
      })
      return `[articles] ${hits.length} 条命中（query: ${args.query}）：\n\n` + lines.join('\n\n---\n\n')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_read',
    description:
      '读取几何论文章。article 接受文章编号（如 "10.8"）或文件名。' +
      '【默认返回结构摘要视图】= 头部元信息（版本/依赖/摘要/核心结果）+ 带 offset 的章节目录 + 核心结论速览，绝不全文。' +
      '需要某章节细节时用 section=\'章节关键词\' 精确拉取该章节片段（推荐）；whole=true 一次获取整篇（截断 12000 字符）。' +
      '【可读性】输出中的 LaTeX 数学自动转换为 Unicode（$\\theta_M$ → θ_M、\\Lambda_H → Λ_H）。' +
      '【token 节省纪律】系统会检测顺序翻页读取并警告，单篇文章累计读取超 25000 字符将被拒绝。优先用摘要视图 + section 精准跳转。',
    parameters: {
      article: { type: 'string', required: true, description: '文章编号或文件名' },
      section: { type: 'string', description: '章节关键词，如 "公理"、"Strouhal"、"数值表"' },
      whole: { type: 'boolean', description: 'true=整篇，默认 false' },
      max_chars: { type: 'number', description: '返回上限，默认 6000' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { article: string; section?: string; whole?: boolean; max_chars?: number }, exec: ToolRunContext) {
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
      const total = index.articleSize[meta.fname] ?? 0

      // 会话 key（A1：exec.agent 零注入；DSH 上下文可能无 agent，退化到全局）
      const sk = sessionKey(exec)
      // 防护记录：whole 或 section 或默认摘要
      if (args.whole) {
        const g = recordRead(sk, meta.fname, 0, Math.min(total, 12000))
        const body = readArticleRaw(p, Math.min(MAX_WHOLE, maxChars))
        const rendered = latexToUnicode(body)
        return g ? `${g}\n\n${rendered}` : `# ${meta.id} ${meta.title}\n\n${rendered}`
      }
      if (args.section) {
        const r = readSectionWithHint(p, toc, args.section, maxChars)
        if (!r.found) {
          const titles = toc.filter((e) => e.level <= 2).map((e) => e.title).slice(0, 20)
          return `文章 ${meta.id} 无章节匹配 "${args.section}"。可用章节：${titles.join(' / ')}`
        }
        // 估算区间用于防护
        const sec = locateSection(toc, args.section)
        if (sec) {
          const end = sectionEnd(toc, sec.tocIndex)
          const g = recordRead(sk, meta.fname, sec.entry.offset, end ?? total)
          const rendered = latexToUnicode(r.text)
          return g ? `${g}\n\n${rendered}` : `# ${meta.id} ${meta.title}\n${rendered}`
        }
        return `# ${meta.id} ${meta.title}\n${latexToUnicode(r.text)}`
      }
      // 默认：结构摘要视图
      return latexToUnicode(`文件: ${meta.fname} (共${total}字符)\n` + buildSummaryView(p, toc, total))
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_calc',
    description:
      '精确数学/数值计算工具（纯 JS 安全求值，零依赖，对标中间层 calculate_math）。' +
      '适用于：数值计算、公式求值、角度/比例核对、方程数值验证。' +
      '支持：+ - * / ** % 、sin/cos/tan/asin/acos/atan/atan2、sqrt/cbrt/abs、ln/log/log10/log2、exp、' +
      'floor/ceil/round/min/max、hypot/sign/gcd/lcm/factorial/binom、阶乘后缀 5!、rad/deg 角度转换、' +
      '常数 pi/E。' +
      '支持多行赋值（分号分隔），中间变量跨调用保留并回显（如 D=10/7821; D*2）。' +
      '【token 节省纪律】同一表达式如已计算过请直接复用结果，不要重复调用；' +
      '角度制请用弧度（如 sin(30*pi/180)）。',
    parameters: {
      expression: { type: 'string', required: true, description: '要计算的表达式，如 "57.93+26.16+5.91"、"sin(pi/4)"、"a=2; a**10"' },
      symbolic: { type: 'boolean', description: '是否返回完整精确结果（纯 JS 版本仅数值，此参数预留）' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { expression: string; symbolic?: boolean }, exec: ToolRunContext) {
      const sk = sessionKey(exec)
      const ns = getNs(sk)
      const r = calcResult(args.expression ?? '', ns)
      return r.text
    },
  }))

  ctx.tools.register(defineTool({
    name: 'geo_truth',
    description:
      `检索主库真理层（${COUNTS.truth} 条已验证绝对真理，含永久编号 #N、公式名、证明摘要、验证时间、来源、文章出处）。` +
      '用于确认某个定理是否已通过主库圆满验证；推导时应优先引用 #N 编号。' +
      '【出处反查】命中结果自动给出来源文章与章节（章节标题级定义优先），可直接用 geo_read 深入。' +
      '这是真理层专用入口（比 geo_search scope=truth 返回更完整字段）。',
    parameters: {
      query: { type: 'string', required: true, description: '检索词，如 "谱刚性"、"Berry 相位"、"互锁常数"' },
      top_k: { type: 'number', description: '默认 5，最大 10' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value: string) => textOut(value),
    },
    async execute(args: { query: string; top_k?: number }) {
      const { engine, refChain } = lazy()
      const topK = clampInt(args.top_k, 5, 1, 10)
      const hits = engine.searchTruth(args.query, topK)
      if (hits.length === 0) return `[truth] 无命中（查询: ${args.query}）。`
      const lines = hits.map((h, i) => {
        const r = h.record
        // C1：按 formula_name 中的文章编号反查出处
        const number = extractArticleNumber(r.formula_name, r.text)
        const ref = number ? refChain.lookup(number) : undefined
        const meta = [
          r.permanent_number ? `#${r.permanent_number}` : null,
          r.formula_name ?? null,
          ref ? `出处 ${ref.fname}${ref.section ? ` §${ref.section}` : ''}` : null,
          r.verified_at ? `验证于 ${r.verified_at.slice(0, 10)}` : null,
          r.source ? `来源 ${r.source}` : null,
        ].filter(Boolean).join(' | ')
        return `${i + 1}. [${h.score.toFixed(2)}] ${meta}\n${(r.text ?? '').slice(0, 1200)}`
      })
      return `[truth] ${hits.length} 条命中（query: ${args.query}）：\n\n` + lines.join('\n\n---\n\n')
    },
  }))

  // 预加载索引 + 预热 BM25：插件激活时完成全部构建，首次工具调用零延迟
  lazy().engine.warm()
  const s = lazy().engine.stats()
  const resolved = resolveDataDir(config.dataDir)
  const sourceLabel =
    resolved.source === 'config' ? '配置 dataDir' :
    resolved.source === 'env' ? '环境变量 GEO_DATA_DIR' :
    resolved.source === 'cwd' ? '工作目录 geo-data 覆盖' : '包内内置数据'
  ctx.logger.info(`[geometry-knowledge] 就绪：${s.articles} 分块 / ${s.truth} 真理 / ${s.dictTerms} 词典词，索引构建 ${s.buildMs}ms，数据源：${sourceLabel}（${resolved.dataDir}）`)
}
