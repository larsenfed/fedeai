---
name: morning-weigh-in
description: Manage daily morning weigh-ins with reminders and scale photo analysis.
version: 1.0.0
---

# Morning Weigh-in

## When to trigger
- Daily cron at 07:00 local time.
- User sends a scale photo or mentions weigh-in.

## Flow
1. If reminder: send "Good morning. Time for weigh-in. Send me a photo of the scale."
2. If a photo is received:
   - Extract exact weight with OCR + vision.
   - Record date and weight.
   - Compare against previous entries (weekly trend).
   - Give motivating feedback and projection to target.

## Logging format
- Save: Date | Weight (kg) | Difference vs previous entry | Note
- Update persistent data through `food-logger/scripts/nutrition_tracker.py`.
- Use direct command execution, for example:
  `python3 skills/food-logger/scripts/nutrition_tracker.py add-weight --weight 77.7 --date 2026-04-30 --notes "Recorded via assistant"`
- Do not use `sessions.resolve` / `sessions_send` for weigh-ins.
- Do not use `write` or `edit` for weight logs.
- Canonical output file: `~/.openclaw/agents/main/food-logger/data/nutrition/weight_log.csv`.

## Example response
"Weight logged: 85.4 kg (-0.3 kg vs previous entry).
Weekly trend: -1.1 kg. You are on track toward your 73 kg target."
