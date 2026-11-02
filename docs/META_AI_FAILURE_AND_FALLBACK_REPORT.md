# META AI FAILURE AND FALLBACK REPORT

| Failure | Code | User-visible outcome | Test |
|---------|------|----------------------|------|
| Key absent | MODEL_NOT_CONFIGURED | 503 + setup hint, deterministic data intact | hermetic tests |
| Timeout 30 s | MODEL_TIMEOUT | 503 + retry guidance | timeout tests |
| Rate limited | MODEL_RATE_LIMITED | 429 + backoff note, audited | 429 tests |
| Bad credentials | MODEL_AUTH_FAILED | 503, no key detail leaked | auth-fail tests |
| Provider 5xx/down | MODEL_PROVIDER_ERROR/UNAVAILABLE | 503 + fallback panel | failure tests |
| Non-JSON body | MALFORMED_RESPONSE | 503, run persisted FAILED | body tests |
| Truncated | MODEL_RESPONSE_TRUNCATED | 503, never partial-as-final | truncation tests |
| Refusal | MODEL_REFUSED | 503 with refusal excerpt | refusal tests |
| Bad schema/refs | MODEL_OUTPUT_INVALID | 503 + problem list | validation tests |
| Daily cap | (429) | audited 429, resumes next UTC day | cap tests |

Fallback chain: live → structured-compat retry → explicit
error + deterministic risk/evidence remain fully usable →
last stored assessment shown ONLY labelled as stored, never
as the fresh result. No silent degradation anywhere. PASS.
