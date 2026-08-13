#!/bin/bash
echo "=== transcription_handler（880-930行）：languages 来源 ==="
sed -n '880,930p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo ""
echo "=== transcribe 函数（1040-1075行） ==="
sed -n '1040,1075p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo ""
echo "=== language 变体测试（bytes + mp3 + openwebui key） ==="
cat > /tmp/lang_test.py << 'PYEOF'
import asyncio, aiohttp, glob
F = glob.glob('/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/141f3a3e-*.mp3')
F = F[0] if F else None
print(f'测试文件: {F}')
KEY = 'sk-ouuvxvlrzjkcmcivupqzwbjqmtqoubgewbblntrvbddzjtcu'
MODEL = 'FunAudioLLM/SenseVoiceSmall'
async def test(lang):
    form = aiohttp.FormData()
    form.add_field('model', MODEL)
    if lang:
        form.add_field('language', lang)
    with open(F,'rb') as f:
        data = f.read()
    form.add_field('file', data, filename='141f3a3e-test.mp3')
    async with aiohttp.ClientSession() as s:
        async with s.post('https://api.siliconflow.cn/v1/audio/transcriptions',
                          headers={'Authorization': f'Bearer {KEY}'},
                          data=form, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = await r.text()
            print(f'language={lang!r}: status={r.status} body={body[:120]}')
async def main():
    for lang in [None, 'zh', 'zh-CN', 'zh_CN', 'Chinese', 'chinese', 'cmn', 'auto', 'en']:
        try:
            await test(lang)
        except Exception as e:
            print(f'language={lang!r}: EXC {e}')
asyncio.run(main())
PYEOF
/usr/local/open-webui-venv/bin/python3 /tmp/lang_test.py
