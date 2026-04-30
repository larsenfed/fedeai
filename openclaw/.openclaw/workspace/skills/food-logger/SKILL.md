---
name: food-logger
description: Analyze meal photos with vision, estimate calories/macros, update daily totals, and compare against health goals.
version: 1.0.0
user-invocable: true
---

# Food Logger - Meal Analysis

## When to use this skill
- The user sends a meal photo (breakfast, lunch, dinner, snack).
- The user mentions they ate and shares an image.
- You need to update daily calorie and macro intake.

## Execution instructions (follow exactly)

1. **Use multimodal vision** to analyze the image:
   - Describe visible foods with approximate portions.
   - Estimate total calories and macros (Protein, Carbs, Fat) as accurately as possible.
   - Include fiber when relevant.

2. **Persist data**:
   - Add the meal to the current daily log.
   - Update day totals for calories and macros.
   - Use `scripts/nutrition_tracker.py` to read and write data.
   - Use direct command execution (example):
     `python3 skills/food-logger/scripts/nutrition_tracker.py add-food --date 2026-04-30 --meal dinner --food "chicken salad" --calories 650 --protein 45 --carbs 50 --fat 22 --notes "Estimated from photo"`

3. **Respond to the user** (clear and motivating format):
   - Confirm the analyzed meal.
   - Show: Calories | P | C | F
   - Show daily total so far.
   - Compare with daily target/deficit.
   - Give brief coaching feedback.
   - Ask whether they want to log anything else.

## Strict rules
- Never fabricate values: rely on image evidence plus general nutrition knowledge.
- Be conservative in estimates (rounding slightly up is safer than down).
- Keep tone direct and motivating, like a coach.
- If the photo is from a scale, do not use this skill (use morning-weigh-in).
- Always keep a timestamped reference to the image.
- Never use `sessions.resolve` / `sessions_send` for food logging.
- Never write meal logs with ad-hoc files (`food.log`, `meals.csv`, etc.).
- Canonical output file: `~/.openclaw/agents/main/food-logger/data/nutrition/food_log.csv`.

## Ideal response example
**User sends breakfast photo**
-> "Breakfast logged: 3-egg omelet with spinach and cheese (~420 kcal | P:28g | C:12g | F:28g).
Daily total: 650 kcal. You have ~1250 kcal left for today's target. Great protein start."
