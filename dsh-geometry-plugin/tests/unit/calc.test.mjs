/**
 * calc.test.mjs — 数学求值器单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calcResult, getNs, evaluate, formatNum } from '../../dist/core/calc.js'

function calc(expr, ns) {
  return calcResult(expr, ns ?? getNs(`test-${Math.random()}`)).text
}

test('四则与幂', () => {
  assert.match(calc('2+3*4'), /数值结果: 14/)
  assert.match(calc('2**10'), /数值结果: 1024/)
  assert.match(calc('10 % 3'), /数值结果: 1/)
  assert.match(calc('(2+3)*4'), /数值结果: 20/)
})

test('三角与角度', () => {
  assert.match(calc('sin(pi/2)'), /数值结果: 1/)
  assert.match(calc('sin(30*pi/180)'), /数值结果: 0\.5/)
  assert.match(calc('rad(180)'), /数值结果: 3\.141592654/)
  assert.match(calc('deg(pi)'), /数值结果: 180/)
})

test('初等函数（C3）：阶乘/组合/最大公约数', () => {
  assert.match(calc('factorial(5)'), /数值结果: 120/)
  assert.match(calc('5!'), /数值结果: 120/) // 后缀阶乘
  assert.match(calc('binom(52,5)'), /数值结果: 2598960/)
  assert.match(calc('gcd(1071,462)'), /数值结果: 21/)
  assert.match(calc('lcm(12,18)'), /数值结果: 36/)
  assert.match(calc('hypot(3,4)'), /数值结果: 5/)
  assert.match(calc('sign(-7)'), /数值结果: -1/)
})

test('多行赋值 + 中间变量回显（C3）', () => {
  const ns = getNs(`echo-${Math.random()}`)
  const r = calcResult('a=5; b=factorial(a); c=binom(10,3); gcd(84,36)', ns)
  assert.match(r.text, /中间变量: a = 5; b = 120; c = 120/)
  assert.match(r.text, /数值结果: 12/)
  // 跨调用保留
  const r2 = calcResult('a*2', ns)
  assert.match(r2.text, /数值结果: 10/)
})

test('错误处理', () => {
  assert.match(calc('1/0'), /除以零/)
  assert.match(calc('process.exit(1)'), /未知符号: process/)
  assert.match(calc('unknown_fn(1)'), /未知函数/)
  assert.match(calc('a'), /未知符号: a/) // 新会话中 a 未定义
})

test('分数/高精度展示', () => {
  assert.equal(formatNum(1 / 3), '0.3333333333')
  assert.equal(formatNum(42), '42')
  assert.equal(formatNum(Infinity), 'Infinity')
})

test('符号解析安全检查（无 eval 注入）', () => {
  // 字符串字面量/对象访问不应可执行
  assert.match(calc('Function("return 1")()'), /无法解析|未知符号|失败/)
  assert.match(calc('this.constructor'), /无法解析|未知符号|失败/)
})
