#!/bin/bash
echo "=== 1. 用最新实际文件测试（模拟修改后代码的完整请求） ==="
cat > /tmp/repro_stt3.py << 'PYEOF'
import asyncio, aiohttp, os, glob
KEY = 'sk-ouuvxvlrzjkcmcivupqzwbjqmtqoubgewbblntrvbddzjtcu'
files = sorted(glob.glob('/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*.mp3'), key=os.path.getmtime)
F = files[-1]
print(f'文件: {F} ({os.path.getsize(F)} bytes)')
async def test():
    form = aiohttp.FormData()
    form.add_field('model', 'FunAudioLLM/SenseVoiceSmall')
    with open(F, 'rb') as f:
        data = f.read()
    form.add_field('file', data, filename=os.path.basename(F))
    async with aiohttp.ClientSession() as s:
        async with s.post('https://api.siliconflow.cn/v1/audio/transcriptions',
                          headers={'Authorization': f'Bearer {KEY}'},
                          data=form) as r:
            body = await r.text()
            print(f'模拟修改后代码: status={r.status}')
            print(f'响应: {body[:300]}')
asyncio.run(test())
PYEOF
/usr/local/open-webui-venv/bin/python3 /tmp/repro_stt3.py
echo ""
echo "=== 2. get_session 定义位置 ==="
grep -rn "async def get_session" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/ 2>/dev/null | head -3
echo ""
echo "=== 3. ENABLE_FORWARD_USER_INFO_HEADERS ==="
grep -rn "ENABLE_FORWARD_USER_INFO_HEADERS" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/config.py 2>/dev/null | head -3
echo ""
echo "=== 4. 09:31:55 之后的新尝试日志 ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "09:31:55" --no-pager 2>/dev/null | grep -iE "transcrib|422|chunk|Converted" | tail -8
