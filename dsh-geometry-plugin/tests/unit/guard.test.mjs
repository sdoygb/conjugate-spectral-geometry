/**
 * guard.test.mjs — 阅读防护 + LRU 单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  recordRead, resetReadState, sessionCount, VIEW_CHAR_LIMIT, MAX_SESSIONS,
} from '../../dist/core/guard.js'

test('正常读取无提示', () => {
  const sk = `g1-${Math.random()}`
  const r = recordRead(sk, 'a.md', 0, 1000)
  assert.equal(r, '')
  resetReadState(sk)
})

test('顺序翻页检测（连续区间 2000 内）', () => {
  const sk = `g2-${Math.random()}`
  assert.equal(recordRead(sk, 'a.md', 0, 1000), '')
  const r2 = recordRead(sk, 'a.md', 1200, 2500) // 与前段重叠容差内
  assert.ok(r2.includes('顺序翻页'), '连续读取应触发翻页警告')
  resetReadState(sk)
})

test('非连续读取不触发翻页', () => {
  const sk = `g3-${Math.random()}`
  assert.equal(recordRead(sk, 'a.md', 0, 1000), '')
  const r2 = recordRead(sk, 'a.md', 8000, 9000) // 远离前段
  assert.equal(r2, '')
  resetReadState(sk)
})

test('累计超限拦截', () => {
  const sk = `g4-${Math.random()}`
  // 分两次读满超过 VIEW_CHAR_LIMIT
  const half = Math.ceil(VIEW_CHAR_LIMIT / 2) + 1000
  assert.equal(recordRead(sk, 'a.md', 0, half), '')
  const r2 = recordRead(sk, 'a.md', half, half + half)
  assert.ok(r2.includes('超过单篇文章上限'), '累计超限应提示')
  resetReadState(sk)
})

test('不同文章分别计数', () => {
  const sk = `g5-${Math.random()}`
  const half = Math.ceil(VIEW_CHAR_LIMIT / 2) + 1000
  recordRead(sk, 'a.md', 0, half)
  recordRead(sk, 'a.md', half, half + half) // a.md 超限
  const rb = recordRead(sk, 'b.md', 0, half) // b.md 未超限
  assert.equal(rb, '', 'b.md 单独计数不受 a.md 影响')
  resetReadState(sk)
})

test('LRU 淘汰（D2）：超过 MAX_SESSIONS 淘汰最旧', () => {
  // 清场
  for (let i = 0; i < 100; i++) resetReadState(`lru-${i}`)
  // 造 MAX_SESSIONS + 10 个会话
  for (let i = 0; i < MAX_SESSIONS + 10; i++) {
    recordRead(`lru-${i}`, 'a.md', 0, 100)
  }
  assert.ok(sessionCount() <= MAX_SESSIONS, `会话数应 ≤ ${MAX_SESSIONS}，实际 ${sessionCount()}`)
  // 最旧的 lru-0..9 应被淘汰（无翻页提示=已被删除）
  const r = recordRead('lru-0', 'a.md', 0, 100)
  assert.equal(r, '', '被淘汰会话重新访问应视为新会话（无翻页检测残留）')
  // 清理
  for (let i = 0; i < MAX_SESSIONS + 10; i++) resetReadState(`lru-${i}`)
})

test('空输入安全', () => {
  assert.equal(recordRead('', 'a.md', 0, 1), '')
  assert.equal(recordRead('sk', '', 0, 1), '')
})
