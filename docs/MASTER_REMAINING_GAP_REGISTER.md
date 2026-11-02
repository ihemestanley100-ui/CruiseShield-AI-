# MASTER REMAINING GAP REGISTER

| ID | Gap | Severity | Owner | Closure test |
|----|-----|----------|-------|--------------|
| G1 | Live AI quota-spend approval | HIGH | Owner | 1 approved call observed 200 + validated + persisted |
| G2 | Commit + push of J3–judging work | HIGH | Owner | staged manifest approved → commit → push verified |
| G3 | Staging deployment + proof (R5) | HIGH | Owner | live URL passes acceptance checklist |
| G4 | Neon live cutover | MEDIUM | Owner | migration on Neon + reconcile OK + rollback tested |
| G5 | Real owner backup | MEDIUM | Owner | archive at approved destination, hashes verified |
| G6 | CSP (Three.js inline) | MEDIUM | Dev+Owner | policy shipped without breaking 3D, or accepted risk |
| G7 | Container image build | LOW | Dev/CI | docker build + boot + /health green |
| G8 | Browsers/AT/real devices (FE-35) | MEDIUM | Owner env | matrix run on real browsers + reader |
| G9 | OSV vuln lookup | LOW | CI | pip_audit online green |
| G10 | Meta quota/billing terms | MEDIUM | Owner | account page/keyword recorded |
| G11 | Pages next-on-pages adapter | MEDIUM | Dev+Owner | adapter configured + preview deploy green |
| G12 | Portal: acceptance/rules/track/video/submit | HIGH | Owner | receipts filed; video recorded+uploaded |
| G13 | Logo rights memo (Q-IP-1) | MEDIUM | Owner | memo filed |
| G14 | Pilot partner + metrics | LOW | Future | pilot run per measurement framework |

No CRITICAL gap is hidden: every BLOCKED/NOT_VERIFIED item
across J3–J10 maps to one row above.
