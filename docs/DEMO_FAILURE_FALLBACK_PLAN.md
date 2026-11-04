# DEMO FAILURE FALLBACK PLAN

| Failure | On-screen line | Continue with |
|---------|----------------|---------------|
| AI API down/quota | "Live AI is unavailable; the deterministic case stands on its own." | Stored assessment (labelled STORED) or rules+evidence only |
| Backend unreachable | "Backend is warming up (free-tier cold start)." | Wait ≤60 s, retry; narrate scores from rehearsal notes — labelled as such |
| Graph/WebGL fails | "3D unavailable here; the relationship table carries the same data." | graph-table component |
| Login fails | "Demo credentials are rotated; switching to a rehearsal capture if one was pre-recorded." | Owner pre-recorded segment, disclosed (none exists yet) |
| Network drops | "Connectivity lost; showing a rehearsal capture if one was pre-recorded." | Same, disclosed |

Never: fake a live result, hide a failure, or show a
fallback as the live path. Every branch keeps the
deterministic scores and evidence visible.
