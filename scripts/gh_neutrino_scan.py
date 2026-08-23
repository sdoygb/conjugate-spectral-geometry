import json, ssl, time, urllib.request, os

TOKEN = open(os.path.expanduser('~/Downloads/GeometryAI-Mac-Build/.github_token')).read().strip()
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + TOKEN,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return json.loads(r.read().decode())

# 候选仓库列表（owner/repo）
cands = [
    # 中微子
    "joaoabcoelho/OscProb",
    "Arguelles/nuSQuIDS",
    "arguelles/nuSQuIDS",
    "jsalvado/SQuIDS",
    "Arguelles/SQuIDS",
    "nu-radio/NuRadioMC",
    "nu-radio/NuRadioReco",
    "SNEWS2/snewpy",
    "graphnet-team/graphnet",
    "icecube/csky",
    "icecube/pisa",
    "icecube/photospline",
    "tudo-astroparticlephysics/PROPOSAL",
    "genie-mcgenerator/genie",
    # 几何/谱
    "pyRiemann/pyRiemann",
    "pymanopt/pymanopt",
    "DedalusProject/dedalus",
    "spectralDNS/shenfun",
    "spectralDNS/spectralDNS",
    "yixuan/spectra",
    "kwant-project/kwant",
    "PythonOT/POT",
    "ott-jax/ott",
    "jeanfeydy/geomloss",
]

print("=== 候选核实 ===")
for c in cands:
    try:
        d = get(f"https://api.github.com/repos/{c}")
        # 最近更新天数
        from datetime import datetime, timezone
        upd = datetime.strptime(d["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - upd).days
        print(f"{c:45s} star={d['stargazers_count']:6d} fork={d['forks_count']:5d} "
              f"issues={d['open_issues_count']:4d} lang={str(d.get('language')):10s} "
              f"upd={days:4d}d ago  archived={d['archived']}")
    except Exception as e:
        print(f"{c:45s} ERROR {e}")

# 搜索补充：中微子振荡高星仓库
print("\n=== search: neutrino oscillation ===")
try:
    r = get("https://api.github.com/search/repositories?q=neutrino+oscillation&sort=stars&order=desc&per_page=15")
    for it in r["items"]:
        print(f"{it['full_name']:45s} star={it['stargazers_count']:6d} lang={str(it.get('language')):10s} upd={it['updated_at'][:10]} desc={str(it.get('description'))[:70]}")
except Exception as e:
    print("search ERR", e)

print("\n=== search: neutrino physics python ===")
try:
    r = get("https://api.github.com/search/repositories?q=neutrino+physics+language:python&sort=stars&order=desc&per_page=15")
    for it in r["items"]:
        print(f"{it['full_name']:45s} star={it['stargazers_count']:6d} lang={str(it.get('language')):10s} upd={it['updated_at'][:10]} desc={str(it.get('description'))[:70]}")
except Exception as e:
    print("search ERR", e)

print("\n=== search: spectral methods ===")
try:
    r = get("https://api.github.com/search/repositories?q=spectral+methods&sort=stars&order=desc&per_page=12")
    for it in r["items"]:
        print(f"{it['full_name']:45s} star={it['stargazers_count']:6d} lang={str(it.get('language')):10s} upd={it['updated_at'][:10]} desc={str(it.get('description'))[:70]}")
except Exception as e:
    print("search ERR", e)
