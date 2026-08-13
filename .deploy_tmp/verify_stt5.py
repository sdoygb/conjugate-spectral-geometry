import sqlite3, json, urllib.request, uuid

db = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db'
con = sqlite3.connect(db)
rows = con.execute("select key, value from config where key like 'audio.stt%'").fetchall()
conf = {}
for k, v in rows:
    try:
        conf[k] = json.loads(v)
    except Exception:
        conf[k] = v
for k in sorted(conf):
    v = conf[k]
    print(k, '=', (str(v)[:60] + '...') if len(str(v)) > 60 else v)

model = conf.get('audio.stt.model', '')
api_key = conf.get('audio.stt.openai.api_key', '')
base = conf.get('audio.stt.openai.api_base_url', '')
url = base.rstrip('/') + '/audio/transcriptions'
print('URL:', url)

audio = open('/tmp/stt_test.wav', 'rb').read()
boundary = uuid.uuid4().hex
body = b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="model"\r\n\r\n' + model.encode() + b'\r\n'
body += b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="file"; filename="t.wav"\r\nContent-Type: audio/wav\r\n\r\n'
body += audio + b'\r\n--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request(url, data=body,
                             headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'multipart/form-data; boundary=' + boundary})
try:
    resp = urllib.request.urlopen(req, timeout=40)
    print('STT_HTTP', resp.status)
    print('STT_BODY', resp.read()[:300])
except Exception as e:
    print('STT_ERR', type(e).__name__, str(e)[:500])
