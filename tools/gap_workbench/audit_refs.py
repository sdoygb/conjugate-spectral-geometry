#!/usr/bin/env python3
"""全库归因审计 v2（A 层·结构级）：提取所有跨文章引用，核对引用目标存在性。

v2 修复：
  1. CROSS_RE 前视排除 §：§3.3§8.3 视为两个自引用连写（3.12 模式），不再误判跨文章
  2. 定理类：优先判本文自引用（当前文章含该编号 → ✅），再判跨文章
  3. 排除 00_总索引 的自引用判定（导航文件）
  4. 输出无小数点编号引用提示（如"22 §8"，10.12 表格模式，待人工）

用法：python3 tools/gap_workbench/audit_refs.py [--top 80]
"""
import os
import re
import sys
from collections import Counter

ART_DIR = "app/articles"

HEAD_RE = re.compile(r"^#{1,4}\s+(.*)$")
SEC_RE = re.compile(r"§?\s*(\d+(?:\.\d+)*)")
CROSS_RE = re.compile(r"(?<![\d.§])(\d+\.\d+)\s*§\s*(\d+(?:\.\d+)*)")
SELF_RE = re.compile(r"§\s*(\d+(?:\.\d+)*)")
THM_RE = re.compile(r"(定理|构造|定义|推论|命题|引理|公理)\s*(\d+\.\d+(?:\.\d+)*)")
ATTRIB_RE = re.compile(r"(来自|见|源于|据|引用|出处|来源|前置|已证|依据|按照|采用|即|对应)\s*[（(]?\s*(\d+\.\d+)\s*§\s*(\d+(?:\.\d+)*)")
NODOT_RE = re.compile(r"(?<![\d.§])(\d{1,2})\s+§\s*(\d+(?:\.\d+)*)")


def article_files(d):
    return sorted(f for f in os.listdir(d) if f.endswith(".md"))


def parse_sections(text):
    secs = set()
    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if not m:
            continue
        for sm in SEC_RE.finditer(m.group(1)):
            secs.add(sm.group(1))
    return secs


def parse_thm_numbers(text):
    nums = set()
    for m in THM_RE.finditer(text):
        nums.add(m.group(2))
    return nums


def main():
    top = 80
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    d = ART_DIR
    files = article_files(d)
    art_map = {}
    for f in files:
        aid = f.split("_", 1)[0]
        art_map.setdefault(aid, []).append(f)

    secs_map, thms_map, text_map = {}, {}, {}
    for aid, fl in art_map.items():
        for f in fl:
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                txt = fh.read()
            text_map[f] = txt
            secs_map.setdefault(aid, set()).update(parse_sections(txt))
            thms_map.setdefault(aid, set()).update(parse_thm_numbers(txt))

    cross_ok, cross_bad = [], []
    self_ok, self_bad = [], []
    thm_ok, thm_bad, thm_amb = [], [], []
    attr_hits = []
    nodot_hits = []

    for f in files:
        txt = text_map[f]
        aid_self = f.split("_", 1)[0]
        if aid_self.startswith("00"):
            continue  # 总索引/导航文件跳过自引用判定
        for ln, line in enumerate(txt.splitlines(), 1):
            for m in CROSS_RE.finditer(line):
                ref = m.group(0)
                aid, sec = m.group(1), m.group(2)
                if aid not in art_map:
                    cross_bad.append((f, ln, ref, aid, sec, "文章不存在"))
                    continue
                if sec in secs_map.get(aid, set()):
                    cross_ok.append((f, ln, ref, aid, sec, ""))
                else:
                    cross_bad.append((f, ln, ref, aid, sec, "章节不存在"))
            rest = CROSS_RE.sub("", line)
            for m in SELF_RE.finditer(rest):
                sec = m.group(1)
                ref = "§" + sec
                if sec in secs_map.get(aid_self, set()):
                    self_ok.append((f, ln, ref, aid_self, sec, ""))
                else:
                    self_bad.append((f, ln, ref, aid_self, sec, "本文件章节不存在"))
            for m in THM_RE.finditer(line):
                kind, num = m.group(1), m.group(2)
                ref = f"{kind} {num}"
                if num in thms_map.get(aid_self, set()):
                    thm_ok.append((f, ln, ref, aid_self, num, "本文自引用"))
                    continue
                aid = num.split(".")[0] + "." + num.split(".")[1]
                if aid not in art_map:
                    if len(num.split(".")) == 2:
                        thm_amb.append((f, ln, ref, aid, num, "两位编号：目标文章不存在（可能为本文自引用漏检或笔误）"))
                    else:
                        thm_bad.append((f, ln, ref, aid, num, "目标文章不存在"))
                    continue
                if num in thms_map.get(aid, set()):
                    thm_ok.append((f, ln, ref, aid, num, ""))
                else:
                    thm_bad.append((f, ln, ref, aid, num, "目标文章无此编号"))
            for m in ATTRIB_RE.finditer(line):
                attr_hits.append((f, ln, m.group(0), m.group(2), m.group(3)))
            for m in NODOT_RE.finditer(line):
                nodot_hits.append((f, ln, m.group(0), m.group(1), m.group(2)))

    print(f"=== 全库归因审计 v2（A 层·结构级）===")
    print(f"文章数：{len(files)}（00_* 导航文件跳过自引用）")
    print(f"\n[1] 跨文章章节引用 X.Y §N")
    print(f"  总数 {len(cross_ok)+len(cross_bad)}：可核实 {len(cross_ok)}，异常 {len(cross_bad)}")
    cnt = Counter((r[2], r[5]) for r in cross_bad)
    print(f"  异常分布：{dict(cnt.most_common(12))}")
    if cross_bad:
        print(f"  --- 异常清单（前 {top}）---")
        for f, ln, ref, aid, sec, why in cross_bad[:top]:
            print(f"  [{why}] {f}:{ln}: {ref}")

    print(f"\n[2] 自引用 §N（同文件）")
    print(f"  总数 {len(self_ok)+len(self_bad)}：可核实 {len(self_ok)}，异常 {len(self_bad)}")
    cnt = Counter(r[2] for r in self_bad)
    print(f"  异常分布：{dict(cnt.most_common(12))}")
    if self_bad:
        print(f"  --- 异常清单（前 {top}）---")
        for f, ln, ref, aid, sec, why in self_bad[:top]:
            print(f"  [{why}] {f}:{ln}: {ref}")

    print(f"\n[3] 定理类引用（定理/构造/定义/推论/命题/引理/公理）")
    print(f"  总数 {len(thm_ok)+len(thm_bad)+len(thm_amb)}："
          f"可核实 {len(thm_ok)}（含本文自引用），真异常 {len(thm_bad)}，歧义待人工 {len(thm_amb)}")
    cnt = Counter(r[2] for r in thm_bad)
    print(f"  真异常分布：{dict(cnt.most_common(10))}")
    if thm_bad:
        print(f"  --- 真异常清单（前 {top}）---")
        for f, ln, ref, aid, num, why in thm_bad[:top]:
            print(f"  [{why}] {f}:{ln}: {ref}")
    if thm_amb:
        print(f"  --- 歧义待人工（前 40）---")
        for f, ln, ref, aid, num, why in thm_amb[:40]:
            print(f"  [⚠️] {f}:{ln}: {ref}")

    print(f"\n[4] 无小数点编号引用（22 §8 型，待人工：{len(nodot_hits)} 条，前 20）")
    for f, ln, ref, aid, sec in nodot_hits[:20]:
        print(f"  {f}:{ln}: {ref}")

    print(f"\n[5] 归因动词引用（B 层重点候选：{len(attr_hits)} 条，前 {top}）")
    for f, ln, ref, aid, sec in attr_hits[:top]:
        print(f"  {f}:{ln}: {ref}")


if __name__ == "__main__":
    main()
