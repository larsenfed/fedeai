# Agent Routing Contract

Use this deterministic routing flow for every inbound Telegram message.

## 1) Explicit command wins

If the message starts with one of these prefixes, route immediately:
- `/health`, `/food`, `/weight` -> `health`
- `/generic`, `/default` -> `generic`
- `/linkedin`, `/post` -> `linkedin-writer-template`

If the selected agent is disabled, explain that it is disabled and fall back to
`generic`.

## 2) Classify by intent keywords

If no explicit command was used, classify by keyword hits from
`agents/registry.yaml`.

Numeric override:
- If the message contains a weight-like value (for example `77.7 kg`, `77kg`,
  `weight 77.7`, or `weighed 77.7`), route to `health` even if no other
  keyword matches.

Routing rules:
- Route to the highest-priority enabled agent with at least one keyword hit.
- If no hits are found, route to `default_agent` (`generic`).

## 3) Media-aware override

When a voice note or audio file is present:
- If user mentions LinkedIn/post/article intent, route to
  `linkedin-writer-template` (if enabled).
- Otherwise route to `generic` and ask one short disambiguation question if
  needed.

## 4) Ambiguity handling

When two enabled agents are plausible and confidence is low:
- Ask one short question: "Do you want health tracking or general assistance?"
- Do not ask more than one clarification question before taking action.

## 5) Execution model

- Route first, then apply only the selected agent's scope and tone.
- Do not blend health coaching behavior into generic responses.
- Keep response language based on user preference unless the user asks to switch.
