# What CodeRabbit flags here (from 115 root comments on 30 PRs)

Use for the pre-push pass. Findings are review attention, not severity, and the same defect often repeats across PRs. Label mix: Functional Correctness 78, Data Integrity & Integration 18, Security & Privacy 7, Stability & Availability 7, Maintainability 3, Performance 2. Severity: 78 Minor, 37 Major. 91 were Quick wins, 24 Heavy lifts. So: hunt functional bugs first; do not spend the pass on style.

| Pattern (inline roots) | Ask of every change | Typical miss |
|---|---|---|
| Approval display and identity (33) | Does the preview cover every added, removed, changed and renamed field with a stable identity, not only a name? Does preview output round-trip into the writer's accepted input? | One omitted field fixed per round; long or duplicate names clip the reason; display name used as identity |
| Workflow and dependency integration (27) | Who else calls, validates, serializes or caches this? Sibling uploaders, background paths, workspace switch, unmount, cancellation? | Contract changed in one layer, validator or sibling path left behind |
| Errors and recovery (18) | Which phase failed: validation, authorization, stale approval, transient, committed-but-response-lost, post-commit side effect? Is each mapped honestly? | Catch-all turned into "not found"; authorization denial swallowed; success reported after a post-write failure |
| Bounds, pagination, search (14) | N-1 / N / N+1; combined caps across unions; total dependent reads; continuation when truncated; empty-after-normalization input | Individually bounded lists whose union is not; truncation without a continuation |
| Transaction freshness (11) | Is the expected state validated inside the transaction over the exact identity set, not just rechecked in the tool layer? Does the race test mutate between recheck and commit? | Digest of counts or examples; race injected before the recheck |
| Authorization and disclosure (8) | Are names, errors, history and lookups protected, not only the main object? Is anything compared before authorization? | Redacted list but names in blocker errors |
| Validation and documentation (4) | Does a comment or doc claim something the code no longer does? | Comment says reason is kept; slice drops it |

Test-quality check on every guard: would this test fail without the guard, for the same wrong reason? Generic "throws" assertions, fixtures missing the meaningful tags, and punctuation that never reaches the empty branch all passed review before.

CodeRabbit labels findings `<severity> · <category> · <effort>`. Mirror that in the pre-review ledger so findings compare one to one with the bot's.
