# Coverage lock preparation (D-020, GAP-005)

Owner approval needed: lock churn + gate re-proof. This document is
the complete execution prescription — no lockfile was modified.

## 1. requirements.txt addition

```text
# D-020: coverage measurement (pins PyPI-verified 2026-11-05).
pytest-cov==7.1.0
coverage==7.10.6
```

No other additions: `pytest>=7` and `pluggy>=1.2` are satisfied by
the locked pytest 9.0.3 / pluggy 1.7.0, and Python 3.13 uses stdlib
`tomllib` (no `tomli` backport).

## 2. Verified artifact hashes (evidence, not hand edits)

Fetched from PyPI 2026-11-05 (sha256):

- `pytest_cov-7.1.0-py3-none-any.whl`
  `a0461110b7865f9a271aa1b51e516c9a95de9d696734a2f71e3e78f46e1d4678`
- `coverage-7.10.6-cp313-cp313-win_amd64.whl`
  `62805529f3e2aa181464c3808402887643405573eb3d9de060d81531fa79d32`
- `coverage-7.10.6-cp313-cp313-manylinux...x86_64.whl`
  `0f3f56e4cb573755e96a16501a98bf211f100463d70275759e73f3cbc00d4f27`

Do NOT hand-write lock entries. Regenerate with pip-compile (same
command as the lock header) so every artifact hash is complete:

```text
pip-compile --generate-hashes --output-file=requirements.lock \
  --pip-args='--timeout=30 --retries=1' requirements.txt
```

Review the resulting diff: only `pytest-cov`, `coverage` (and any
documented transitive bumps) may appear.

## 3. CI step (security-gate.yml, after "Backend regression")

```yaml
      - name: Backend coverage
        env:
          STORE_BACKEND: json
        run: >
          python -m pytest tests/ -q -p no:cacheprovider
          --cov=app --cov=backups --cov=migrations
          --cov-report=term-missing --cov-fail-under=70
```

Threshold 70 is a starting ratchet: critical security/financial
paths already carry explicit tests; raise only with evidence, never
by deleting tests.

## 4. Frontend (blocked on networked npm)

`@vitest/coverage-v8@3.2.7` (exact match to locked vitest 3.2.7 —
zero-conflict) + `vitest run --coverage` step. Hash capture needs a
networked npm run; npm is unavailable in this sandbox (EPERM).

## 5. Acceptance

1. `pip install --require-hashes -r requirements.lock` green.
2. `python scripts/security_gate.py` green (re-proof after churn).
3. Full backend suite green + coverage report artifact.
4. Frontend coverage step green in hosted CI.
