#!/usr/bin/env python3
"""Scan hot & actively maintained repos across our skill axes.
Checks: stars, push recency, open PR median age, merged-PR author diversity.
"""
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = open(
    os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
).read().strip()
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

API = "https://api.github.com"


def req(url, method="GET", data=None):
    r = urllib.request.Request(url, method=method, data=data)
    r.add_header("Authorization", f"token {TOKEN}")
    r.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(r, context=CTX) as resp:
        return json.loads(resp.read().decode())


def search(q, n=8):
    u = f"{API}/search/repositories?q={urllib.parse.quote(q)}&sort=stars&per_page={n}"
    try:
        return req(u)["items"]
    except Exception as e:
        print(f"  ! search failed: {q} -> {e}")
        return []


def age_days(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def pr_stats(full_name):
    """merged-PR author diversity (last 30 closed) + open PR median age."""
    try:
        closed = req(f"{API}/repos/{full_name}/pulls?state=closed&sort=updated"
                     "&direction=desc&per_page=30")
        merged = [p for p in closed if p.get("merged_at")]
        authors = sorted({p["user"]["login"] for p in merged})
        openp = req(f"{API}/repos/{full_name}/pulls?state=open&per_page=30")
        ages = sorted([age_days(p["created_at"]) for p in openp])
        med_age = ages[len(ages) // 2] if ages else -1
        return len(merged), len(authors), med_age, len(openp)
    except Exception as e:
        return -1, -1, -1, -1


def show(full_name):
    try:
        r = req(f"{API}/repos/{full_name}")
        pushed = age_days(r["pushed_at"])
        nm, na, med, nopen = pr_stats(full_name)
        print(
            f"{full_name:55s} star={r['stargazers_count']:>6d} "
            f"push={pushed:>3d}d "
            f"openPR={nopen:>3d}(medAge={med:>4d}d) "
            f"mrg30={nm:>2d}/auth={na:>2d}"
        )
    except Exception as e:
        print(f"{full_name:55s} ! {e}")


print("=== targeted searches (stars desc, pushed last 60d) ===")
for q in [
    "quantum+error+correction+pushed:>2026-06-15",
    "quantum+computing+simulator+pushed:>2026-06-15",
    "riemannian+optimization+pushed:>2026-05-01",
    "geometric+deep+learning+pushed:>2026-06-01",
    "spectral+methods+pushed:>2026-05-01",
    "optimal+transport+pushed:>2026-05-01",
    "manifold+learning+pushed:>2026-05-01",
]:
    items = search(q)
    print(f"\n-- {q}")
    for it in items[:8]:
        print(f"   {it['full_name']:50s} star={it['stargazers_count']:>6d} "
              f"push={age_days(it['pushed_at']):>3d}d")

print("\n=== detailed PR dynamics for shortlist ===")
for name in [
    "qutip/qutip",
    "PennyLaneAI/pennylane",
    "quantumlib/stim",
    "quantumlib/Cirq",
    "Qiskit/qiskit",
    "geomstats/geomstats",
    "geoopt/geoopt",
    "PythonOT/POT",
    "ott-jax/ott",
    "DedalusProject/dedalus",
    "yixuan/spectra",
    "pymanopt/pymanopt",
    "google-deepmind/optax",
    "jax-ml/jax",
]:
    show(name)
