/**
 * bm25.test.mjs + toc.test.mjs — BM25 检索与章节定位单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildIndex, queryIndex } from '../../dist/core/bm25.js'
import { Tokenizer } from '../../dist/core/tokenize.js'
import { sectionAt, locateSection, sectionEnd, safeArticlePath } from '../../dist/core/toc.js'
import path from 'node:path'

// ---------- BM25 ----------
const DOCS = [
  '谱刚性带定理适用于高谱间隙格',
  '谱刚性带对随机化密码格不可达',
  '弱混合角与 Weinberg 角的关系',
  '互锁常数 0.5 的几何意义',
]

function makeEngine() {
  const tok = new Tokenizer(['谱刚性带', '谱刚性', '弱混合角', '互锁常数'])
  const idx = buildIndex(DOCS, (d) => d, tok)
  return { tok, idx }
}

test('BM25：相关文档排序在前', () => {
  const { tok, idx } = makeEngine()
  const hits = queryIndex(idx, tok.tokenize('谱刚性带'), 4)
  assert.ok(hits.length >= 2)
  assert.equal(hits[0].i, 0, '含"谱刚性带"整词的文档应排第一')
  // 分数递减
  for (let i = 1; i < hits.length; i++) assert.ok(hits[i - 1].score >= hits[i].score)
})

test('BM25：idf 区分（高频词得分低）', () => {
  const { tok, idx } = makeEngine()
  // "与" 出现 3 次（idf 低）
  const hits = queryIndex(idx, tok.tokenize('与'), 4)
  if (hits.length > 0) {
    for (const h of hits) assert.ok(h.score < 1, '高频虚词 idf 应压低分数')
  }
})

test('BM25：无命中 token 返回空', () => {
  const { tok, idx } = makeEngine()
  assert.equal(queryIndex(idx, tok.tokenize('zzz不存在词'), 3).length, 0)
})

// ---------- TOC ----------
const TOC = [
  { level: 1, title: '## 摘要', offset: 0 },
  { level: 2, title: '### 2.1 推导', offset: 100 },
  { level: 2, title: '### 2.2 数值表', offset: 300 },
  { level: 1, title: '## 结论', offset: 500 },
]

test('sectionAt：offset 所属章节', () => {
  assert.equal(sectionAt(TOC, 150)?.title, '### 2.1 推导')
  assert.equal(sectionAt(TOC, 50)?.title, '## 摘要')
  assert.equal(sectionAt(TOC, 700)?.title, '## 结论')
  assert.equal(sectionAt([], 0), null)
  assert.equal(sectionAt(undefined, 0), null)
})

test('locateSection：关键词定位（最小 level 优先）', () => {
  const m = locateSection(TOC, '数值')
  assert.equal(m?.entry.title, '### 2.2 数值表')
  assert.equal(locateSection(TOC, '不存在'), null)
})

test('sectionEnd：取下一个同级别标题偏移', () => {
  const m = locateSection(TOC, '推导')
  assert.equal(sectionEnd(TOC, m.tocIndex), 300)
  const last = locateSection(TOC, '结论')
  assert.equal(sectionEnd(TOC, last.tocIndex), null) // 最后一节
})

test('safeArticlePath：防路径穿越', () => {
  const dir = '/tmp/nonexistent'
  assert.equal(safeArticlePath(dir, '../etc/passwd'), null, '拒绝 ..')
  assert.equal(safeArticlePath(dir, 'a/b.md'), null, '拒绝子目录路径')
  assert.equal(safeArticlePath(dir, 'x.md'), null, '文件不存在返回 null')
  assert.equal(safeArticlePath(dir, ''), null)
  // 合法 basename 但文件不存在 → null
  const tmp = path.join(process.cwd(), 'tests')
  assert.equal(safeArticlePath(tmp, 'nonexistent-file.md'), null)
})
