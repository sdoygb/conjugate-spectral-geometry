import os

plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.geometryai.webui</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>unset PYTHONHOME PYTHONPATH; exec /usr/local/bin/open-webui serve</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/oygb/Downloads/GeometryAI-Mac-Build</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/oygb/Downloads/GeometryAI-Mac-Build/logs/webui-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/oygb/Downloads/GeometryAI-Mac-Build/logs/webui-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENAI_API_BASE_URLS</key>
        <string>http://localhost:5000/v1</string>
        <key>OPENAI_API_KEYS</key>
        <string>not-needed</string>
        <key>HF_ENDPOINT</key>
        <string>https://hf-mirror.com</string>
        <key>SENTENCE_TRANSFORMERS_HOME</key>
        <string>/Users/oygb/Downloads/GeometryAI-Mac-Build/models_cache</string>
        <key>WEBUI_NAME</key>
        <string>Geometry AI</string>
    </dict>
</dict>
</plist>
'''

home = os.path.expanduser("~")
path = os.path.join(home, "Library/LaunchAgents/com.geometryai.webui.plist")

# 备份
if os.path.exists(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        os.rename(path, bak)
        print(f"备份旧plist: {bak}")

with open(path, "w") as f:
    f.write(plist)

print(f"✅ plist 已写入: {path}")
print(f"✅ 新增环境变量: WEBUI_NAME=Geometry AI")
