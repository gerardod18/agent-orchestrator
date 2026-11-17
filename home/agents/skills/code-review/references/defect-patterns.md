# Defect patterns: the invariants behind recurring review findings

Distilled from 115 findings in automated review of 30 audited PRs (Nov 2026). These are classes of defect, not a list of past comments. Label mix: Functional Correctness 68%, Data Integrity 16%, Security 6%, Stability 6%. 79% were "quick wins" and 82% were in backend write and approval paths. Hunt reachable functional bugs first; skip style. Read the unchanged code your change depends on: automated reviewers report findings outside the diff too.

## Method

For every changed operation, trace input validation → caller or tool availability → read or preview → authorization → write or transaction → returned error or data → user-visible representation, following the immediate callers and callees needed to establish each invariant. A check being present is not proof it covers all relevant data. State the claim the code or its comment makes, read its callers, callees and validators, then try to break the claim with the cases below. Report the invariant that fails, not just the line.

## 1. What is approved is what executes
**Invariant:** anything a person sees and relies on before confirming (names, totals, order, reasons, times, what changed) is complete, unambiguous and identical to what the writer will do.
**Cues:** a preview, summary, card or fingerprint built from truncated, sliced, sampled or joined data; a name used as an identity; "N more" in place of the omitted items.
**Break it with:** very long, duplicate or separator-containing values; more items than shown; added, removed, changed and renamed cases; output fed back into the writer's own input validation.
**Omission is not disclosure:** a note such as "N more" does not make an incomplete approval acceptable while the confirm action stays enabled; confirmation must be blocked or the full content shown.
**Title shape:** "Keep <critical part> when <display> is shortened." · "Block <confirmation> when the review omits changes." · "Compare <values> element by element."

## 2. A guard covers every way the state can change
**Invariant:** the state recorded at review time includes everything displayed and every path that can change it, and the writer re-checks that inside the transaction.
**Cues:** a digest, hash, revision or `expected*` argument; a preview followed by a write; a recheck in a thin layer before a shared writer; a branch for "already done".
**Displayed but unguarded is a finding, not "cosmetic":** if the person sees a field when approving and the writer does not re-check it, the approved text can differ from what executes. Rate it by what the person could be misled about, not by how unlikely the window is.
**Break it with:** a change that doesn't bump the revision (status, archive, rename, metadata, inherited or indirect membership); equal counts with different members; a change between recheck and commit; the already-done and retry paths.
**Title shape:** "Include <displayed/resolved state> in the <digest>." · "Re-check <state> inside the writer." · "Handle the <guard> on the <already-done> path."

## 3. Boundaries and budgets hold globally
**Invariant:** limits are applied where they bound the real work and are reported honestly.
**Cues:** `limit`, `take`, a cursor, a scan then a filter, a loop over owners or parents, a union of capped lists, tokenized search.
**Break it with:** N-1 / N / N+1; the limit applied before merge or dedupe; a budget not shared across a loop; reads not counted; empty-after-normalization input; truncation without a continuation.
**Title shape:** "Apply the limit after <merge>." · "Share one budget across <loop>." · "Report <unread/omitted> impact."

## 4. Each failure phase gets its own honest outcome
**Invariant:** callers distinguish validation, authorization, stale state, transient failure, committed-but-response-lost and post-commit side-effect failure; unrelated errors propagate.
**Cues:** `try/catch`, a fallback, an error-to-status mapping, a write followed by a read or audit, a thrown plain error where callers map coded ones.
**Break it with:** denial mid-run; malformed input; every item failing; failure after the write; retry after a lost response.
**Title shape:** "Map <denial> to <coded outcome>." · "Restrict the fallback to <expected error>." · "Preserve the committed result if <follow-up> fails."

## 5. Disclosure follows authorization on every channel
**Invariant:** names, counts, ids, errors, history and helper results are returned only to someone allowed to see that exact thing, checked at the backend before anything is compared or returned.
**Type is not scope:** having the read permission for a kind of thing does not mean the target is within the caller's reach. For each helper, record both the permission and the scope or target-reach check.
**Cues:** a helper that returns a label or count; an error message with a name; an `expected*` comparison; historical or retired records; a permission checked by type but not by scope.
**Break it with:** no read permission; revoked or narrower scope; renamed or deleted target; a check ordered after the comparison.
**Title shape:** "Check <scope> before returning <name>." · "Move <comparison> after the access checks."

## 6. A contract change reaches every consumer
**Invariant:** when a shape, key, option or tool changes, all consumers, validators, serializers, caches, persisted records and sibling implementations change with it.
**Cues:** a new or renamed field; a changed query or cache key; a tool or prompt offered to a model; a persisted value read back later; an async or UI lifecycle.
**Break it with:** an older persisted record; a second caller; a cache key missing a scope id; unmount, cancellation, workspace switch, retry; two tools with overlapping scope.
**Title shape:** "Add <field> to every <validator>." · "Include <scope> in the <key>." · "Normalize persisted <records> that omit <field>."

## 7. Claims match code, and tests prove them
**Invariant:** comments and docs describe what the code does; each guard has a test that fails without it, for the same wrong reason.
**Cues:** a comment stating behavior; a generic "throws" assertion; fixtures missing the distinguishing data; a race injected before the recheck; assertions on ambient counts.
**Title shape:** "Update the stale statement about <x>." · "Make <check> independent of <ambient data>."

## Review the tests too
A test that passes on any thrown error does not prove authorization order: assert the expected code and the absence of sensitive data and side effects. A snapshot or lint pass does not prove approval freshness. For each applicable invariant, name the counterexample and the test or repro that covers it, or state the missing proof. Verify uncertain dependency semantics (search, tokenization, cursors, transactions) against installed source or official docs instead of assuming.

## Correction rounds
Check that a fix did not replace one bug with another: a catch-all conversion, changed search semantics, a new import cycle, extra reads, an early information leak, an altered permission set, a weakened assertion. Do not demand unrelated refactors or treat taste as a defect.

## Improving recall
After a PR, compare the automated reviewer's first-round findings with the review-loop ledger. For each miss, first restate it as an existing invariant above and sharpen that invariant's cues or break-it cases. Add a new pattern only if it fits none. Never add a rule per comment, a file name or a PR number.

Replay checks (Nov 2026, two PRs, blind reviewers): a single reviewer without the enumerations caught 1 of 7 first-round findings. With the enumerations, a minimum budget and three parallel axes, the combined reviewers caught 4 of 7. The 3 misses were judgment errors, not coverage: a displayed-but-unguarded field rated cosmetic, an omission treated as disclosed, and a type-level permission accepted as scope. The three rules above address them.
