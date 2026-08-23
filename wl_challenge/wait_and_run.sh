#!/bin/bash
# 等待 full 数据下载完成 → 软链接 kappa_full.npy → 启动基线回归（阶段1）
TOTAL=6826966656
DEST=wl_challenge/data/full/WIDE12H_bin2_2arcmin_kappa_newrealization.npy
LINK=wl_challenge/data/full/kappa_full.npy
while true; do
  size=$(stat -f%z "$DEST" 2>/dev/null || echo 0)
  if [ "$size" -ge "$TOTAL" ]; then break; fi
  sleep 60
done
echo "[$(date)] download complete ($size bytes)" >> wl_challenge/download.log
[ -e "$LINK" ] || ln -s WIDE12H_bin2_2arcmin_kappa_newrealization.npy "$LINK"
echo "[$(date)] kappa_full.npy link ready" >> wl_challenge/download.log
cd "$(dirname "$0")/.." || exit 1
nohup python3 kappa-lab/scripts/run_baseline_regression.py \
  > kappa-lab/results/baseline_regression_run.log 2>&1 &
echo "[$(date)] regression started pid $!" >> wl_challenge/download.log
