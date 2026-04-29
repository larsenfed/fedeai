---
name: health-visualizer
description: Generate visual charts for macro distribution and weight history using food and weight CSV logs.
version: 1.0.0
user-invocable: true
---

# Health Visualizer

## When to use this skill
- User asks for macro percentages, macro split, or calorie/macronutrient distribution.
- User asks for a chart/graph/plot of weight trend or weight history.

## Execution instructions
1. For macro distribution requests, run:
   - `python3 skills/food-logger/scripts/health_charts.py macro-pie --days <N>`
2. For weight trend requests, run:
   - `python3 skills/food-logger/scripts/health_charts.py weight-timeseries --days <N>`
3. Send the generated PNG image back to the user.
4. Add a short caption with 1-3 bullet points:
   - selected period
   - key metric (latest weight or dominant macro)
   - one concise coaching insight

## Rules
- Prefer chart-first response over text tables for chart requests.
- If no data exists, explain what entries are missing and how to add them.
- If chart generation fails due to missing matplotlib, ask to install it:
  - `pip3 install matplotlib`
