import os, json, plistlib

OPEN_WEBUI_DIR = "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/open_webui"

changes = []

# 1. site.webmanifest
manifest_path = os.path.join(OPEN_WEBUI_DIR, "static", "site.webmanifest")
if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        data = json.load(f)
    data["name"] = "Geometry AI"
    data["short_name"] = "Geometry AI"
    with open(manifest_path, "w") as f:
        json.dump(data, f, indent=2)
    changes.append(f"site.webmanifest: name -> Geometry AI")

# 2. Chrome App Info.plist
chrome_app_plist = "/Users/oygb/Applications/Chrome Apps.localized/Open WebUI.app/Contents/Info.plist"
if os.path.exists(chrome_app_plist):
    with open(chrome_app_plist, "rb") as f:
        plist = plistlib.load(f)
    old_name = plist.get("CFBundleName", "")
    old_shortcut = plist.get("CrAppModeShortcutName", "")
    plist["CFBundleName"] = "Geometry AI"
    plist["CrAppModeShortcutName"] = "Geometry AI"
    with open(chrome_app_plist, "wb") as f:
        plistlib.dump(plist, f)
    changes.append(f"Info.plist: CFBundleName '{old_name}' -> 'Geometry AI'")
    changes.append(f"Info.plist: CrAppModeShortcutName '{old_shortcut}' -> 'Geometry AI'")
    
    # 也要把整个 .app 文件夹重命名
    app_dir = os.path.dirname(os.path.dirname(chrome_app_plist))
    parent_dir = os.path.dirname(app_dir)
    new_app_path = os.path.join(parent_dir, "Geometry AI.app")
    if not os.path.exists(new_app_path) and os.path.exists(app_dir):
        os.rename(app_dir, new_app_path)
        changes.append(f"重命名 .app: 'Open WebUI.app' -> 'Geometry AI.app'")
else:
    changes.append(f"⚠️ Chrome App 不存在: {chrome_app_plist}")

# 3. env.py 里 WEBUI_FAVICON_URL 也改掉
env_path = os.path.join(OPEN_WEBUI_DIR, "env.py")
with open(env_path, "r") as f:
    content = f.read()
if "https://openwebui.com/favicon.png" in content:
    content = content.replace(
        'WEBUI_FAVICON_URL = "https://openwebui.com/favicon.png"',
        'WEBUI_FAVICON_URL = "/static/favicon.png"'
    )
    with open(env_path, "w") as f:
        f.write(content)
    changes.append("env.py: WEBUI_FAVICON_URL 改为本地路径")

for c in changes:
    print(f"✅ {c}")
print(f"\n✅ 共 {len(changes)} 项修改完成")
print(f"⚠️ 重要提示：")
print(f"   1. 需要重启 Open WebUI")
print(f"   2. Chrome App 已重命名为 'Geometry AI.app'")
print(f"   3. 如果 Dock 上还有旧图标，需要重新从应用程序文件夹打开 Geometry AI.app")
