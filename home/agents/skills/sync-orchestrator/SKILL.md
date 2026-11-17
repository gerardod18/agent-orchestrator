---
name: sync-orchestrator
description: Reconcile the agent-orchestrator repo with the local agent folders (~/.agents skills, agent definitions, policy, hooks; ~/.claude and ~/.codex adapters). Use when the user asks to sync, back up, save, restore, or reconcile the orchestrator config, or after editing skills or agents.
---

# Sync orchestrator

The GitHub repo `gerardod18/agent-orchestrator` (local clone: `~/Documents/Github/agent-orchestrator`) keeps a sanitized copy of the user's agent configuration. `scripts/sync.py` reconciles it with the local folders. Local `~/.agents` is the source of truth for day-to-day edits; the repo is the backup and the way to restore on another machine.

## Run

1. `git -C ~/Documents/Github/agent-orchestrator pull --ff-only` (clone it first if missing: `gh repo clone gerardod18/agent-orchestrator ~/Documents/Github/agent-orchestrator`).
2. `python3 ~/Documents/Github/agent-orchestrator/scripts/sync.py status`: lists `changed`, `local-only`, `repo-only` files.
3. Decide the direction from the user's words:
   - **Save / back up / after edits** → `sync.py push` (local → repo, paths stored as `{{HOME}}`, secret scan, diagram rebuilt). Then commit and push the repo: Conventional Commit (`chore(config): sync skills and agents`, or a more specific scope), push to `main`. This repo is the user's own backup; pushing there is authorized for this skill.
   - **Restore / pull on a new machine** → `sync.py pull` (repo → local; overwritten files are backed up to `~/.agents-sync-backup/<timestamp>/`; recreates `~/.claude/skills` symlinks and regenerates Claude and Codex agent adapters).
   - **Conflict** (same file `changed` and edited on both sides): show the diff, ask which side wins. Never overwrite silently.
4. After any pull or edit of `agent-definitions/`, run `sync.py render` so `~/.claude/agents` and `~/.codex/agents` match.
5. Report: files pushed/pulled, commit SHA, and anything skipped.

## Rules

- The repo is **public**. Never copy `dev-team/profiles/` (project-specific), `settings.json` (only its `hooks` block is synced), auth files, session data, or anything the secret scan flags. If the scan refuses a file, report it; do not bypass.
- Hooks are not auto-merged on pull: show `home/claude/hooks.json` and ask before editing `~/.claude/settings.json`.
- Do not edit generated adapters by hand; edit `agent-definitions/` and render.
- After `push`, `diagram/index.html` is rebuilt from the live files. Offer to republish the artifact if the user keeps one.
