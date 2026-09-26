# Skills
The published collection of opinionated agent skills, generated from the agentic-coding repository and served as a Claude, Codex, and Cursor plugin marketplace. This repo has no local build or test tooling.

## Commands
| Command | Description |
|---------|-------------|
| `npx skills add nielsmadan/skills` | Install the skills into any detected agent (`--skill <name>` for one). |
| `gh workflow run sync.yml` | Trigger the render-and-commit sync by hand instead of waiting for the schedule. |

## Gotchas
- Everything under `skills/`, plus `README.md`, the plugin manifests, and the license, is rendered by `publish/sync.py` in the agentic-coding checkout. Never hand-edit them here; the source of truth is that repo.
- `.github/workflows/sync.yml` re-renders hourly (`17 * * * *`) and commits with a bot author, overwriting any local edit on the next run.
- There is no `version` field in the manifests: the version resolves to the source commit SHA, so every push is immediately available to anyone who updates.
