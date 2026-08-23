"""多线程分块下载 Zenodo 弱透镜训练数据（防双写版）
- 单实例锁（pid 存活检查，shell 超时杀不掉也能恢复）
- 严格限制每段读取量 <= 剩余量（服务端多给也不多写）
"""
import urllib.request, os, threading, time, sys

URL = 'https://zenodo.org/records/20056065/files/WIDE12H_bin2_2arcmin_kappa_newrealization.npy?download=1'
TOTAL = 6826966656
NSEG = 8
DEST = 'wl_challenge/data/full/WIDE12H_bin2_2arcmin_kappa_newrealization.npy'
PARTDIR = 'wl_challenge/data/full/parts'
LOCK = 'wl_challenge/.multi_dl.lock'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

# ---- 单实例锁 ----
if os.path.exists(LOCK):
    try:
        with open(LOCK) as f:
            pid = int(f.read().strip() or 0)
        os.kill(pid, 0)
        print(f'another instance running (pid {pid}), exit')
        sys.exit(0)
    except (OSError, ValueError):
        os.remove(LOCK)
with open(LOCK, 'w') as f:
    f.write(str(os.getpid()))

try:
    os.makedirs(PARTDIR, exist_ok=True)
    seg = TOTAL // NSEG
    ranges = [(i * seg, (i + 1) * seg - 1 if i < NSEG - 1 else TOTAL - 1) for i in range(NSEG)]

    def dl_seg(idx, start, end):
        part = f'{PARTDIR}/part_{idx}.bin'
        done = os.path.getsize(part) if os.path.exists(part) else 0
        remaining = end - start + 1 - done
        if remaining <= 0:
            return
        headers = {'User-Agent': UA, 'Referer': 'https://zenodo.org/',
                   'Range': f'bytes={start + done}-{end}'}
        req = urllib.request.Request(URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                with open(part, 'ab') as f:
                    while remaining > 0:
                        chunk = r.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
        except Exception as e:
            print(f'  seg{idx} warn: {str(e)[:80]}')

    t0 = time.time()
    threads = [threading.Thread(target=dl_seg, args=(i, s, e)) for i, (s, e) in enumerate(ranges)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    sizes = [os.path.getsize(f'{PARTDIR}/part_{i}.bin') for i in range(NSEG)]
    total = sum(sizes)
    dt = time.time() - t0
    print('segments(MB):', [round(s / 1048576, 1) for s in sizes])
    print(f'total: {total}/{TOTAL} = {total / TOTAL * 100:.2f}%')

    if total == TOTAL:
        with open(DEST, 'wb') as out:
            for i in range(NSEG):
                with open(f'{PARTDIR}/part_{i}.bin', 'rb') as f:
                    out.write(f.read())
        print('MERGED COMPLETE ->', DEST)
    elif total > TOTAL:
        print('ERROR: oversize, need cleanup')
finally:
    if os.path.exists(LOCK):
        os.remove(LOCK)
