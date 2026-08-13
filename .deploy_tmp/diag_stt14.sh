#!/bin/bash
AUDIO_PY=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py

echo "=== 1. Config.get 运行时实际值 ==="
cat > /tmp/check_config.py << 'PYEOF'
import asyncio
async def main():
    from open_webui.config import Config
    for k in ['audio.stt.model', 'audio.stt.openai.api_base_url', 'audio.stt.openai.api_key', 'audio.stt.openai.api_request_format', 'audio.stt.engine']:
        v = await Config.get(k)
        print(f'{k} = {v!r}')
asyncio.run(main())
PYEOF
/usr/local/open-webui-venv/bin/python3 /tmp/check_config.py 2>&1 | tail -8

echo ""
echo "=== 2. 添加诊断日志 ==="
echo 'ab640815.' | sudo -S cp $AUDIO_PY ${AUDIO_PY}.bak_sttdiag
cat > /tmp/patch_diag.py << 'PYEOF'
path = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py'
with open(path) as f:
    c = f.read()

old_send = "                form_data.add_field('file', audio_data, filename=os.path.basename(file_path))"
new_send = """                log.error(
                    f'STT_DIAG send file={os.path.basename(file_path)} size={len(audio_data)} payload={payload} head={audio_data[:24].hex()}'
                )
                form_data.add_field('file', audio_data, filename=os.path.basename(file_path))"""
n1 = c.count(old_send)
c = c.replace(old_send, new_send)

old_exc = """    except Exception as e:
        log.exception(e)
        detail = None
        if r is not None:
            try:
                res = await r.json()
                if 'error' in res:
                    detail = f'External: {res["error"].get("message", "")}'
            except Exception:
                detail = f'External: {e}'
        raise Exception(detail if detail else 'Open WebUI: Server Connection Error')"""
new_exc = """    except Exception as e:
        log.exception(e)
        detail = None
        if r is not None:
            try:
                body_text = await r.text()
                log.error(f'STT_DIAG response status={r.status} body={body_text[:600]}')
                try:
                    res = json.loads(body_text)
                    if 'error' in res:
                        detail = f'External: {res["error"].get("message", "")}'
                except Exception:
                    detail = f'External: {e}'
            except Exception:
                detail = f'External: {e}'
        raise Exception(detail if detail else 'Open WebUI: Server Connection Error')"""
n2 = c.count(old_exc)
c = c.replace(old_exc, new_exc)

with open(path, 'w') as f:
    f.write(c)
print(f'发送前日志: {n1} 处; except日志: {n2} 处')
PYEOF
echo 'ab640815.' | sudo -S python3 /tmp/patch_diag.py

echo ""
echo "=== 3. 重启服务 ==="
echo 'ab640815.' | sudo -S systemctl restart open-webui
sleep 4
systemctl is-active open-webui
systemctl show open-webui --property=MainPID
