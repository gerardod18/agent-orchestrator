# What CodeRabbit flags in these PRs (115 inline findings, 30 PRs, Nov 2026)

Evidence, not its prompt. Labels: Functional Correctness 78, Data Integrity & Integration 18, Security & Privacy 7, Stability & Availability 7, Maintainability 3, Performance 2. Severity: Minor 78, Major 37. Effort: Quick win 91, Heavy lift 24. Location: backend 94, web 18, tests 2. Hot files: the Copilot review/approval tools and writers (`review.ts`, `schedules.ts`, `songs.ts`, `archiveSpots.ts`, `storeAdmin.ts`, `read.ts`, `write.ts`, `prompt.ts`). Hunt functional bugs first; skip style. The bot also reports "outside diff range" findings: read the unchanged code your change depends on.

For each hunk: read callers, callees and validators, state the claim the code or its comment makes, then try to break it.

## 1. Approval display and identity (33)
Cues: a preview, summary, label or fingerprint built from truncated, sliced or example data; `.slice`, `.substring`, `take`, `join` on a displayed string; a name used where an id is needed; a list of N items shown with fewer.
Break it with: label of 200+ chars, duplicate names, nine items shown as eight, renamed or removed items, offsets, exceptions, source rule, UTC time.
Title templates: "Keep <reason/time/total> when <label> is long." · "Include <source rule> in <row> identity." · "Block <confirm/rollback> when the review omits changes." · "Show the total when names are truncated." · "Flag omitted positions."
Check: every added, removed, changed and renamed field represented; stable identity, not display name; preview output accepted by the writer's input validator (round trip).

## 2. Workflow and dependency integration (27)
Cues: a changed shape, key or option; a new field; a tool or prompt change; a React Query key; a persisted value read back later.
Break it with: another caller, a second validator, a serializer, a cache key without the workspace id, a persisted record missing the new field, a prompt that offers a tool the policy hides, a sibling uploader, unmount and cancellation.
Title templates: "Add <field> to both <validator>s." · "Add the workspace corporation to the review query key." · "Normalize persisted targets that omit <field>." · "Scope <tool> so it does not conflict with <other tool>." · "Gate <A> and <B> separately."
Check: grep every consumer of the changed symbol; compare siblings of the same shape.

## 3. Errors and recovery (18)
Cues: `try/catch`, `.catch`, a fallback, a status mapped from an error, a write followed by a read, audit or response.
Break it with: authorization denial, scope loss mid-run, malformed JSON, transient failure, a failure after the write committed, every item failing, duplicate input.
Title templates: "Map <denial> from pre-write reads to <coded error>." · "Restrict the fallback to recognized <missing-x> errors." · "Do not classify every <query> failure as <not found>." · "Convert malformed <input> JSON to a domain error." · "Preserve per-item reasons when every mutation fails."
Check: each failure phase has its own honest outcome; unrelated errors propagate.

## 4. Bounds, pagination and search (14)
Cues: `.take(`, `limit`, a cursor, `filter` after a scan, a loop over owners, a union of capped lists, tokenization of search terms.
Break it with: N-1 / N / N+1, limit applied before merge or dedupe, a budget not shared across a loop, parent reads not counted, archived owners counted, an end cursor, a term that is empty after punctuation is stripped.
Title templates: "Apply the <N>-item limit after merging <lists>." · "Share one <read> budget across the loop." · "Bound <cursor> on <history> pages." · "Replace the filtered scan with an indexed lookup." · "Report unread impact when the limit is exceeded."
Check: truncation is reported, with a continuation or an honest blocker; totals match what is shown.

## 5. Transaction freshness (11)
Cues: a preview then a confirmed write; a digest, hash or `expected*` argument; a tool-layer recheck before a shared writer.
Break it with: a member added to an inherited set, equal counts with different membership, a state change between recheck and commit, the already-published or already-done path.
Title templates: "Include <resolved membership/inherited identities> in the <digest>." · "Pin the reviewed <set> when <writing>." · "Check reviewed <state> inside the writer." · "Handle the digest on the <alreadyDone> path."
Check: the exact identity set is validated inside the transaction; the race test mutates between recheck and commit.

## 6. Authorization and disclosure (8)
Cues: a name, count or error string returned; an `expected*` comparison; a lookup helper; history or retired records.
Break it with: no read permission, revoked scope, renamed or deleted target, a comparison done before the access check, today's name used to redact an old one.
Title templates: "Check <access> before returning a stored <name>." · "Redact <inaccessible> target names." · "Move the <expected> check after the access checks." · "Bind <tool> to the selected workspace."
Check: the whole response (errors, blockers, history), not only the primary object, honors permissions; backend check, not a UI guard.

## 7. Validation and documentation (4)
Cues: a comment or doc stating behavior; a test with fixed counts; formatting.
Title templates: "Update the stale statement about <x>." · "Make the list checks independent of the account count." · "Fix the formatting failure."
Check: comments match the code; lint and format pass; tests do not depend on ambient data.

## Cues added from the replay (misses on PRs 264 and 272)
- **Joined comparison:** a list compared via `join('\n')`/`join(',')` of names that may contain the separator. Compare element by element. (264)
- **Update guard vs archived/inactive state:** a guarded update checks `revision` but archive or deactivate does not bump it. Re-check the active state inside the writer. (264)
- **Truncated change list on a confirmation card:** `changeCount > changes.length` with `blocked: null`. Block or show everything before confirming. (272, Major)
- **Basis narrower than the card:** the card shows title/artist/labels but the guarded basis stores only status. Every displayed field the user relies on must be in the basis the writer re-checks. (272, Major)
- **Redaction by type permission only:** a helper reveals a name when the caller has `<thing>:read` without checking operational scope or that the target is within the caller's reach. (272)
- **Writer throws plain `Error`, caller maps coded errors:** the caller's fallback then replaces the real reason. Throw the coded error the mapper recognizes. (272)

## Replay baseline (Nov 2026, blind reviewer at first-pushed commit, 14 tool calls each)
Bot first-round findings: 7. Caught 1 fully (committed result lost when the follow-up read fails) and 1 partly (revision not bumped by a related change). Missed 5, including both Major ones. Recall about 15-30%. One extra finding (the already-published digest path) matched a bot finding on stacked PR 271. Reviewers stopped far under budget and cleared the status-only guard as fine, which is exactly what the bot flagged. See the enumerate-before-concluding rule in `pre-review`.

## Test quality (summary findings)
A guard needs a test that fails without it, for the same wrong reason. Past misses: a race injected before the recheck, punctuation that never reached the empty-query branch, fixtures lacking the meaningful tags, a generic "throws" assertion.

## Improving recall
After each PR, add every bot finding the pre-review missed as a cue and a title template here. Do not paste the list into other prompts.
