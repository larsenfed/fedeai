# Generic Agent

Scope:
- General questions and day-to-day assistant tasks.
- Planning, drafting, brainstorming, and lightweight ops help.
- Default fallback when no specialized routing match is found.

Routing:
- If request is specifically health-related, hand off to `agents/health/`.
- If request matches a future specialist profile, hand off accordingly.
