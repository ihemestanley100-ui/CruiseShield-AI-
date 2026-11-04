# J3 — REMAINING GAP REGISTER

Every item not PASS, with owner and unblock condition. Nothing hidden.

## PARTIAL — CI-gated (run automatically post-push)

- **AI-09** TimeoutException→MODEL_TIMEOUT mapping test. Owner: CI.
  Unblock: loop-capable runner. Local half (passthrough + 35 s abort)
  green.
- **AI-11** 5 AIError codes end-to-end (TIMEOUT/PROVIDER_UNAVAILABLE/
  REFUSED/TRUNCATED/MALFORMED). Owner: CI. 4 codes green locally.
- **AI-17-half** run-usage persistence test. Owner: CI. Missing-usage
  tolerance green locally.
- **P9-transport** 10 TestClient twins. Owner: CI. Direct twins green.

## PARTIAL — environment-gated

- **FE-35** real contrast ratios + screen-reader behavior. Owner:
  whoever runs browser/AT pass (devices needed). Tokens verified.

## PARTIAL — owner-gated

- **AI-05** DI-validator production wiring (design decision).
- **DC-02** R-13 acceptance proof filing (eligibility stays AT_RISK).
- **DC-21** %TEMP% proof + backup execution (D-008 destination).

## BLOCKED — owner approval

- **R4** live Meta call + quota/billing. Needs: explicit quota-spend
  approval + networked env. Key present locally (count 1, unread).
- **BE-23/BE-24/R5** container bind + Render staging proof. Needs:
  staging deploy approval (blueprint corrected, auth/AI vars added).

## NOT_VERIFIED

- **DC-22** provider quotas + web-linked claims. Needs: network +
  owner re-confirm (ZERO_COST §B).

## NOT_APPLICABLE (documented non-defects)

- **BE-18** shutdown handlers / per-route timeouts (uvicorn default;
  stateless demo). **EN-21** multiprocess writes (single worker).
  **EN-28** PG pooling/cutover (explicit future work). **EN-40**
  `.gitkeep` (placeholder by design).

## Watch items (not gaps)

- One transient vitest failure in run 1 of 2 (261/261 on rerun;
  new tests green in both). CI watch; cause unidentified (no repro).
- **DC-20** logo rights (Q-IP-1) still owner-asserted only.
