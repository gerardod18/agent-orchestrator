---
name: implement
description: Spec-first, test-driven implementation of a ticket, spec, or fix. Use when asked to build a feature, fix a bug, or implement a ticket. The dev-team-implementer agent preloads this skill; an orchestrator never runs it itself, it dispatches that agent.
---

# Implement: spec first, then tests, then code

One procedure for all code changes. Spec-driven development decides *what* to build; TDD proves it works. Skip the spec step only for typos and isolated presentation changes.

**Orchestrators:** if you are a Lead or parent coordinating a team, do not run this skill. Dispatch `dev-team-implementer` with the criteria. You never write the code, including fixes for review comments.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting.

## 1. Spec (short, 1 page max)

Inside dev-team, the approved spec from the Specs role is the spec: consume it, do not rewrite it or its criteria. Standalone, write a lean spec to `~/claude-plans/<repo>/<ticket-or-slug>/spec.md` (never in the repository):

- **Goal and exclusions**: one paragraph, plus what is out of scope.
- **Acceptance criteria**: observable behavior, one line each.
- **Invariants**: what must stay true (authorization, freshness, bounds, identity, ordering).
- **Consumers**: callers, validators, serializers, caches, background paths, sibling implementations that the change touches. Discover them by search; do not trust a list you were handed as complete.
- **Failure cases**: validation denial, authorization denial, stale approval, transient failure, committed-but-response-lost, post-commit side-effect failure, as applicable.
- **Seams**: the public boundaries where tests go (see below).

For risky areas (approvals, transactions, pagination, authorization, errors, async lifecycle), read `~/.agents/skills/code-review/references/stateful-review.md` and write down one counterexample per applicable invariant before coding. Keep the spec lean: long specs make agents lose the thread.

Ask the user only when a material product decision is unresolved. Do not ask for approval of seams, test names, or routine choices.

## 2. Tests from the spec (red → green)

Every test traces to a criterion, invariant, or failure case. Work in vertical slices: one seam, one test, one minimal implementation, repeat. Never write all tests first.

- **Red before green.** Write the failing test, watch it fail for the *right* reason, then write only enough code to pass.
- **Seams:** infer them from the ticket, repository contract, and existing tests. Test through public interfaces, never internals. Ask only when choosing between product-visible interface behaviors.
- **Prove the guard.** For each guard or invariant, the test must fail without it. Note in one line why. A test that passes on any thrown error proves nothing: assert the specific code, the absence of sensitive data, and the absence of side effects. A race test must mutate state *between the tool recheck and the commit*, not before the recheck.
- **Boundaries:** N-1 / N / N+1, deduplicated unions, total reads across a shared budget, empty-after-normalization input.
- **Independent expected values:** from a literal, a worked example, or the spec, never recomputed the way the code does.
- **Anti-patterns:** implementation-coupled mocks, tautological assertions, horizontal slicing. See [tests.md](tests.md) and [mocking.md](mocking.md).

When the interface shape itself is in question, read `~/.agents/skills/api-and-interface-design/SKILL.md` (on-demand only).

## 3. Refactor under green

After the tests pass, small behavior-preserving cleanups of the code you just wrote are allowed, with tests green before and after. No unrelated cleanup. Independent review follows separately.

## 4. Sibling sweep and verification

Pattern self-check (Tier 0 of `pre-review`, cheap): read `~/.agents/skills/code-review/references/coderabbit-patterns.md` and, for each pattern whose cues appear in your diff, try its "break it with" cases against your code. Fix what breaks. This is authoring discipline, not a review; the independent pass is separate.

Before reporting: for each defect you fixed, search for the same root cause at other call sites and in sibling implementations, and fix or list them. Run typecheck regularly, single test files regularly, and the full agreed gate once at the end. Report exact changed paths, commands with exit codes, seams covered, the invariant-to-test mapping, and anything not verified.

## 5. Hand-off

- **Inside dev-team or PR follow-up:** stop here. Return the snapshot to the parent. Never self-review, commit, or push; the parent dispatches independent Standards and Spec reviews and the Publisher.
- **Standalone:** run `pre-review` first, then `code-review` (both axes, independent), then the `commit` skill and, per shared policy, `create-pr`. They handle branch name, Linear ticket, conventional commit and PR body.
