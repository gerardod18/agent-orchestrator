---
name: export-markdown-to-codex
description: Export Markdown files to the user's personal Codex documents folder. Use when the user asks to export or save general Markdown content to Documents/Codex. Not for plans, handoffs or reports, which go to `~/claude-plans/<repo>/`.
---

# Export Markdown to Codex

Save general Markdown exports under `$HOME/Documents/Codex` unless the user chooses another location. Plans, handoffs, and reports follow the user policy: `~/claude-plans/<repo>/`. Do not make a second copy in Documents/Codex for those artifacts.

- Create `$HOME/Documents/Codex` if it does not exist.
- Infer a concise, descriptive filename ending in `.md` when the user does not provide one.
- Preserve the requested content and Markdown structure.
- Do not write the export into the active repository.
- Do not overwrite an existing file unless the user explicitly requests replacement. Choose a clear unique filename when necessary.
- Return a clickable absolute path to the created file.
