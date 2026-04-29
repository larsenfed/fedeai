# OpenClaw Workspace Refactor

This directory is the local source of truth for your OpenClaw setup.

## Current state
- Imported from VM backup (`vm-import/backups/openclaw-home-20260429-132118.tgz`)
- Legacy workspace is under `.openclaw/workspace`
- Initial refactor done to remove hardcoded agent identity and language

## Important findings
- VM had two gateway services:
  - system-level: `/etc/systemd/system/openclaw-gateway.service` (crash-looping)
  - user-level: `/home/federico_larsen/.config/systemd/user/openclaw-gateway.service` (healthy)
- The crash-loop was caused by running `openclaw gateway start` in system scope, which expects user systemd bus.

## Refactor direction
- Keep profile-specific behavior under `workspace/agents/<agent-id>/config/`.
- Keep skills reusable under `workspace/skills/`.
- Route intents through `workspace/agents/registry.yaml`.
- Keep global files (`AGENTS.md`, `SOUL.md`) domain-neutral.

## Current multi-agent layout
- `openclaw/.openclaw/workspace/agents/health/` for food + weight tracking.
- `openclaw/.openclaw/workspace/agents/generic/` for default assistant behavior.
- `openclaw/.openclaw/workspace/agents/linkedin-writer-template/` as a future specialist scaffold.

## Deployment model
- Preferred: git-based deploy (`git pull --ff-only` on VM, then restart user gateway service)
- Optional: rsync for emergency patching

## Release process
- One-command release from local to GitHub to VM:
  - `openclaw/scripts/release.sh "your commit message" main`
- What it does:
  - stages and commits local changes
  - pushes to `origin/main`
  - runs VM deploy (`deploy_vm_git_pull.sh`) which:
    - ensures VM repo checkout exists at `/home/federico_larsen/fedeAI`
    - pulls latest branch
    - syncs `openclaw/.openclaw/workspace/` into runtime workspace
    - restarts `openclaw-gateway.service` in user systemd context
