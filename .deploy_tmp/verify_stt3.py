import sqlite3, json, urllib.request, uuid, os

db = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db'
con = sqlite3.connect(db)
rows = con.execute("select key, value from config where key like 'audio.stt.openai%'").fetchall()
conf = {}
for k, v in rows:
    short = k.replace('audio.stt.openai', '').strip('.')
    try:
        conf[short] = json.loads(v)
    except Exception:
        conf[short] = v
print('config keys:', sorted(conf.keys()))
key = conf.get('api_key', '')
model = conf.get('model', '')
fmt = conf.get('api_request_format', 'multipart')
print('fmt=%s model=%s key=%s...' % (fmt, model, str(key)[:6]))

cjson = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/099137f3-453b-47f8-806c-f549643dc7fc.json'
if os.path.exists(cjson):
    print('CACHE_JSON(10:05):', open(cjson).read()[:300])

audio = open('/tmp/stt_test.wav', 'rb').read()
boundary = uuid.uuid4().hex
body = b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="model"\r\n\r\n' + model.encode() + b'\r\n'
body += b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="file"; filename="t.wav"\r\nContent-Type: audio/wav\r\n\r\n'
body += audio + b'\r\n--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request('https://api.siliconflow.cn/v1/audio/transcriptions', data=body,
                             headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'multipart/form-data; boundary=' + boundary})
try:
    resp = urllib.request.urlopen(req, timeout=40)
    print('STT_HTTP', resp.status)
    print('STT_BODY', resp.read()[:300])
except Exception as e:
    print('STT_ERR', type(e).__name__, str(e)[:500])
