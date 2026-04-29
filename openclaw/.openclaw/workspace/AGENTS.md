# AGENTS - Workspace Operating Rules

This workspace must support multiple agent use cases. Do not hardcode a single
name, language, or domain in global rules.

## General behavior
- Use the response language from `config/agent_profile.yaml` (`response_language`).
- Confirm image reception and provide immediate feedback.
- Never invent measurements: use image output, persisted records, or ask follow-up.
- Use vision tools whenever an image is provided.

## Agent routing
- Route by intent using `agents/registry.yaml`.
- Enforce deterministic dispatch defined in `agents/ROUTING.md`.
- Keep health tracking isolated in `agents/health/`.
- Keep all non-specialized tasks in `agents/generic/`.
- If intent is unclear, ask one short clarifying question before acting.

## Scheduling
- Daily reminders and check-ins must be configured in profile config, not hardcoded here.
- Any automated schedule should include timezone-aware timestamps.

## Storage
- Persist logs and summaries in agent-specific paths under `agents/main/<agent-id>/`.
- Store structured nutrition data through `skills/food-logger/scripts/nutrition_tracker.py`.
- Name image files with `YYYY-MM-DD_HHMM_<type>.jpg` for deterministic sorting.

## Workspace structure
- `agents/health/`: nutrition, weight, and fitness coaching.
- `agents/generic/`: general assistant profile for everything else.
- `agents/linkedin-writer-template/`: scaffold for LinkedIn article generation from audio notes.
- `agents/ROUTING.md`: deterministic routing contract used at message ingress.
- `skills/`: reusable capabilities shared across agents.
- `skills/health-visualizer/`: chart generation for macro distribution and weight trends.

## Security and scope
- Respect per-agent scope configured in profile config.
- If a request is out-of-scope for the active agent, hand off to a general assistant profile.

