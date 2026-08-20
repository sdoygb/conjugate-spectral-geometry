#!/bin/bash
# G1 自动接力：等待下载完成 → 等基线回归完成 → 启动 G1 几何管道
DEST=wl_challenge/data/full/WIDE12H_bin2_2arcmin_kappa_newrealization.npy
TOTAL=6826966656
while true; do
  size=$(stat -f%z "$DEST" 2>/dev/null || echo 0)
  [ "$size" -ge "$TOTAL" ] && break
  sleep 60
done
echo "[g1_wait] kappa ready $(date)" >> wl_challenge/download.log
while ! grep -q "DONE" kappa-lab/results/baseline_regression_run.log 2>/dev/null; do
  sleep 30
done
echo "[g1_wait] baseline done, starting G1 $(date)" >> wl_challenge/download.log
cd kappa-lab && nohup python3 scripts/check_geo_pipeline.py > results/g1_pipeline_run.log 2>&1 &
echo "[g1_wait] G1 started" >> wl_challenge/download.log
