# -*- coding: utf-8 -*-
"""
md_to_zhihu.py — 把 app/articles 下的 Markdown 文章转换为知乎兼容 HTML。
公式渲染双后端：
  A. katex  (默认): 本地 KaTeX + Playwright 截图，支持完整 LaTeX
  B. matplotlib:     matplotlib mathtext 渲染，支持常见公式子集（备用）

用法:
  python3 zhihu_tools/md_to_zhihu.py app/articles/0.1_零之动与区分_CN_260808.md [--renderer katex|matplotlib] [--out zhihu_tools/out/]

输出:
  out/<文章名>_zhihu.html   （公式为 base64 PNG 内嵌，可直接粘贴进知乎编辑器）
"""
import argparse
import base64
import io
import os
import re
import sys

try:
    import markdown as md_lib
except ImportError:
    sys.exit("缺少 markdown 库: python3 -m pip install markdown")

# ---------------------------------------------------------------- 公式提取
BLOCK_RE = re.compile(r"\$\$(.+?)\$\$", re.S)   # $$...$$ 块级公式
INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.S)  # $...$ 行内公式

class FormulaExtractor:
    """把 md 文本中的公式替换为占位符，返回 (文本, 公式列表)"""
    def __init__(self):
        self.formulas = []
        self._n = 0

    def _placeholder(self, tex, block):
        self.formulas.append((tex.strip(), block))
        ph = f"__ZH_FORMULA_{self._n}__"
        self._n += 1
        return ph

    def extract(self, text):
        # 先块级，再行内（块级占位符避免被行内正则误匹配）
        text = BLOCK_RE.sub(lambda m: self._placeholder(m.group(1), True), text)
        text = INLINE_RE.sub(lambda m: self._placeholder(m.group(1), False), text)
        return text, self.formulas


# ---------------------------------------------------------------- 渲染后端
class MatplotlibRenderer:
    """matplotlib mathtext 渲染（备用，支持常见公式子集）"""
    def __init__(self, dpi=200, fontsize=16):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt = plt
        self.dpi = dpi
        self.fontsize = fontsize

    def render(self, tex, block):
        fig = self.plt.figure()
        try:
            t = fig.text(0, 0, f"${tex}$", fontsize=self.fontsize)
            fig.canvas.draw()
            bbox = t.get_window_extent()
            w, h = bbox.width, bbox.height
            self.plt.close(fig)
            fig = self.plt.figure(figsize=(w / self.dpi, h / self.dpi), dpi=self.dpi)
            fig.text(0.5, 0.5, f"${tex}$", fontsize=self.fontsize,
                     ha="center", va="center")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=self.dpi,
                        transparent=False, bbox_inches="tight", pad_inches=0.05)
            self.plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            self.plt.close(fig)
            print(f"  [matplotlib 渲染失败] {tex[:60]}: {e}")
            return None


class KatexRenderer:
    """KaTeX + Playwright 截图渲染（默认，支持完整 LaTeX）"""
    def __init__(self, katex_dir="zhihu_tools/katex"):
        from playwright.sync_api import sync_playwright
        self.katex_dir = os.path.abspath(katex_dir)
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch()
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        # 渲染用空白页 + KaTeX
        katex_css = f"file://{self.katex_dir}/katex.min.css"
        self.page.set_content(f"""
        <!DOCTYPE html><html><head>
        <link rel="stylesheet" href="{katex_css}">
        <script src="file://{self.katex_dir}/katex.min.js"></script>
        </head><body><div id="out"></div></body></html>""")

    def render(self, tex, block):
        try:
            mode = "display" if block else "inline"
            self.page.evaluate(
                """(tex, mode) => {
                    const el = document.createElement('div');
                    el.style.position = 'absolute';
                    el.style.left = '-9999px';
                    document.getElementById('out').appendChild(el);
                    katex.render(tex, el, {displayMode: mode === 'display', throwOnError: false});
                    return el;
                }""", tex, mode)
            el = self.page.locator("#out div:last-child")
            el.wait_for(state="attached")
            b64 = el.screenshot()
            return base64.b64encode(b64).decode()
        except Exception as e:
            print(f"  [katex 渲染失败] {tex[:60]}: {e}")
            return None

    def close(self):
        try:
            self.browser.close()
            self.pw.stop()
        except Exception:
            pass


# ---------------------------------------------------------------- 主流程
def convert(md_path, renderer, out_dir):
    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    # 1. 提取公式
    ext = FormulaExtractor()
    text, formulas = ext.extract(text)

    # 2. md → HTML
    html = md_lib.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])
    # 代码块里不应该有公式占位符，但保险起见把代码块内容保护：实际上公式先于 md 转换被提取，
    # 代码块中的 $...$ 也会被提取——可接受的简化（数学文章代码块少）。

    # 3. 公式占位符 → <img>
    img_tags = []
    for i, (tex, block) in enumerate(formulas):
        b64 = renderer.render(tex, block)
        if b64:
            img_tags.append((f"__ZH_FORMULA_{i}__",
                             f'<img src="data:image/png;base64,{b64}" '
                             f'style="max-width:100%;{"display:block;margin:8px auto;" if block else ""}">'))
        else:
            img_tags.append((f"__ZH_FORMULA_{i}__",
                             f'<span style="color:#888;">[公式渲染失败: {tex[:40]}]</span>'))
    for ph, tag in img_tags:
        html = html.replace(ph, tag)

    # 4. 输出
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(md_path))[0]
    out_path = os.path.join(out_dir, f"{base}_zhihu.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 转换完成: {out_path}")
    print(f"   公式数: {len(formulas)} | 渲染失败: {sum(1 for t,_ in img_tags if '渲染失败' in t)}")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", help="Markdown 文章路径")
    ap.add_argument("--renderer", choices=["katex", "matplotlib"], default="katex")
    ap.add_argument("--out", default="zhihu_tools/out")
    args = ap.parse_args()

    if args.renderer == "katex":
        r = KatexRenderer()
    else:
        r = MatplotlibRenderer()
    try:
        convert(args.md, r, args.out)
    finally:
        if args.renderer == "katex":
            r.close()


if __name__ == "__main__":
    main()
