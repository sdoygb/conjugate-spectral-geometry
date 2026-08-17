/**
 * smoke.mjs — 冒烟测试：验证 BM25 检索质量 + 章节定位（不依赖 DSH 运行时）
 *
 * 用法：cd dsh-geometry-plugin && node test/smoke.mjs
 */
import { loadIndex } from '../dist/core/loader.js'
import { createEngine } from '../dist/core/search.js'
import { locateSection, sectionEnd, readSectionRaw, safeArticlePath } from '../dist/core/toc.js'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const t0 = Date.now()
const index = loadIndex()
const engine = createEngine(index)
const s = engine.stats()
console.log(`[load] 分块 ${s.articles} / 真理 ${s.truth} / 词典 ${s.dictTerms} 词，加载 ${Date.now() - t0}ms，BM25 构建 ${s.buildMs}ms`)
console.log(`[articles] ${index.articleList.length} 篇，全文目录 ${index.articlesDir}`)
console.log('')

function show(title, hits, maxText = 90) {
  console.log(`▶ ${title}`)
  if (hits.length === 0) {
    console.log('  （无命中）')
    return
  }
  for (const [k, h] of hits.entries()) {
    const r = h.record
    const id = r.article_id ?? r.permanent_number ?? r.fname ?? r.chunk_id
    const sec = h.section ? ` | §${h.section}` : ''
    const txt = (r.text ?? '').replace(/\s+/g, ' ').slice(0, maxText)
    console.log(`  #${k + 1} score=${h.score.toFixed(2)} [${id}]${sec}`)
    console.log(`      ${txt}${txt.length >= maxText ? '…' : ''}`)
  }
  console.log('')
}

// ── 文章检索查询集（模拟真实使用场景） ──────────────────────────
const queries = [
  ['Strouhal 数', '期望命中 10.8（St=0.19 推导文章）'],
  ['Kolmogorov 尺度 大气湍流', '期望命中 10.8 §7.2（η_K≈1mm）'],
  ['弱混合角 sinθ_W', '期望命中 9.6 / 10.39 / 10.25'],
  ['中微子振荡 味混合', '期望命中 10.x 中微子文章'],
  ['Prandtl 数 动量扩散 热扩散', '期望命中 10.8/10.20（Pr_geo 修复后 1.92）'],
  ['η_K 数值', '期望命中 10.8（Kolmogorov 尺度）'],
  ['谱刚性 证明', '期望命中 主库/理论文章'],
  ['观测者位置 谱条件 窗口', '期望命中 1.5 / 谱条件相关'],
]

for (const [q, expect] of queries) {
  console.log(`── 查询: "${q}"  （${expect}）`)
  show('文章', engine.searchArticles(q, 3))
}

// ── 真理层检索 ────────────────────────────────────────────────
console.log('══════════ 真理层（master_truth, 860 条） ══════════')
for (const q of ['互锁常数', 'Berry 相位', '谱刚性']) {
  console.log(`── 查询: "${q}"`)
  show('真理', engine.searchTruth(q, 3))
}

// ── 章节定位：取第一个命中块的 fname，验证 geo_read 链路 ────────
console.log('══════════ geo_read 章节定位链路 ══════════')
const first = engine.searchArticles('弱混合角 sinθ_W', 1)[0]
if (first) {
  const fname = first.record.fname
  const mdPath = safeArticlePath(index.articlesDir, fname)
  const toc = index.toc[fname] ?? []
  console.log(`命中块: ${fname} @[${first.record.start},${first.record.end})`)
  console.log(`章节表条目数: ${toc.length}`)
  const sec = locateSection(toc, '混合角')
  if (sec && mdPath) {
    const end = sectionEnd(toc, sec.tocIndex)
    const raw = readSectionRaw(mdPath, sec.entry.offset, end)
    console.log(`locateSection("混合角") → §${sec.entry.title} (level ${sec.entry.level})`)
    console.log(`章节原文 ${raw.length} 字符，开头：`)
    console.log('  ' + raw.replace(/\s+/g, ' ').slice(0, 120) + '…')
  } else {
    console.log('（未定位到章节，或 md 不存在）')
  }
} else {
  console.log('（无命中，跳过）')
}

console.log('')
console.log('[smoke] 完成')
