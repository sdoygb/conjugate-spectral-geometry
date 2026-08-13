#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
echo 'ab640815.' | sudo -S cp $AUDIO_PY ${AUDIO_PY}.bak_sttfix2
cat > /tmp/fix_audio2.py << 'PYEOF'
path = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py'
with open(path) as f:
    content = f.read()

# 修改1：multipart 分支——filename 必须用实际发送文件（file_path）的 basename，而非上传时的 filename（转换后扩展名不匹配）
old1 = "form_data.add_field('file', audio_data, filename=filename or os.path.basename(file_path))"
new1 = "form_data.add_field('file', audio_data, filename=os.path.basename(file_path))"

# 修改2：json 分支——ext 同样应从实际文件（file_path）取，而非上传时的 filename
old2 = "ext = os.path.splitext(filename)[1].lower().lstrip('.') or 'wav'"
new2 = "ext = os.path.splitext(file_path)[1].lower().lstrip('.') or 'wav'"

c1 = content.count(old1)
c2 = content.count(old2)
content = content.replace(old1, new1)
content = content.replace(old2, new2)
with open(path, 'w') as f:
    f.write(content)
print(f'修改1 (multipart filename): {c1} 处')
print(f'修改2 (json ext): {c2} 处')
PYEOF
echo 'ab640815.' | sudo -S python3 /tmp/fix_audio2.py
echo ""
echo "=== 确认修改 ==="
grep -n "filename=os.path.basename(file_path)\|splitext(file_path)" $AUDIO_PY
echo ""
echo "=== 语法检查 ==="
/usr/local/open-webui-venv/bin/python3 -m py_compile $AUDIO_PY && echo "语法 OK"
echo ""
echo "=== 重启 open-webui ==="
echo 'ab640815.' | sudo -S systemctl restart open-webui
sleep 6
systemctl is-active open-webui
echo ""
echo "=== 验证代码已加载（进程启动时间） ==="
systemctl show open-webui --property=ActiveEnterTimestamp,MainPID 2>/dev/null
