# Contributing

Contributions are welcome. The project follows standard open-source
practices; for anything larger than a typo fix, please open an issue first
to discuss the change.

## Development setup

```bash
git clone https://github.com/sdoygb/qec-distance-certificates.git
cd qec-distance-certificates
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install pytest build twine
```

## Running the tests

```bash
.venv/bin/python -m pytest -q
```

All 15 tests must pass. The test suite includes exact closed-form anchors
(2-flat counts of AG(5,2) and AG(6,2)) that cross-validate the certificate
path against the brute-force path.

## Design principles

- **Distance-certifying, not distance-finding.** The certificate path never
  enumerates the error space; keep it that way. Any new code path that
  grows with sum_{w<d} C(n,w) belongs in `brute.py`, not in `certificate.py`.
- **Machine-checked, not trusted.** Every field of `DistanceCertificate`
  must be produced by an executed check on the machine, never by citation.
- **Big-integer bit masks.** Vectors are Python integers with bit `v`
  corresponding to the point `v` of AG(m,2). Keep this convention uniform.

## Release checklist

1. Bump the version in `pyproject.toml` and `CHANGELOG.md`.
2. `python -m build && twine check dist/*`
3. Tag the release: `git tag vX.Y.Z && git push origin vX.Y.Z`
4. Upload to PyPI: `twine upload dist/*`
