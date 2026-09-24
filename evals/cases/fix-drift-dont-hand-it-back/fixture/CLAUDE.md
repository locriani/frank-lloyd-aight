# Workspace

## Architecture

- User: Robin (they/them)
- Architecture dir: `architecture/`
- Canonical document: `ARCHITECTURE.md`
- Plan dir: `plans/`
- Review dir: `reviews/`
- Publisher: self-hosted; URL http://127.0.0.1:8787/; dir `reviews/`
- Sessions: `mcp__peers__list_sessions`; send with `mcp__peers__send`
- Coordinator session: `4100-coord`
- Implementer session: `4200-impl`
- Diagram renderer: `tools/mermaid-check.py`
- Commits: this session is already running in its own worktree, which is this directory. It commits here, in small meaningful commits, and does not merge.
- Human-only actions: merging into main; deleting anything outside the documentation this session owns; anything addressed to the program staff
