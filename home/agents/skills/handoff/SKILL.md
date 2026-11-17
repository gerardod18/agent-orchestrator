---
name: handoff
description: Write a handoff summary of current work (completed work, state, decisions,
  and next step) for another session or agent. Use only when the user asks for a handoff
  or session summary.
disable-model-invocation: true
---

# handoff

## Context (run first, read-only)
`git rev-parse --show-toplevel` · `git branch --show-current` · `git status --short` · `git log --oneline -10`

## Instructions
1. If `.agents/skills/handoff/SKILL.md` exists in the repository, use its content structure. The destination is always outside the repository (step 2).
2. Save to `~/claude-plans/<repo>/handoff-<YYYY-MM-DD>-<branch>.md`. If one exists for the same day and branch, append a timestamped section instead of overwriting it.
3. Content, at most about 60 lines:
   - Objective and Linear ticket(s)
   - Completed work (with commit hashes)
   - In progress: files and exact state
   - Decisions made and why
   - Discarded work and why
   - Concrete next step
   - Commands to verify the current state
   - Open questions
4. Write verifiable facts, not narrative. Do not include secrets or `.env` values.
5. At the end, provide the path and this resume phrase: `Read ~/claude-plans/<repo>/<file> and continue from "Next step".`
