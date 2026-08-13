#!/bin/bash
echo "=== 1. open-webui 服务 STT 环境变量 ==="
systemctl cat open-webui 2>/dev/null | grep -iE "STT|AUDIO|SPEECH|TRANSCRI|WHISPER|ASR" || echo "（无 STT 相关环境变量，配置应在 WebUI 设置/数据库里）"
echo ""
echo "=== 2. journalctl 最近 STT 错误 ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "6 hours ago" --no-pager 2>/dev/null | grep -iE "transcrib|422|stt|audio" | tail -15 || echo "（无匹配日志）"
echo ""
echo "=== 3. webui.db 中的 STT 配置 ==="
python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
cur = conn.cursor()
try:
    cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='config'\")
    if cur.fetchone():
        cur.execute(\"SELECT key, value FROM config WHERE key LIKE '%stt%' OR key LIKE '%audio%' OR key LIKE '%speech%' OR key LIKE '%transcrib%'\")
        rows = cur.fetchall()
        if rows:
            for k, v in rows:
                # 隐藏 api_key 的值
                if 'key' in k.lower() or 'token' in k.lower():
                    print(f'{k} = sk-***（已设置）' if v and len(v) > 6 else f'{k} = （空）')
                else:
                    print(f'{k} = {v}')
        else:
            print('（config 表中无 STT 相关键）')
    else:
        print('（无 config 表）')
except Exception as e:
    print('查询失败:', e)
conn.close()
"
echo ""
echo "=== 4. SiliconFlow STT 模型列表（用 geometry-ai .env 的 key） ==="
KEY=$(grep -E "^SILICONFLOW_API_KEY" /usr/local/geometry-ai/.env 2>/dev/null | head -1 | cut -d= -f2-)
if [ -n "$KEY" ]; then
  curl -s --max-time 15 -H "Authorization: Bearer $KEY" https://api.siliconflow.cn/v1/models 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    models = [m.get('id','') for m in d.get('data', [])]
    stt = [m for m in models if any(x in m.lower() for x in ['audio','sensevoice','whisper','asr','speech','voice'])]
    if stt:
        print('STT/ASR 相关模型:')
        for m in stt: print(' -', m)
    else:
        print('（模型列表中没有明显的 STT 模型，共', len(models), '个模型）')
        # 打印前 20 个看看
        for m in models[:20]: print('   -', m)
except Exception as e:
    print('解析失败:', e)
"
else
  echo "（.env 无 SILICONFLOW_API_KEY）"
fi
