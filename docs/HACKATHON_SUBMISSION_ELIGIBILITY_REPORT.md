# HACKATHON SUBMISSION ELIGIBILITY REPORT

READ-ONLY audit evidence. SCOPE LIMIT UP FRONT: no official hackathon rules
were found in this repository (searched `docs/`, `README.md`, blueprints
for rules/eligibility/organizer/Devpost/deadline/judging text — zero hits),
and no rule text was supplied with this audit request. This report therefore
reviews evidence fitness per topic and lists the questions organizers must
answer. **It makes no eligibility decision.**

## 1. Existing-codebase reuse

- Evidence supports a greenfield in-window build: T2 baseline record (repo
  did not exist on 10-28 morning; only 2 spec files), T1 commits all 10-28,
  all other work Oct 28–31 (see baseline + register reports).
- Sole pre-event artifact: the V5.0 blueprint text (mtime 10-08).
  RECOMMENDATION: disclose it as pre-existing input; it is a specification,
  not code, and no pre-event code exists.
- Q-REUSE-1: does a pre-existing written specification count as
  pre-existing work under the new-work rule, or only code/assets?

## 2. New-work requirement

- 14 contribution groups (C-01…C-14) document in-window creation with
  commit or mtime evidence; live Meta execution evidenced 10-29 (4
  doc-reported runs), 10-30 (2 persisted runs), 11-01 (1 fully-observed
  run, full artifact retained outside the repo).
- WEAKNESS (unchanged 11-01): all post-Oct-28 work is UNCOMMITTED
  (HEAD still `0eaaaf5`, 85 changed/untracked entries), so timestamps
  rest on filesystem mtimes (T3, mutable) rather than commits. Consider
  committing (user decision only — this programme made no commits) to
  harden provenance.
- Q-NEW-1: is uncommitted-but-timestamped work acceptable, or must new
  work be committed/pushed during the window?

## 3. Team and track

- No team roster, team size, track selection, or individual-vs-team status
  exists anywhere in the repo. Git authorship shows a single identity
  (`CruiseTech Dev`), which is not evidence of team composition.
- Q-TEAM-1/2: confirm team rules and the correct track; record both in the
  submission (cannot be derived from the repo).

## 4. Public repository

- Remote `origin` points at GitHub (`ihemestanley100-ui/CRUISESHIELD-AI-`);
  the 3 baseline commits are pushed (HEAD == origin/master); all later
  work exists only locally. Public/private visibility is NOT verifiable
  from inside the repo, and this audit changed nothing about visibility.
- Q-REPO-1: is a public repo required, and as of what date must the full
  submission state be pushed?

## 5. Submission and video

- PARTIAL 11-01: 3-minute script + storyboard + recording checklist +
  backup sequence now exist (`HACKATHON_FINAL_DEMO_SCRIPT.md`); the
  video itself is NOT recorded (user step). No submission package
  assembled; app never deployed (no public URL).
- Screenshots exist (`%TEMP%\smoke32f`, `%TEMP%\smoke33`: 23 real
  headless-Edge renders from 11-01 — 8 retest + 15 VQA, individually
  verified) but live OUTSIDE the repo in
  ephemeral temp dirs — preserve the set into the repo (user decision)
  before submission if screenshots are required.
- Q-SUB-1/2: confirm required artifacts (video length/content, live URL
  vs local demo, write-up format) and the exact deadline/timezone.

## 6. Intellectual property and assets

- Code: no third-party code reuse detected; OSS deps declared (see
  provenance report). V5.0's references to Frontier/CruiseTech IP are
  not present as code — disclose the reference, claim no ownership.
- Logo: `cruiseshield-logo-original.png` source UNVERIFIED (see
  provenance report; now 1273370 B high-res + one byte-identical
  double-extension duplicate flagged for removal). Developer asserts it
  is their original — assertion recorded, not independently verified.
  Q-IP-1: confirm the logo's owner/creator and that
  the team holds rights to use it in the submission (and whether
  organizer/press reuse is granted).
- "Meta", "Muse Spark", model IDs appear as integration facts + displayed
  provider labels, not as endorsement claims. Q-IP-2: confirm any
  trademark-attribution requirements for Meta marks in the submission.

## 7. Organizer-clarification checklist (consolidated)

Q-REUSE-1 (spec-as-prior-work?) · Q-NEW-1 (uncommitted work OK?) ·
Q-TEAM-1/2 (team + track) · Q-REPO-1 (public + push-by date) ·
Q-SUB-1/2 (artifacts + deadline) · Q-IP-1 (logo rights) · Q-IP-2 (marks).

## 8. Readiness summary (evidence fitness, not a ruling)

| Topic | Standing |
|---|---|
| Greenfield-in-window build | SUPPORTED (T1+T2+T3) |
| Meta AI genuinely integrated + executed live | SUPPORTED (incl. fully-observed 11-01 run) |
| Secrets hygiene / synthetic-only data | SUPPORTED (re-verified 11-01) |
| Commit-hardened provenance for all new work | WEAK (uncommitted) — user decision |
| Logo rights | UNVERIFIED — must confirm |
| 3-minute script / storyboard / checklist | DONE 11-01 (video itself NOT recorded) |
| Submission package / deployment | NOT DONE |
| Rules-verified eligibility | BLOCKED — no rules on file |

Next step after this audit: obtain written answers to Q-*-* from the
organizers (or the official rules text for a follow-up review), then
decide on commit/push, logo confirmation, video production, and packaging.
STOP: audit deliverables complete; no code, history, visibility, data, or
secrets were touched.
