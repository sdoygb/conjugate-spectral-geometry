#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索质量评估：真实对话问题 → 期望命中文章
用法: python3 eval_retrieval.py [--learned-off] [--tag 名称]
输出: 每问题 Hit@1/@3/@5/@8（articles 源），汇总表
"""
import sys, os, time, json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

from config import CHROMA_DB_DIR, UPLOAD_FOLDER
from knowledge import VectorKnowledgeBase

# ---- 评估集：真实对话历史提取（问题 → 期望命中文章）----
EVAL_SET = [
    {"q": "七层以内没有自由度，观测区域是137.036，这个数确定下来之后七层之内都是固定的",
     "expect": ["8.13", "0.6"], "note": "几何论的偶然性@分层宇宙"},
    {"q": "把分形宇宙这个文章扩展一下吧，先搜一搜其他文章有没有相应的理论",
     "expect": ["8.13", "0.6", "10.21", "10.12"], "note": "几何论的偶然性@扩展8.13"},
    {"q": "根据前面那5个文章定义把它引进来，扩展8.13，引入三层本体论",
     "expect": ["8.13", "10.21", "10.12", "8.11", "0.6"], "note": "几何论的偶然性@三层本体论"},
    {"q": "人界是第几层，我们要把它计算出来",
     "expect": ["8.13", "0.5", "7.12"], "note": "几何论的偶然性@人界定位"},
    {"q": "因果层能分几层，信息层能分几层",
     "expect": ["0.5", "8.13"], "note": "几何论的偶然性@三扇区厚度"},
    {"q": "既然人界是所有界的终点，把因果界跟信息界拆开一层一层，能组合出多少个界",
     "expect": ["8.13", "10.21", "10.12"], "note": "几何论的偶然性@组合空间"},
    {"q": "12个位置全部过筛，哪些是稳定驻点",
     "expect": ["8.13", "10.12", "0.5"], "note": "几何论的偶然性@过筛"},
    {"q": "O3递归复现边界，终止判据",
     "expect": ["8.13", "0.6", "10.12"], "note": "几何论的偶然性@O3"},
    {"q": "O5层界相容性，界的划分在递归下保持稳定",
     "expect": ["8.13", "0.6", "10.12", "10.21"], "note": "几何论的偶然性@O5"},
    {"q": "这些定理之间有没有一个依赖关系交错的网络",
     "expect": ["10.21"], "note": "主库定理查询@依赖图"},
    {"q": "抽查定理编号的定位准不准确，章节定位",
     "expect": [], "na": "期望标注不现实,00_总索引命中合理", "note": "主库定理查询@编号抽查"},
    {"q": "3.10的编号错误还有没有",
     "expect": ["3.10"], "note": "主库定理查询@3.10审核"},
    {"q": "把共扼谱几何推广出去，精细结构常数比较有冲击力",
     "expect": ["1.5", "0.8"], "note": "共扼谱几何推广@FSD(0.9已撤销→1.5/0.8)"},
    {"q": "我们现在有几个选择的点？是选择了还是什么原理让它分支了",
     "expect": [], "na": "0.10已归档,4.5弱关联", "note": "共扼谱几何推广@分叉口"},
    {"q": "回过头来看看0卷那里比较基础，有哪些地方不合理",
     "expect": ["0.1", "MOC_0"], "note": "共扼谱几何推广@0.1审视"},
    {"q": "那个27分之1我们要把它搞定，不能够猜想",
     "expect": [], "na": "0.9已撤销,B1概念无承载文章", "note": "共扼谱几何推广@B1=1/27"},
    {"q": "137.035999102这个数是不是更接近另一个精细结构常数标准",
     "expect": ["1.5"], "note": "共扼谱几何推广@CODATA对比(0.9已撤销→1.5)"},
    {"q": "S_e锁定的证明过程",
     "expect": ["10.14", "0.8"], "note": "今日问题@S_e锁定"},
    {'q': '引力和其他三种力到底怎么统一的，有没有一个统一的理论', 'expect': ['8.1'], 'note': '物理学新进展@引力统一'},
    {'q': '黑洞把信息吞进去之后，信息还会不会丢', 'expect': ['8.4'], 'note': '物理学新进展@黑洞信息'},
    {'q': '星系转那么快为什么不散掉，是暗物质在起作用吗', 'expect': ['8.2', '8.18'], 'note': 'Three Cosmic Fields@旋转曲线'},
    {'q': '中微子是不是自己的反粒子，质量到底怎么来的', 'expect': ['7.8'], 'note': '标准模型@中微子'},
    {'q': '质子自旋从哪来，夸克贡献不够吧', 'expect': ['7.13'], 'note': '标准模型@质子自旋'},
    {'q': '强相互作用为什么没有破坏CP对称', 'expect': ['7.10'], 'note': '标准模型@强CP'},
    {'q': '为什么观测不到单独的夸克', 'expect': ['7.9'], 'note': '标准模型@夸克禁闭'},
    {'q': '磁单极子到底存不存在，为什么一直找不到', 'expect': ['9.5'], 'note': '预言检验@磁单极子'},
    {'q': '质子会不会衰变，寿命有多长', 'expect': ['9.3'], 'note': '预言检验@质子衰变'},
    {'q': '高温超导的机理几何理论怎么解释', 'expect': ['9.1'], 'note': '预言检验@超导'},
    {'q': '缪子反常磁矩那个实验偏差，几何论怎么解释', 'expect': ['9.6'], 'note': '预言检验@g-2'},
    {'q': '水星近日点进动那43角秒是怎么来的', 'expect': ['8.8'], 'note': '引力与宇宙学@水星进动'},
    {'q': '银河系的结构是怎么形成的', 'expect': ['8.11'], 'note': '引力与宇宙学@银河系'},
    {'q': '量子纠缠这个现象在几何框架里怎么理解', 'expect': ['10.13'], 'note': '应用@量子纠缠'},
    {'q': '中医的经络有没有几何上的起源', 'expect': ['10.3'], 'note': '应用@经络'},
    {'q': '碳14测年的结果是不是要修正', 'expect': ['10.14'], 'note': '应用@测年修正'},
    {'q': '杨米尔斯质量间隙的问题证明了吗', 'expect': ['10.17'], 'note': '应用@质量间隙'},
    {'q': '为什么自然界恰好是三代粒子', 'expect': ['7.2'], 'note': '标准模型@三代'},
    {'q': '卡比博角那个混合角的值怎么来的', 'expect': ['7.5'], 'note': '标准模型@弱混合角'},
    {'q': '相对性原理是不是完全成立，有没有例外', 'expect': ['11.13'], 'note': '哲学@相对性原理'},
]

def article_id_of(r):
    return (r.get('metadata') or {}).get('article_id', '')

def match_expect(aid, expect_list):
    if not aid:
        return False
    for exp in expect_list:
        if aid == exp or aid.startswith(exp + '_'):
            return True
    return False

def hit_at(results, expect, k):
    arts = [r for r in results if r.get('source') == 'articles']
    for r in arts[:k]:
        if match_expect(article_id_of(r), expect):
            return True
    return False

def top_articles(results, k):
    arts = [r for r in results if r.get('source') == 'articles']
    return [article_id_of(r) for r in arts[:k]]

def main():
    tag = 'baseline'
    learned_on = True
    args = sys.argv[1:]
    if '--learned-off' in args:
        learned_on = False
        tag = 'learned_off'
    for i, a in enumerate(args):
        if a == '--tag' and i + 1 < len(args):
            tag = args[i + 1]

    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    ok = vkb.initialize()
    print("BM25 initialized:", vkb.bm25_searcher.initialized)
    if not ok:
        print("[FATAL] 初始化失败")
        sys.exit(1)
    print(f"# 配置: {tag} | learned={'ON' if learned_on else 'OFF'} | articles={vkb.articles_count} learned={vkb.learned_count}")

    rows = []
    for item in EVAL_SET:
        q = item['q']
        if not learned_on:
            vkb._learned_count = 0
        else:
            vkb._learned_count = vkb.learned_count  # 恢复真实值
        t0 = time.time()
        try:
            results = vkb.search(q, top_k=12)
        except Exception as e:
            print(f"[ERR] {q[:30]}: {e}")
            continue
        dt = time.time() - t0
        h1 = hit_at(results, item['expect'], 1)
        h3 = hit_at(results, item['expect'], 3)
        h5 = hit_at(results, item['expect'], 5)
        h8 = hit_at(results, item['expect'], 8)
        n_learned = sum(1 for r in results if r.get('source') == 'learned')
        top8 = ','.join(top_articles(results, 8))
        rows.append((item['note'], item['q'][:40], item['expect'], h1, h3, h5, h8, n_learned, top8, dt))
        print(f"[{'H' if h5 else '.'}] {item['note'][:16]:<18} exp={','.join(item['expect']):<22} "
              f"H1={'Y' if h1 else '-'} H3={'Y' if h3 else '-'} H5={'Y' if h5 else '-'} H8={'Y' if h8 else '-'} "
              f"|L={n_learned} | {dt:.2f}s | top8={top8[:70]}")

    n = len(rows)
    if n == 0:
        print("无有效结果")
        return
    for k, idx, name in [(1, 3, 'H1'), (3, 4, 'H3'), (5, 5, 'H5'), (8, 6, 'H8')]:
        cnt = sum(1 for r in rows if r[idx])
        print(f"{name}@{k}: {cnt}/{n} = {cnt / n * 100:.1f}%")

    # 保存明细供对比
    out = f"eval_result_{tag}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump([{"note": r[0], "q": r[1], "expect": r[2], "h1": r[3], "h3": r[4], "h5": r[5], "h8": r[6],
                    "n_learned": r[7], "top8": r[8], "dt": r[9]} for r in rows], f, ensure_ascii=False, indent=1)
    print(f"明细 -> {out}")

if __name__ == '__main__':
    main()
