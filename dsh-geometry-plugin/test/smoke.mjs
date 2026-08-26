/**
 * smoke.mjs — 冒烟测试：验证 BM25 检索质量 + 章节定位 + 数据目录解析（不依赖 DSH 运行时）
 *
 * 用法：cd dsh-geometry-plugin && node test/smoke.mjs
 */
import { loadIndex, resolveDataDir } from '../dist/core/loader.js'
import { createEngine } from '../dist/core/search.js'
import { locateSection, sectionEnd, readSectionRaw, safeArticlePath } from '../dist/core/toc.js'
import { buildSummaryView, readSectionWithHint } from '../dist/core/summary.js'
import { calcResult, getNs, resetNs } from '../dist/core/calc.js'
import { recordRead, resetReadState, VIEW_CHAR_LIMIT } from '../dist/core/guard.js'
import path from 'node:path'
import fs from 'node:fs'
import os from 'node:os'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const t0 = Date.now()
const index = loadIndex()
const engine = createEngine(index)
const tWarm0 = Date.now()
engine.warm() // 激活时预热：首次工具调用零延迟
const buildMs = Date.now() - tWarm0
const tSearch0 = Date.now()
engine.searchArticles('Strouhal 数', 3)
const firstSearchMs = Date.now() - tSearch0
const s = engine.stats()
console.log(`[load] 分块 ${s.articles} / 真理 ${s.truth} / 词典 ${s.dictTerms} 词，加载 ${Date.now() - t0}ms，BM25 预热 ${buildMs}ms，预热后首次搜索 ${firstSearchMs}ms`)
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

// ── 新功能：geo_calc（纯 JS 安全求值） ─────────────────────────
console.log('══════════ geo_calc 数学计算 ══════════')
{
  const ns = getNs('smoke-test')
  const cases = [
    ['57.93+26.16+5.91', '三角和 → 90'],
    ['sin(pi/4)', 'sin(π/4) → 0.707'],
    ['a=2; a**10', '赋值+幂 → 1024'],
    ['sqrt(2)', '√2 → 1.414'],
    ['27.16/4', '除法'],
    ['5.91/2', '除法'],
    ['ln(exp(1))', 'ln(e) → 1'],
  ]
  for (const [expr, note] of cases) {
    const r = calcResult(expr, ns)
    console.log(`  ${expr}  =>  ${r.text.split('\n').pop()}  （${note}）`)
    if (!r.ok) console.log('    ❌ 计算失败！')
  }
  // 会话变量保留
  calcResult('D=10/7821', ns)
  const r2 = calcResult('D*2', ns)
  console.log(`  会话变量 D 跨调用: D=10/7821; D*2 => ${r2.text.split('\n').pop()}  （应为 20/7821≈0.00256）`)
  resetNs('smoke-test')
  const r3 = calcResult('D*2', getNs('smoke-test'))
  console.log(`  重置后 D: ${r3.text.split('\n').pop()}  （应为未知符号错误）`)
  // 安全：禁止 eval 类
  const bad = calcResult('process.exit(1)', getNs('smoke-test'))
  console.log(`  恶意输入拦截: ${bad.ok ? '❌ 未拦截！' : '✅ 已拦截 ' + bad.text.split('\n').pop()}`)
}

// ── 新功能：结构摘要视图（buildSummaryView） ─────────────────────
console.log('══════════ geo_read 结构摘要视图 ══════════')
{
  const fname = '7.5_弱混合角_CN_260808.md'
  const p = safeArticlePath(index.articlesDir, fname)
  if (p) {
    const toc = index.toc[fname] ?? []
    const size = fs.statSync(p).size
    const sv = buildSummaryView(p, toc, size)
    console.log(`  摘要视图 ${sv.length} 字符（文章 ${size} 字符）`)
    console.log('  ' + sv.split('\n').slice(0, 3).join('\n  '))
    console.log('  ...')
    const hasToc = sv.includes('【章节目录】')
    const hasCore = sv.includes('【核心结论速览】')
    const hasGuide = sv.includes('【引导】')
    console.log(`  章节目录: ${hasToc ? '✅' : '❌'} | 核心结论: ${hasCore ? '✅' : '❌'} | 引导: ${hasGuide ? '✅' : '❌'}`)
    // section 跳转
    const r = readSectionWithHint(p, toc, '弱混合角', 800)
    console.log(`  section 跳转 "弱混合角": ${r.found ? '✅ 命中 ' + r.text.slice(0, 40) + '…' : '❌ ' + r.text.slice(0, 60)}`)
  } else {
    console.log('  （7.5 文章缺失，跳过）')
  }
}

// ── 新功能：翻页防护（guard） ─────────────────────────────────
console.log('══════════ geo_read 翻页防护 ══════════')
{
  resetReadState('smoke-guard')
  const g1 = recordRead('smoke-guard', 'f1.md', 0, 5000)
  const g2 = recordRead('smoke-guard', 'f1.md', 5000, 10000)
  const g3 = recordRead('smoke-guard', 'f1.md', 10000, 15000)
  console.log(`  第1段: ${g1 || '正常'}`)
  console.log(`  第2段(翻页): ${g2.includes('顺序翻页') ? '✅ 翻页检测' : '❌ 未检测'}`)
  console.log(`  第3段: ${g3.includes('顺序翻页') ? '✅ 翻页检测' : '❌ 未检测'}`)
  // 超限
  resetReadState('smoke-guard2')
  let last = ''
  for (let i = 0; i < 6; i++) {
    last = recordRead('smoke-guard2', 'big.md', i * 5000, i * 5000 + 5000)
  }
  console.log(`  累计 ${6 * 5000} 字符: ${last.includes(`上限 ${VIEW_CHAR_LIMIT}`) ? '✅ 超限拦截' : '❌ 未拦截 ' + last.slice(0, 40)}`)
}

console.log('')
console.log('[smoke] 新功能测试完成')

// ── 数据目录解析：工作目录 geo-data 覆盖 ──────────────────────────
console.log('══════════ 数据目录解析（resolveDataDir） ══════════')
{
  // 正例：<cwd>/geo-data/ 存在且含核心文件 → 应命中 'cwd'
  const tmpWs = fs.mkdtempSync(path.join(os.tmpdir(), 'geo-ws-'))
  const gd = path.join(tmpWs, 'geo-data')
  fs.mkdirSync(gd)
  for (const f of ['articles.jsonl', 'truth.jsonl', 'articles_toc.json', 'dict.json']) {
    fs.writeFileSync(path.join(gd, f), '')
  }
  const oldCwd = process.cwd()
  process.chdir(tmpWs)
  const r1 = resolveDataDir()
  process.chdir(oldCwd)
  fs.rmSync(tmpWs, { recursive: true, force: true })
  console.log(`cwd 覆盖: ${r1.source === 'cwd' ? '生效 ✓' : '未生效 ✗'}（${r1.dataDir}）`)

  // 反例：工作目录无 geo-data（或无效副本）→ 应回退 'package'
  const r2 = resolveDataDir()
  console.log(`无覆盖回退: ${r2.source === 'package' ? '包内数据 ✓' : '异常 ✗'}（${r2.dataDir}）`)
}
