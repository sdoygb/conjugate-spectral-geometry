#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo "=== 1. 备份（sudo） ==="
echo 'ab640815.' | sudo -S cp $AUDIO_PY ${AUDIO_PY}.bak_sttfix 2>/dev/null
ls -la ${AUDIO_PY}.bak_sttfix 2>/dev/null || echo "备份失败"
echo ""
echo "=== 2. 替换（sudo python3） ==="
cat > /tmp/fix_audio.py << 'PYEOF'
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
    print('实际片段:', repr(m2.group(0))[:600] if m2 else '无 audio_chunks')
PYEOF
echo 'ab640815.' | sudo -S python3 /tmp/fix_audio.py 2>/dev/null
echo ""
echo "=== 3. 确认修改 ==="
grep -n -B 1 -A 3 "audio_data = await audio_file.read()" $AUDIO_PY | head -12
grep -n "form_data.add_field('file'" $AUDIO_PY
echo ""
echo "=== 4. 查看 1020 行上下文（另一个 add_field） ==="
sed -n '1000,1030p' $AUDIO_PY
echo ""
echo "=== 5. 重启 open-webui ==="
echo 'ab640815.' | sudo -S systemctl restart open-webui 2>/dev/null
sleep 8
systemctl is-active open-webui
echo ""
echo "=== 6. 语法检查 ==="
/usr/local/open-webui-venv/bin/python3 -c "import ast; ast.parse(open('$AUDIO_PY').read()); print('audio.py 语法 OK')"
