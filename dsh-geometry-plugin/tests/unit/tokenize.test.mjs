/**
 * tokenize.test.mjs — 分词器单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Tokenizer, greekToLatin } from '../../dist/core/tokenize.js'

// 迷你术语词典
const TERMS = ['谱刚性', '谱刚性带', '谱刚性比', '格密码', '弱混合角', '编码轨道', '互锁常数']

const tok = new Tokenizer(TERMS)

test('词典最长匹配优先（编码轨道 > 码轨道 bigram）', () => {
  const t = tok.tokenize('编码轨道乘子序列')
  assert.ok(t.includes('编码轨道'), '应命中完整词典词')
  assert.ok(!t.some((x) => x === '码轨'), '不应输出被词典词覆盖的 bigram')
})

test('bigram 兜底 + 虚词过滤', () => {
  const t = tok.tokenize('本文给出一个例子')
  assert.ok(!t.includes('本文'), 'STOP_BIGRAM 过滤"本文"')
  assert.ok(!t.includes('给出'), 'STOP_BIGRAM 过滤"给出"')
  // 非虚词 bigram 保留
  assert.ok(t.includes('例子'), 'bigram"例子"应保留')
})

test('"几何" 不被虚词误杀', () => {
  const t = tok.tokenize('几何知道')
  assert.ok(t.includes('几何'), '"几何"是有效 bigram')
})

test('希腊字母别名（B2）：θ_M → theta_m', () => {
  const t = tok.tokenize('θ_M 与 Λ_H')
  assert.ok(t.includes('theta_m'), 'θ_M 应追加 theta_m 别名')
  assert.ok(t.includes('lambda_h'), 'Λ_H 应追加 lambda_h 别名')
  assert.equal(greekToLatin('δ'), 'delta')
  assert.equal(greekToLatin('abc'), 'abc')
})

test('数字 token（文章编号/小数）', () => {
  const t = tok.tokenize('文章 10.8 与数值 137.036')
  assert.ok(t.includes('10.8'))
  assert.ok(t.includes('137.036'))
})

test('单字查询前缀扩展（B1）："谱" 扩展出词典词', () => {
  const q = tok.queryTokenize('谱')
  assert.ok(q.includes('谱刚性带'), '单字"谱"应扩展出词典词"谱刚性带"')
  assert.ok(q.includes('谱刚性比'))
  assert.ok(q.includes('谱刚性'))
})

test('单字查询 unigram 兜底："熵" 保留为单字 token', () => {
  const q = tok.queryTokenize('熵')
  assert.ok(q.includes('熵'), '单字"熵"应作为 unigram 保留（词典无"熵"开头词）')
})

test('查询端与文档端 token 互通', () => {
  // 文档端有"谱刚性带"；查询"谱刚性带"应产生相同 token
  const doc = new Set(tok.tokenize('谱刚性带定理'))
  assert.ok(doc.has('谱刚性带'))
  const q = new Set(tok.queryTokenize('谱刚性带'))
  assert.ok(q.has('谱刚性带'))
})
