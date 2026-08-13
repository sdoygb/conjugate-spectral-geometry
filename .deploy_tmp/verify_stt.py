import sqlite3, json, urllib.request, uuid, ssl, os, glob, subprocess

db = '/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db'
audio_path = '/tmp/test_latest.mp3'
if not os.path.exists(audio_path):
    cands = glob.glob('/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*/*.mp3')
    cands += glob.glob('/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*/*.wav')
    if not cands:
        print('NO_TEST_AUDIO'); exit(1)
    audio_path = sorted(cands)[-1]
print('audio:', audio_path)

con = sqlite3.connect(db)
row = con.execute("select data from config where id='audio.stt.openai'").fetchone()
conf = json.loads(row[0])
key = conf['api_key']; model = conf['model']; fmt = conf.get('api_request_format', 'multipart')
print('config: fmt=%s model=%s key=%s...' % (fmt, model, key[:6]))

audio = open(audio_path, 'rb').read()
boundary = uuid.uuid4().hex
body = b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="model"\r\n\r\n' + model.encode() + b'\r\n'
body += b'--' + boundary.encode() + b'\r\nContent-Disposition: form-data; name="file"; filename="t.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'
body += audio + b'\r\n--' + boundary.encode() + b'--\r\n'
req = urllib.request.Request('https://api.siliconflow.cn/v1/audio/transcriptions', data=body,
                             headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'multipart/form-data; boundary=' + boundary})
try:
    resp = urllib.request.urlopen(req, timeout=40)
    print('STT_HTTP', resp.status)
    print('STT_BODY', resp.read()[:300])
except Exception as e:
    print('STT_ERR', type(e).__name__, str(e)[:400])

pid = subprocess.run(['systemctl', 'show', 'open-webui', '-p', 'MainPID', '--value'], capture_output=True, text=True).stdout.strip()
r = subprocess.run(['bash', '-c', "echo 'ab640815.' | sudo -S ls -l /proc/" + pid + "/fd 2>/dev/null | grep -iE 'webui|data' | head -8"], capture_output=True, text=True)
print('FD:', r.stdout)
