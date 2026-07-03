"""
深度修复：替换 Open WebUI 前端静态资源中的所有品牌标识
"""
import os
import glob
import re

OPEN_WEBUI_DIR = "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/open_webui"

# 要替换的字符串对 (old -> new)
REPLACEMENTS = [
    ("Open WebUI", "Geometry AI"),
    ("OpenWebUI", "GeometryAI"),
    ("openwebui.com", "geometry-ai.com"),
    ("open-webui", "geometry-ai"),
]

count = 0

# 扫描所有前端文件
patterns = [
    os.path.join(OPEN_WEBUI_DIR, "frontend", "**", "*.js"),
    os.path.join(OPEN_WEBUI_DIR, "frontend", "**", "*.html"),
    os.path.join(OPEN_WEBUI_DIR, "frontend", "**", "*.css"),
    os.path.join(OPEN_WEBUI_DIR, "frontend", "**", "*.json"),
    os.path.join(OPEN_WEBUI_DIR, "static", "**", "*.js"),
    os.path.join(OPEN_WEBUI_DIR, "static", "**", "*.html"),
    os.path.join(OPEN_WEBUI_DIR, "static", "**", "*.css"),
    os.path.join(OPEN_WEBUI_DIR, "static", "**", "*.json"),
    os.path.join(OPEN_WEBUI_DIR, "**", "*.py"),  # Python 源码也扫
]

# 排除二进制和地图文件
exclude_patterns = ["*.map", "*.pyc", "__pycache__", "*.png", "*.ico", "*.svg"]

def should_exclude(filepath):
    for pat in exclude_patterns:
        if "*" in pat:
            # 简单通配
            if filepath.endswith(pat[1:]):
                return True
        elif pat in filepath:
            return True
    return False

for pattern in patterns:
    for filepath in glob.glob(pattern, recursive=True):
        if should_exclude(filepath):
            continue
        if not os.path.isfile(filepath):
            continue
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        
        original = content
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)
        
        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
            print(f"  ✅ {filepath}")

print(f"\n✅ 共修改 {count} 个文件")
print(f"✅ 请重启 Open WebUI 并清空浏览器缓存后查看")
