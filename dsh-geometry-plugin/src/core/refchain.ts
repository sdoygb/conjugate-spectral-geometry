/**
 * refchain.ts — 真理 → 文章引用链（C1）。
 *
 * truth.jsonl 本身不含文章出处；本模块在加载后**懒构建**"文章编号 → 出处"
 * 映射：扫描全部文章分块，正则提取 "命题/定理/引理/… X.Y.Z.W" 形式的编号，
 * 记录其所在文章与章节。geo_truth 命中后按 formula_name 中的编号反查，
 * 输出"出处：文章 §章节"，让 #N 能直接跳转到来源文章。
 *
 * 零运行时依赖，纯增量（不动导出流程与数据文件）。
 */
import type { ArticleChunk, LoadedIndex } from './loader.js'
import { sectionAt } from './toc.js'

/** 文章编号模式：命题/定理/引理/推论/定义/公理/性质/注(记) + 形如 0.2.1.02 的编号 */
const REF_RE = /(命题|定理|引理|推论|定义|公理|性质|注记?)[ ]?(\d+\.\d+(?:\.\d+)*)/g
/** 从文本中提取"文章编号"（纯编号形式，如 0.2.1.02） */
const NUM_ONLY_RE = /\d+\.\d+(?:\.\d+)*/g
/** 行首定义：行以"命题/定理/… X.Y.Z"开头（含 markdown 列表/加粗符号）；全局版供 matchAll */
const LINE_HEAD_RE = /^[#>*\-\s]*(命题|定理|引理|推论|定义|公理|性质|注记?)[ ]?(\d+\.\d+(?:\.\d+)*)/gm

/** 定义处优先级：章节标题 > 行首定义 > 正文引用（0/1/2） */
const ORIGIN_PRIORITY = { heading: 0, lineHead: 1, body: 2 } as const

export interface ArticleRef {
  /** 文章编号，如 "0.2.1.02" */
  number: string
  /** 出处文章 fname */
  fname: string
  /** 出处章节标题（无则空） */
  section: string
  /** 出处质量：heading=定义在章节标题 / lineHead=行首定义 / body=正文引用 */
  kind: keyof typeof ORIGIN_PRIORITY
}

export interface RefChain {
  /** 按文章编号查出处（无则 undefined） */
  lookup(number: string): ArticleRef | undefined
  /** 条目总数（诊断用） */
  size: number
}

export function buildRefChain(index: LoadedIndex): RefChain {
  const map = new Map<string, ArticleRef>()

  /** 记录一个候选：更高优先级（更小的 kind 值）才替换 */
  function consider(number: string, fname: string, section: string, kind: keyof typeof ORIGIN_PRIORITY): void {
    const cur = map.get(number)
    if (cur && ORIGIN_PRIORITY[cur.kind] <= ORIGIN_PRIORITY[kind]) return
    map.set(number, { number, fname, section, kind })
  }

  // 1) 章节标题（最高优先级：定理以独立标题出现时即定义处）
  for (const [fname, toc] of Object.entries(index.toc)) {
    for (const e of toc) {
      for (const m of e.title.matchAll(NUM_ONLY_RE)) {
        consider(m[0], fname, e.title, 'heading')
      }
    }
  }
  // 2) 行首定义（正文中"定理 X.Y.Z"独立成行，遍历全部匹配）
  for (const c of index.chunks) {
    const sec = sectionAt(index.toc[c.fname], c.start ?? 0)
    for (const lm of c.text.matchAll(LINE_HEAD_RE)) {
      consider(lm[2], c.fname, sec?.title ?? '', 'lineHead')
    }
  }
  // 3) 正文引用（兜底）
  for (const c of index.chunks) {
    const sec = sectionAt(index.toc[c.fname], c.start ?? 0)
    for (const m of c.text.matchAll(REF_RE)) {
      consider(m[2], c.fname, sec?.title ?? '', 'body')
    }
  }
  return {
    lookup(number: string): ArticleRef | undefined {
      return map.get(number)
    },
    size: map.size,
  }
}

/** 从真理记录的 formula_name/text 中提取首个文章编号 */
export function extractArticleNumber(formulaName: string | undefined, text: string | undefined): string | undefined {
  const src = `${formulaName ?? ''} ${text ?? ''}`
  const m = src.match(NUM_ONLY_RE)
  return m ? m[0] : undefined
}
