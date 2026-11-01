# CruiseShield AI — Security Gate Policy (P2.2D)

## 1. What the gate enforces

Every push, pull request, and weekly schedule runs
`.github/workflows/security-gate.yml`, which fails on ANY of:

1. **Known vulnerabilities.** `pip-audit` against `requirements.lock`
   reports a vulnerability with an available fix, unless that exact
   advisory ID is listed in an approved exceptions file passed with
   `--exceptions`. Any finding without a fix version fails pending
   documented review.
2. **Invalid dependency hashes.** `pip install --require-hashes`
   rejects a mismatch, or `requirements.lock` lacks a sha256 hash for
   any pin.
3. **Unexpected dependency changes.** A `requirements.txt` pin missing
   from the lock, a version drift between the two, or an installed
   distribution that is neither locked nor documented audit tooling.
4. **Real credentials or private keys.** The gate's secret scan or
   gitleaks flags AWS keys, long provider tokens, PEM private-key
   blocks, age secret keys, or embedded AWS secret values.
5. **Failed mandatory tests.** Backend suite, frontend suite,
   TypeScript validation, or production build exits non-zero.

## 2. Severity and remediation

- CRITICAL or HIGH advisory with a fix: remediate (pin lift + lock
  regeneration + full regression) before any dependent change merges.
- MEDIUM or LOW with a fix: remediate in the same cycle; an exception
  (section 3) may defer it once with a review date.
- No fix available: document exposure analysis; fail closed until the
  maintainers accept the risk in writing via section 3.

## 3. Exceptions

Approved exceptions live in a JSON file with this shape:

```json
[
  {"id": "PYSEC-2026-0000", "owner": "name",
   "reason": "why this is safe or deferred",
   "review_date": "2026-11-30"}
]
```

Rules: one entry per advisory ID, a named owner, a dated review, and
re-approval at every review date. Expired or ownerless entries do not
except anything. **Currently approved exceptions: none.**

## 4. Test fixtures vs real secrets

Short synthetic strings in tests (`ghp_Xyz123`, `TEST-ONLY-...`) are
fixtures by construction: the scanner only matches real-length token
shapes and key blocks. Never "fix" a scanner hit by shortening a real
credential — rotate it instead.

## 5. Ownership

The gate script (`scripts/security_gate.py`), lockfile, and this
policy change only through reviewed phases. The weekly scheduled run
reports audit drift even when no code changes.
