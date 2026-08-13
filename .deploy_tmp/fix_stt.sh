#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== 1. 备份 ==="
cp $AUDIO_PY ${AUDIO_PY}.bak_sttfix
ls -la ${AUDIO_PY}.bak_sttfix
echo ""
echo "=== 2. 精确替换（正则自适应缩进） ==="
python3 << 'PYEOF'
import re
path = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py'
with open(path) as f:
    content = f.read()

pattern = re.compile(
    r"(\s*)async def audio_chunks\(\):\s*\n"
    r"\s*async with aiofiles\.open\(file_path, 'rb'\) as audio_file:\s*\n"
    r"\s*while chunk := await audio_file\.read\(AIOHTTP_FILE_STREAM_CHUNK_SIZE\):\s*\n"
    r"\s*yield chunk\s*\n"
    r"\s*\n"
    r"\s*form_data\.add_field\('file', audio_chunks\(\), filename=filename\)"
)
m = pattern.search(content)
if m:
    indent = m.group(1)
    new_block = (
        f"{indent}async with aiofiles.open(file_path, 'rb') as audio_file:\n"
        f"{indent}    audio_data = await audio_file.read()\n"
        f"\n"
        f"{indent}form_data.add_field('file', audio_data, filename=filename or os.path.basename(file_path))"
    )
    content = pattern.sub(lambda _: new_block, content, count=1)
    with open(path, 'w') as f:
        f.write(content)
    print('替换成功')
else:
    print('未找到目标代码')
    m2 = re.search(r'async def audio_chunks.*?filename=filename\)', content, re.S)
    print('实际片段:', repr(m2.group(0))[:800] if m2 else '无 audio_chunks')
PYEOF
echo ""
echo "=== 3. 确认修改结果 ==="
grep -n -A 4 "audio_data = await audio_file.read()" $AUDIO_PY | head -10
grep -n "form_data.add_field('file'" $AUDIO_PY | head -5
echo ""
echo "=== 4. 重启 open-webui ==="
echo 'ab640815.' | sudo -S systemctl restart open-webui
sleep 8
systemctl is-active open-webui
echo ""
echo "=== 5. 验证：非流式 + filename 复现 ==="
cat > /tmp/verify_fix.py << 'PYEOF'
import asyncio, aiohttp
F = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/cbb6bb15-15c0-4a1a-adca-e84259ff11da.mp3'
KEY = 'sk-ouuvxvlrzjkcmcivupqzwbjqmtqoubgewbblntrvbddzjtcu'
async def test(name, filename, data_mode):
    form = aiohttp.FormData()
    form.add_field('model', 'FunAudioLLM/SenseVoiceSmall')
    if data_mode == 'bytes':
        with open(F,'rb') as f:
            data = f.read()
        form.add_field('file', data, filename=filename)
    async with aiohttp.ClientSession() as s:
        async with s.post('https://api.siliconflow.cn/v1/audio/transcriptions',
                          headers={'Authorization': f'Bearer {KEY}'},
                          data=form, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = await r.text()
            print(f'[{name}] status={r.status} body={body[:200]}')
async def main():
    await test('V1_bytes_filename_mp3', 'test.mp3', 'bytes')
    await test('V2_bytes_filename_None', None, 'bytes')
asyncio.run(main())
PYEOF
/usr/local/open-webui-venv/bin/python3 /tmp/verify_fix.py
