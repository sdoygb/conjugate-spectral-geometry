import os

home = os.path.expanduser("~")
OPEN_WEBUI_DIR = "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/open_webui"

# ===========================
# 1. Fix env.py: remove the (Open WebUI) suffix
# ===========================
env_path = os.path.join(OPEN_WEBUI_DIR, "env.py")
with open(env_path, "r") as f:
    content = f.read()

# The problematic lines:
#   WEBUI_NAME = os.environ.get("WEBUI_NAME", "Open WebUI")
#   if WEBUI_NAME != "Open WebUI":
#       WEBUI_NAME += " (Open WebUI)"

old = '''WEBUI_NAME = os.environ.get("WEBUI_NAME", "Open WebUI")
if WEBUI_NAME != "Open WebUI":
    WEBUI_NAME += " (Open WebUI)"'''

new = '''WEBUI_NAME = os.environ.get("WEBUI_NAME", "Open WebUI")
# Disabled: auto suffix forces (Open WebUI) even when custom name is set
if False:
    WEBUI_NAME += " (Open WebUI)"'''

if old in content:
    content = content.replace(old, new)
    with open(env_path, "w") as f:
        f.write(content)
    print(f"✅ env.py: 已禁用 (Open WebUI) 后缀自动添加")
else:
    print(f"⚠️ env.py: 未找到需要修改的代码，可能已经改过")

# ===========================
# 2. Fix index.html title
# ===========================
index_path = os.path.join(OPEN_WEBUI_DIR, "frontend", "index.html")
if os.path.exists(index_path):
    with open(index_path, "r") as f:
        content = f.read()
    
    if "<title>Open WebUI</title>" in content:
        content = content.replace("<title>Open WebUI</title>", "<title>Geometry AI</title>")
        with open(index_path, "w") as f:
            f.write(content)
        print(f"✅ index.html: 标题已改为 'Geometry AI'")
    elif "<title>Geometry AI</title>" in content:
        print(f"✅ index.html: 已改过，跳过")
    else:
        print(f"⚠️ index.html: 未找到 <title>Open WebUI</title>")
        # Print surrounding context for debugging
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'title' in line.lower() and '<' in line:
                print(f"    Line {i+1}: {line.strip()}")
else:
    print(f"❌ index.html 不存在: {index_path}")

print("\n✅ 品牌标识修改完成！请重启 Open WebUI 生效")
