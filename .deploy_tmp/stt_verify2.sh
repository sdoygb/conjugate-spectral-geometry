#!/bin/bash
echo "=== 1. db 当前 STT 配置 ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE 'audio.stt%'\")
for k, v in cur.fetchall():
    if 'api_key' in k:
        print(f'{k} = {v[:10]}...{v[-4:]}')
    else:
        print(f'{k} = {v!r}')
conn.close()
" 2>/dev/null

echo ""
echo "=== 2. Config.get 运行时值 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import asyncio
async def main():
    from open_webui.config import Config
    for k in ['audio.stt.model','audio.stt.openai.api_base_url','audio.stt.openai.api_request_format','audio.stt.engine']:
        v = await Config.get(k)
        print(f'{k} = {v!r}')
asyncio.run(main())
" 2>&1 | tail -6

echo ""
echo "=== 3. 实测 multipart ==="
KEY=$(echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
print(conn.execute(\"SELECT value FROM config WHERE key='audio.stt.openai.api_key'\").fetchone()[0])
" 2>/dev/null)
echo "KEY 前6位: ${KEY:0:6}"
curl -s -o /tmp/resp_mp.txt -w "HTTP %{http_code}\n" -X POST https://api.siliconflow.cn/v1/audio/transcriptions -H "Authorization: Bearer $KEY" -F "model=FunAudioLLM/SenseVoiceSmall" -F "file=@/tmp/test_latest.mp3"
head -c 300 /tmp/resp_mp.txt; echo

echo ""
echo "=== 4. 实测 json 格式 ==="
python3 -c "
import base64, json
data = open('/tmp/test_latest.mp3','rb').read()
payload = {'model':'FunAudioLLM/SenseVoiceSmall','input_audio':{'data':base64.b64encode(data).decode(),'format':'mp3'}}
open('/tmp/payload.json','w').write(json.dumps(payload))
"
curl -s -o /tmp/resp_json.txt -w "HTTP %{http_code}\n" -X POST https://api.siliconflow.cn/v1/audio/transcriptions -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d @/tmp/payload.json
head -c 300 /tmp/resp_json.txt; echo

echo ""
echo "=== 5. 实测 json+language 组合 ==="
python3 -c "
import json
p = json.load(open('/tmp/payload.json'))
p['language'] = 'zh'
open('/tmp/payload2.json','w').write(json.dumps(p))
"
curl -s -o /tmp/resp_json2.txt -w "HTTP %{http_code}\n" -X POST https://api.siliconflow.cn/v1/audio/transcriptions -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d @/tmp/payload2.json
head -c 300 /tmp/resp_json2.txt; echo
