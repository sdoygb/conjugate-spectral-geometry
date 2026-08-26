/**
 * latex.test.mjs — LaTeX→Unicode 转换器单元测试（D3）
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { latexToUnicode, hasLatex } from '../../dist/core/latex.js'

test('希腊字母命令', () => {
  assert.equal(latexToUnicode('\\theta_M'), 'θ_M')
  assert.equal(latexToUnicode('\\Lambda_H'), 'Λ_H')
  assert.equal(latexToUnicode('\\alpha^{-1}'), 'α^-1')
})

test('数学符号', () => {
  assert.equal(latexToUnicode('\\leq'), '≤')
  assert.equal(latexToUnicode('\\le'), '≤') // 别名
  assert.equal(latexToUnicode('\\approx'), '≈')
  assert.equal(latexToUnicode('\\in \\mathbb{R}'), '∈ ℝ')
  assert.equal(latexToUnicode('\\cdots'), '⋯')
})

test('frac 含嵌套上标的实参（修复回归）', () => {
  const out = latexToUnicode('\\frac{n \\Lambda_{\\max}^{(n-1)/n} - 1}{\\Lambda_H - 1}')
  assert.equal(out, '(n Λ_max^(n-1)/n - 1)/(Λ_H - 1)')
})

test('普通括号保留（修复回归：DELIMS 不再误删 ()）', () => {
  assert.equal(latexToUnicode('(a+b)^2'), '(a+b)^2')
  assert.equal(latexToUnicode('\\frac{a}{b} + (c)'), '(a)/(b) + (c)')
})

test('分隔符删除', () => {
  assert.equal(latexToUnicode('$x$'), 'x')
  assert.equal(latexToUnicode('\\(x\\)'), 'x')
  assert.equal(latexToUnicode('$$y$$'), 'y')
})

test('函数命令去反斜杠', () => {
  assert.equal(latexToUnicode('\\sin^2\\theta'), 'sin^2θ')
  assert.equal(latexToUnicode('\\max'), 'max')
})

test('未知命令保守保留', () => {
  assert.equal(latexToUnicode('\\unknowncommand{x}'), '\\unknowncommand{x}')
})

test('hasLatex 快速判断', () => {
  assert.ok(hasLatex('$x$'))
  assert.ok(hasLatex('\\theta'))
  assert.ok(!hasLatex('纯文本 123'))
})
