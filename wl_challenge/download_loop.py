#!/usr/bin/env python3
"""循环断点续传，直到 kappa_full 数据下载完成。用法：nohup python3 wl_challenge/download_loop.py > wl_challenge/download.log 2>&1 &"""
import sys, time
sys.path.insert(0, '.')
import importlib.util
spec = importlib.util.spec_from_file_location('dl', 'wl_challenge/download.py')
dl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dl)

TOTAL = 6826966656
while True:
    size, got = dl.download(50)  # 每次 50 秒（shell 超时 60s 余量）
    print(f'progress: {size}/{TOTAL} = {size/TOTAL*100:.2f}% (this run {got/1e6:.0f} MB)', flush=True)
    if size >= TOTAL:
        break
    time.sleep(1)
print('DOWNLOAD COMPLETE')
