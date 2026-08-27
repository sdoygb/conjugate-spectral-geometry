/**
 * refchain.test.mjs — 真理→文章引用链单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildRefChain, extractArticleNumber } from '../../dist/core/refchain.js'

/** 构造最小 LoadedIndex 假数据 */
function fakeIndex() {
  const chunks = [
    // 10.1 正文里引用了 0.2.1.02（引用处）
    { chunk_id: 'c1', fname: '10.1_a.md', article_id: '10.1', start: 0, end: 100,
      text: '见定理 0.2.1.02 与引理 1.3.2.01（正文引用）。' },
    // 10.2 行首定义 0.2.1.02
    { chunk_id: 'c2', fname: '0.2_b.md', article_id: '0.2', start: 0, end: 100,
      text: '**命题 0.2.1.02（体积元的平方）**：ω² = (-1)^n。\n推论 0.2.1.03 直接成立。\n**注记 0.4.5.01（子回路圆满性）**：结构预览。' },
    // 10.3 章节标题含 1.3.2.01（heading 定义）
    { chunk_id: 'c3', fname: '1.3_c.md', article_id: '1.3', start: 500, end: 800,
      text: '## 引理 1.3.2.01（投影强度恒等式）\n\n设 L 为左乘表示。' },
  ]
  const toc = {
    '10.1_a.md': [{ level: 1, title: '10.1 文章', offset: 0 }],
    '0.2_b.md': [{ level: 1, title: '0.2 文章', offset: 0 }],
    '1.3_c.md': [
      { level: 1, title: '1.3 文章', offset: 0 },
      { level: 2, title: '## 引理 1.3.2.01（投影强度恒等式）', offset: 500 },
    ],
  }
  const dictTerms = []
  const articleList = [
    { id: '10.1', fname: '10.1_a.md', title: '10.1', chunks: 1, size: 100 },
    { id: '0.2', fname: '0.2_b.md', title: '0.2', chunks: 1, size: 100 },
    { id: '1.3', fname: '1.3_c.md', title: '1.3', chunks: 1, size: 300 },
  ]
  const articleSize = { '10.1_a.md': 100, '0.2_b.md': 100, '1.3_c.md': 300 }
  const truth = []
  return { chunks, toc, dictTerms, articleList, articleSize, dataDir: '', articlesDir: '', truth }
}

test('优先级：章节标题(heading) > 行首定义(lineHead) > 正文引用(body)', () => {
  const rc = buildRefChain(fakeIndex())
  // 0.2.1.02：10.1 正文引用 + 0.2 行首定义 → 应选 lineHead（0.2）
  const r1 = rc.lookup('0.2.1.02')
  assert.ok(r1, '0.2.1.02 应有出处')
  assert.equal(r1.kind, 'lineHead')
  assert.equal(r1.fname, '0.2_b.md')
  // 1.3.2.01：10.1 正文引用 + 1.3 章节标题 → 应选 heading（1.3）
  const r2 = rc.lookup('1.3.2.01')
  assert.ok(r2, '1.3.2.01 应有出处')
  assert.equal(r2.kind, 'heading')
  assert.equal(r2.fname, '1.3_c.md')
  assert.ok(r2.section.includes('1.3.2.01'))
  // 0.2.1.03：仅行首定义（0.2）
  const r3 = rc.lookup('0.2.1.03')
  assert.equal(r3.fname, '0.2_b.md')
  // 注记 0.4.5.01：行首'**注记 X.Y.Z**'也能被 lineHead 抓到（修复回归）
  const r4 = rc.lookup('0.4.5.01')
  assert.ok(r4, '注记编号应有出处')
  assert.equal(r4.kind, 'lineHead')
  assert.equal(r4.fname, '0.2_b.md')
  // 不存在的编号
  assert.equal(rc.lookup('9.9.9.99'), undefined)
})

test('extractArticleNumber 从 formula_name/text 提取编号', () => {
  assert.equal(extractArticleNumber('定理 10.17.0.05（谱刚性）', undefined), '10.17.0.05')
  assert.equal(extractArticleNumber(undefined, '见命题 3.1.2.04'), '3.1.2.04')
  assert.equal(extractArticleNumber('无编号定理', '文本'), undefined)
  assert.equal(extractArticleNumber(undefined, undefined), undefined)
})

test('rc.lookup 对无匹配编号返回 undefined', () => {
  const rc = buildRefChain(fakeIndex())
  assert.equal(rc.lookup('7.11.2.01'), undefined) // 数据缺口场景
})
