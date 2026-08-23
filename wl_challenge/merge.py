#!/usr/bin/env python3
"""续传式合并：把 8 个 part 顺序拼成目标 npy。可中断，可续传。"""
import os, time

PARTS = 'wl_challenge/data/full/parts'
DEST = 'wl_challenge/data/full/WIDE12H_bin2_2arcmin_kappa_newrealization_merged.npy'
PART_SIZE = 853370832
NSEG = 8
TOTAL = 6826966656

def merge(max_seconds=105):
    cur = os.path.getsize(DEST) if os.path.exists(DEST) else 0
    t0 = time.time()
    with open(DEST, 'ab') as out:
        for i in range(NSEG):
            p = f'{PARTS}/part_{i}.bin'
            size = os.path.getsize(p)
            if cur >= size * (i + 1):
                continue  # 这个 part 已完整合并
            if cur < size * i:
                continue  # 前面的 part 还没补完（理论上不会发生）
            start_off = cur - size * i  # 本 part 内已合并的偏移（0 表示从头）
            with open(p, 'rb') as f:
                if start_off:
                    f.seek(start_off)
                while True:
                    if time.time() - t0 > max_seconds:
                        print(f'checkpoint: {cur}/{TOTAL} ({(cur/TOTAL*100):.1f}%) part {i} off {start_off}')
                        return False
                    chunk = f.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    cur += len(chunk)
        print(f'DONE {cur}/{TOTAL}')
        return cur == TOTAL

if __name__ == '__main__':
    done = merge()
    if done:
        print('MERGED COMPLETE')
    else:
        print('run again to continue')
