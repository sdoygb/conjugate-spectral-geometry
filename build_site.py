#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共扼谱几何 GitHub Pages 站点生成器
- 从 app/articles/*.md 生成 gh-pages/cn/*.html（全文，MathJax 支持）
- 生成 gh-pages/cn/index.html（按卷分组的文章列表）
- 生成 gh-pages/sitemap.xml（首页 + cn 全部 + en 现有全部）
用法: python3 build_site.py
"""
import os
import re
import glob
import html as html_mod

BASE = "https://sdoygb.github.io/conjugate-spectral-geometry"
ARTICLES_DIR = "app/articles"
OUT_DIR = "gh-pages/cn"
EN_DIR = "gh-pages/en"
SITEMAP = "gh-pages/sitemap.xml"

MATHJAX_HEAD = """<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    packages: {'[+]': ['amsmath', 'amssymb', 'noerrors', 'mhchem']}
  },
  options: {
    skipHtmlTypes: 'script|style|noscript',
    renderActions: {
      addMenu: [0, '', '']
    }
  },
  loader: {
    load: ['[tex]/amsmath', '[tex]/amssymb', '[tex]/noerrors', '[tex]/mhchem']
  },
  chtml: {
    displayAlign: 'center',
    scale: 1.05
  }
};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" id="MathJax-script"></script>"""


def natural_key(name):
    """自然排序：0.1, 0.2, ..., 0.10, 1.1..."""
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', name)]


def protect_math(text):
    """保护 $...$ 和 $$...$$ 公式，防止 markdown 破坏 LaTeX"""
    placeholders = {}
    counter = [0]

    def _protect(m):
        counter[0] += 1
        key = f"\x00MATH{counter[0]}\x00"
        placeholders[key] = m.group(0)
        return key

    # 先保护 $$...$$，再保护 $...$（非贪婪，避免跨行）
    text = re.sub(r'\$\$.*?\$\$', _protect, text, flags=re.S)
    text = re.sub(r'(?<!\$)\$(?!\$)(?:[^$\n]|\n(?!\n))+?\$(?!\$)', _protect, text)
    return text, placeholders


def restore_math(text, placeholders):
    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text


def render_md(md_text):
    import markdown
    md_text, placeholders = protect_math(md_text)
    body = markdown.markdown(
        md_text,
        extensions=['extra', 'sane_lists', 'fenced_code', 'tables', 'nl2br'],
    )
    body = restore_math(body, placeholders)
    return body


def extract_title(md_text, filename):
    """从 md 第一个 # 提取标题"""
    m = re.search(r'^#\s+(.+?)\s*$', md_text, re.M)
    if m:
        return m.group(1).strip()
    # fallback: 文件名去掉编号和日期
    base = os.path.splitext(filename)[0]
    base = re.sub(r'^(?:[\d.]+_|BZ-?[\d.]+_|[A-Z]+-[\d.]+_)', '', base)
    base = re.sub(r'_(?:CN|EN)_\d+$', '', base)
    return base


def extract_version(md_text):
    m = re.search(r'(?:版本|Version)[:：]\s*([\w.]+)', md_text)
    return m.group(1) if m else ''


def article_url(fname):
    return f"{BASE}/cn/{fname}"


def gen_article_html(fname, md_text):
    title = extract_title(md_text, fname)
    version = extract_version(md_text)
    body = render_md(md_text)
    desc = f"版本: {version}" if version else title
    canon = article_url(fname)
    esc_title = html_mod.escape(title)
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc_title} | 共扼谱几何 | Conjugate Spectral Geometry</title>
<meta name="description" content="{html_mod.escape(desc)}">
<meta name="generator" content="GeometryAI Build Script">

{MATHJAX_HEAD}

<link rel="stylesheet" href="../assets/style.css">
<link rel="canonical" href="{canon}">
</head>
<body>
<div class="page-container">
  <nav class="top-nav">
    <a href="../index.html" class="nav-home">🏠 首页</a>
    <a href="../cn/index.html" class="nav-cn">🇨🇳 中文</a>
    <a href="../en/index.html" class="nav-en">🇬🇧 English</a>
    <span class="nav-title">{esc_title}</span>
  </nav>
  <main class="article-content">
{body}
  </main>
</div>
</body>
</html>"""


def volume_of(fname):
    """从文件名提取卷号（整数部分）"""
    m = re.match(r'^(\d+)', fname)
    if not m:
        return '其他'
    return m.group(1)


def gen_index_html(articles):
    """articles: list of (fname, title) 已排序"""
    from collections import OrderedDict
    vols = OrderedDict()
    for fname, title in articles:
        vol = volume_of(fname)
        vols.setdefault(vol, []).append((fname, title))

    lis = []
    for vol, items in vols.items():
        lis.append(f'<h2>第{vol}卷</h2>')
        lis.append('<ul class="article-list">')
        for fname, title in items:
            num = os.path.splitext(fname)[0].split('_')[0]
            lis.append(f'<li><a href="{fname}">{num}. {html_mod.escape(title)}</a></li>')
        lis.append('</ul>')

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中文文章索引 | 共扼谱几何 | Conjugate Spectral Geometry</title>
<meta name="description" content="共扼谱几何论文全集 — 中文版，全部开放获取">
<link rel="stylesheet" href="../assets/style.css">
<link rel="canonical" href="{BASE}/cn/index.html">
</head>
<body>
<div class="page-container">
  <nav class="top-nav">
    <a href="../index.html" class="nav-home">🏠 首页</a>
    <a href="../cn/index.html" class="nav-cn">🇨🇳 中文</a>
    <a href="../en/index.html" class="nav-en">🇬🇧 English</a>
    <span class="nav-title">中文文章索引</span>
  </nav>
  <main>
    <h1>🇨🇳 中文文章索引</h1>
    <p>共扼谱几何论文全集 — 中文版（{len(articles)} 篇，全部开放获取）</p>

{chr(10).join(lis)}
  </main>
</div>
</body>
</html>"""


def gen_sitemap(cn_articles, en_htmls):
    """生成 sitemap.xml"""
    urls = []
    # 首页
    urls.append(("", "2026-08-12", "1.0", "daily"))
    urls.append(("index.html", "2026-08-12", "1.0", "daily"))
    urls.append(("cn/index.html", "2026-08-12", "0.9", "weekly"))
    urls.append(("en/index.html", "2026-08-12", "0.9", "weekly"))

    for fname in cn_articles:
        date = "2026-08-12"
        m = re.search(r'_(\d{6})\.md$', fname)
        if m:
            d = m.group(1)
            date = f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
        urls.append((f"cn/{fname.replace('.md', '.html')}", date, "0.7", "monthly"))

    for ef in sorted(en_htmls):
        date = "2026-08-02"
        m = re.search(r'_(\d{6})\.html$', ef)
        if m:
            d = m.group(1)
            date = f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
        urls.append((f"en/{ef}", date, "0.7", "monthly"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, date, prio, freq in urls:
        loc = f"{BASE}/{path}" if path else f"{BASE}/"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{date}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{prio}</priority>")
        lines.append("  </url>")
    lines.append('</urlset>')
    return "\n".join(lines)


def is_paper(fname):
    """过滤非论文文件（MOC 目录、投稿信、投稿稿、对照表）"""
    if fname.startswith(('MOC_', 'Cover_', 'QEC_Paper_', 'zenodo_', '00_')):
        return False
    if '对照表' in fname or 'Cover' in fname:
        return False
    return True


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.md")), key=natural_key)
    md_files = [f for f in all_files if is_paper(os.path.basename(f))]
    print(f"文章库: {len(all_files)} 篇，过滤非论文后: {len(md_files)} 篇")

    articles = []  # (fname, title)
    for mdf in md_files:
        fname = os.path.basename(mdf).replace('.md', '.html')
        with open(mdf, encoding='utf-8') as f:
            md_text = f.read()
        title = extract_title(md_text, fname)
        articles.append((fname, title))
        out_path = os.path.join(OUT_DIR, fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(gen_article_html(fname, md_text))
        print(f"  ✓ {fname}")

    # 清理不在文章库中的旧 HTML
    keep = {a[0] for a in articles}
    removed = 0
    for old in glob.glob(os.path.join(OUT_DIR, "*.html")):
        base = os.path.basename(old)
        if base != 'index.html' and base not in keep:
            os.remove(old)
            removed += 1
    print(f"清理旧文件: {removed} 个")

    # 列表页
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(gen_index_html(articles))
    print(f"✓ cn/index.html（{len(articles)} 篇）")

    # en 现有 HTML
    en_htmls = []
    for ef in glob.glob(os.path.join(EN_DIR, "*/*.html")):
        en_htmls.append(os.path.relpath(ef, EN_DIR))
    print(f"en 文章: {len(en_htmls)} 个")

    # sitemap
    with open(SITEMAP, 'w', encoding='utf-8') as f:
        f.write(gen_sitemap([a[0] for a in articles], en_htmls))
    print(f"✓ sitemap.xml（{4 + len(articles) + len(en_htmls)} URL）")


if __name__ == '__main__':
    main()
