"""断点续传下载 Zenodo 弱透镜训练数据（6.36 GB）"""
import urllib.request, os, time, sys

URL = 'https://zenodo.org/records/20056065/files/WIDE12H_bin2_2arcmin_kappa_newrealization.npy?download=1'
DEST = 'wl_challenge/data/full/WIDE12H_bin2_2arcmin_kappa_newrealization.npy'
TOTAL = 6826966656
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

def download(timeout=112):
    size = os.path.getsize(DEST) if os.path.exists(DEST) else 0
    headers = {'User-Agent': UA, 'Referer': 'https://zenodo.org/'}
    if size > 0:
        headers['Range'] = f'bytes={size}-'
    req = urllib.request.Request(URL, headers=headers)
    t0 = time.time()
    downloaded_this_run = 0
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            with open(DEST, 'ab') as f:
                while time.time() - t0 < timeout:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    size += len(chunk)
                    downloaded_this_run += len(chunk)
    except Exception as e:
        print('warning:', str(e)[:120])
    return size, downloaded_this_run

size, got = download()
print(f'progress: {size}/{TOTAL} = {size / TOTAL * 100:.2f}%  (this run: {got / 1024 / 1024:.0f} MB)')
print('COMPLETE' if size >= TOTAL else 'CONTINUE')
