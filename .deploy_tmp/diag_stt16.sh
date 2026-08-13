#!/bin/bash
F=$(ls -t /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*.wav 2>/dev/null | head -1)
echo "使用文件: $F"
if [ -z "$F" ]; then
  echo "（无 wav 文件，检查目录）"
  ls -lt /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/ 2>/dev/null | head -8
  exit 0
fi
cat > /tmp/run_transcribe.py << 'PYEOF'
import asyncio, sys, os
async def main():
    from open_webui.routers.audio import transcribe
    result = await transcribe(request=None, file_path=sys.argv[1], metadata=None, user=None)
    print('RESULT:', result)
asyncio.run(main())
PYEOF
SECRET=$(systemctl cat open-webui 2>/dev/null | grep WEBUI_SECRET_KEY | head -1 | cut -d= -f2- | tr -d '"')
echo "（使用 WEBUI_SECRET_KEY 长度: ${#SECRET}）"
WEBUI_SECRET_KEY="$SECRET" /usr/local/open-webui-venv/bin/python3 /tmp/run_transcribe.py "$F" 2>&1 | tail -20
