#!/usr/bin/env python3
"""Download 2026 Phase-2 public dataset from Codabench (8.7 GB)."""
import urllib.request, os, sys, time, json

URL = "https://www.codabench.org/datasets/download/09b7a27a-bfb3-4031-a5b0-9b3c533f45e6/"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "2026")
OUT_FILE = os.path.join(OUT_DIR, "phase2_2026_public.zip")
LOG = os.path.join(OUT_DIR, "download_2026.log")

os.makedirs(OUT_DIR, exist_ok=True)

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg, flush=True)

def download(retries=3):
    for attempt in range(1, retries + 1):
        try:
            log(f"Attempt {attempt}: downloading {URL}")
            req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(OUT_FILE, "wb") as f:
                total = int(resp.headers.get("Content-Length", 0))
                done = 0
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if done % (200 * 1024 * 1024) < 1024 * 1024:
                        log(f"  {done/1e9:.2f} / {total/1e9:.2f} GB")
            log(f"Done: {OUT_FILE} ({os.path.getsize(OUT_FILE)/1e9:.2f} GB)")
            return True
        except Exception as e:
            log(f"Attempt {attempt} failed: {e}")
            time.sleep(30 * attempt)
    return False

if __name__ == "__main__":
    ok = download()
    log(f"RESULT: {'OK' if ok else 'FAILED'}")
    sys.exit(0 if ok else 1)
