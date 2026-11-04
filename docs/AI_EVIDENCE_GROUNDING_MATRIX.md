# AI EVIDENCE-GROUNDING MATRIX

| Control | Mechanism | Test |
|---------|-----------|------|
| Supplied-facts-only prompt | SYSTEM_INSTRUCTION + schema spec | test_ai_validation.py |
| Evidence-ID allowlist | sent_ids set; unknown ID → INVALID | validation tests |
| No invented scores | BANNED_SCORE_FIELDS reject | validation tests |
| No enforcement language | ENFORCEMENT_PHRASES reject | validation tests |
| Human approval required | requires_human_approval=true enforced | validation tests |
| Follow-up injection fence | <<<ANALYST_QUESTION delimiters + sentinel neutralizing | hostile tests |
| Prior-analysis distrust | prior context labelled untrusted | follow-up tests |
| Truncation/refusal honesty | finish_reason=length/refusal → explicit errors | provider-body tests |
| Score authority | engine never consumes AI output | boundary tests |
| Stale-run honesty | failed runs never shown as fresh success | failed-run tests |

Result: every grounding claim has a rejecting test. PASS.
