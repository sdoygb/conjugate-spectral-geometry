import os

MAIN_PATH = "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/open_webui/main.py"

with open(MAIN_PATH, "r") as f:
    content = f.read()

# 在 yield 前插入一行来重写 index.html
old = "    yield"
new = '''    # 强制替换 index.html 标题
    import pathlib
    idx_path = pathlib.Path(FRONTEND_BUILD_DIR) / "index.html"
    if idx_path.exists():
        idx_content = idx_path.read_text(encoding="utf-8")
        idx_path.write_text(idx_content.replace("<title>Open WebUI</title>", "<title>Geometry AI</title>"))
    yield'''

if old in content:
    content = content.replace(old, new)
    with open(MAIN_PATH, "w") as f:
        f.write(content)
    print(f"✅ main.py: 已添加启动时重写标题的钩子")
else:
    print(f"⚠️ main.py: 未找到 '    yield'")

# 验证
with open(MAIN_PATH, "r") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "yield" in line and "#" in line:
        print(f"  Line {i+1}: {line.strip()}")
    if i >= 640 and i <= 660:
        print(f"  {i+1}: {line.rstrip()}")
