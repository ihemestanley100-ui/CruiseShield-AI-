# PHASE 13 — RULES AND ELIGIBILITY MATRIX

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 13 | DATE: 2026-11-01 | HEAD: 0eaaaf5 (no commit/push)
METHOD: official event page fetched 2026-11-01 (see sources); full Official Rules text NOT retrievable (JS-rendered waiver page). Prior repo-only matrix superseded by this one wherever official text now exists.

## Sources (checked 2026-11-01)
- S1 OFFICIAL: https://cerebralvalley.ai/e/meta-ai-developer-hackathon (Meta + Cerebral Valley event page) — dates, tracks, themes, caps, exclusions.
- S2 PRESS (third-party): madrobot.blog 2026-10-25 update — reports official-rules contents (prizes, scoring weights, ownership/licence, 18+, one track, one representative). Credible but NOT the rules text.
- S3 PARTICIPANT CLAIM (unverified): github.com/sholaola23/meta-hackathon-2026 — paraphrases in-window-only demo, public repo + video link + team members. Working assumption only.
- S4 PRIOR: repo audits (baseline T1/T2/T3, contribution register C-01…C-14, security audits).

## Official facts now established (S1)
- Event: Meta Global AI Developer Hackathon, virtual, Oct 26 – Nov 4, 9:00 PM ET (S1). Projects due by 9pm ET Nov 4 (S2 corroborates).
- Tracks: Indie developer (individuals/students; creativity, technical ambition, works) / Startup (teams/founders; execution, production). One track per project (S1+S2).
- Themes: "Build for Your World" (firsthand problem) / "Push the Frontier" (S1).
- Cap: 20,000 selected applicants, rolling review; applications closed Oct 25 11:59 PM ET (S1).
- Geography: worldwide EXCEPT sanctioned/embargoed locales (Belarus, China, Russia, Ukraine, Syria, Crimea/Donetsk/Luhansk, Cuba, North Korea, Iran) + Meta/CV staff/households (S1). Nigeria is NOT excluded.
- Models: Muse Spark series, Muse Wonder, Muse Image, SAM 3.1 via Meta Model API; "code faster with Muse Code coding agent" — AI-assisted coding explicitly welcomed (S1).
- Full Official Rules: published on sign-up page ~Oct 25 per S2; not retrievable here (waiver page JS-only). MUST be read+accepted by the participant (S1).

## Rules matrix (R-01…R-14 against best available sources)
| # | Requirement | Evidence | Status | Missing / action |
|---|---|---|---|---|
| R-01 | New work only | Greenfield-in-window (T1/T2/T3); sole pre-event artifact = V5.0 spec text (disclose); S3 claims in-window-only demo | PASS_WITH_LIMITATIONS | Official new-work clause text; Q-REUSE-1, Q-NEW-1 stand |
| R-02 | Identifiable team contributions | C-01…C-16 with file/mtime/commit evidence | PASS_WITH_LIMITATIONS | Roster; commit-hardening (owner decision) |
| R-03 | Public repository | Remote set, 3 commits pushed; S3 claims public repo required | PARTIAL | Confirm via portal/rules (Q-REPO-1); selective push (owner) |
| R-04 | Max four members | Single git identity (not team evidence) | NOT_VERIFIED | Q-TEAM-1 |
| R-05/R-06 | Track (Indie) | No in-repo record; product fits Indie ("individual builder, works") | NOT_VERIFIED (owner confirms) | Q-TEAM-2 |
| R-07 | One submission | Nothing submitted | PASS_WITH_LIMITATIONS | Confirm at submit |
| R-08 | Demo video | Script/storyboard/checklist done; video NOT recorded | PARTIAL | Record+upload (owner). S2: demo+video = 25% of score |
| R-09 | Legal/ethical | Synthetic-only, advisory AI, human authority | PASS_WITH_LIMITATIONS | Full rules legal review (owner) |
| R-10 | Platform policy | Documented Meta endpoint, server-side key, no abuse | PASS_WITH_LIMITATIONS | Meta terms review |
| R-11 | Rights to code/assets | Code greenfield; deps declared; logo UNVERIFIED; psycopg LGPL note | PARTIAL | Q-IP-1 (logo), Q-IP-2 (marks). S2 ownership clause raises stakes |
| R-12 | Theme alignment | "Build for Your World" (S1 theme text matches firsthand-problem framing) | PASS_WITH_LIMITATIONS | Confirm selection in portal |
| R-13 | Acceptance status | Nothing in repo; S1: notifications by 9am ET Oct 26 | NOT_VERIFIED | Owner checks email/portal (R-13) |
| R-14 | Deadline/portal | S1: due Nov 4 9:00 PM ET; portal = Cerebral Valley page | PASS_WITH_LIMITATIONS | Confirm submission fields/upload mechanics in portal (Q-SUB-2) |

## Organizer/owner clarification list (narrowed)
Q-REUSE-1 (spec-as-prior-work?) · Q-NEW-1 (uncommitted OK?) · Q-TEAM-1/2 (team+track) · Q-REPO-1 (public+push-by date) · Q-SUB-1/2 (artifacts+fields) · Q-IP-1 (logo) · Q-IP-2 (marks) · R-13 (acceptance) · LGPL/psycopg distribution note.
Note: several are now answerable from the full Official Rules text / portal directly (owner-side read), not necessarily requiring organizer contact.

## Bottom line
Eligibility posture improved from "no rules on file" to "official event terms verified, full rules text pending owner-side read". Verdict: ELIGIBILITY_AT_RISK_REQUIRES_ORGANIZER_CLARIFICATION is unchanged in NAME but narrowed in SCOPE (acceptance + full-text review + video + push decisions remain).
