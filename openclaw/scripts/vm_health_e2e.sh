#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_SCRIPT="${ROOT_DIR}/scripts/ssh_vm.sh"

if [[ ! -x "${SSH_SCRIPT}" ]]; then
  echo "ERROR: ssh helper not found or not executable: ${SSH_SCRIPT}" >&2
  exit 1
fi

echo "[e2e] Running VM health pipeline test..."

"${SSH_SCRIPT}" --command "python3 - <<'PY'
import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path

def sh(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

workspace = Path('/home/federico_larsen/.openclaw/workspace')
data_dir = Path('/home/federico_larsen/.openclaw/agents/main/food-logger/data/nutrition')
charts_dir = data_dir / 'charts'
weight_csv = data_dir / 'weight_log.csv'
food_csv = data_dir / 'food_log.csv'
config_path = Path('/home/federico_larsen/.openclaw/openclaw.json')
marker = datetime.utcnow().strftime('e2e-%Y%m%d-%H%M%S')

data_dir.mkdir(parents=True, exist_ok=True)
charts_dir.mkdir(parents=True, exist_ok=True)

# Validate hard guardrails in config.
cfg = json.loads(config_path.read_text())
deny = set(cfg.get('tools', {}).get('deny', []))
required_deny = {'group:sessions', 'write', 'edit', 'apply_patch'}
missing = sorted(required_deny - deny)
if missing:
    raise SystemExit(f'FAIL: missing tools.deny entries: {missing}')

# Ensure canonical CSV headers exist.
if not weight_csv.exists():
    with weight_csv.open('w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['date', 'weight_kg', 'notes'])
if not food_csv.exists():
    with food_csv.open('w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['date', 'meal_type', 'food_item', 'calories', 'protein_g', 'carbs_g', 'fat_g', 'notes'])

before_weight = weight_csv.read_text(encoding='utf-8')
before_food = food_csv.read_text(encoding='utf-8')
before_charts = {p.name for p in charts_dir.glob('*.png')}

# Run end-to-end pipeline through the production scripts.
cmd_weight = (
    f\"cd {workspace} && \"
    f\"python3 skills/food-logger/scripts/nutrition_tracker.py add-weight \"
    f\"--weight 77.65 --date 2026-04-30 --notes '{marker}-weight'\"
)
cmd_food = (
    f\"cd {workspace} && \"
    f\"python3 skills/food-logger/scripts/nutrition_tracker.py add-food \"
    f\"--date 2026-04-30 --meal dinner --food 'e2e test meal' \"
    f\"--calories 510 --protein 36 --carbs 44 --fat 19 --notes '{marker}-food'\"
)
cmd_chart1 = f\"cd {workspace} && python3 skills/food-logger/scripts/health_charts.py macro-pie --days 7\"
cmd_chart2 = f\"cd {workspace} && python3 skills/food-logger/scripts/health_charts.py weight-timeseries --days 14\"

out_weight = sh(cmd_weight).strip()
out_food = sh(cmd_food).strip()
out_chart1 = sh(cmd_chart1).strip()
out_chart2 = sh(cmd_chart2).strip()

# Validate rows were appended in canonical CSVs.
weight_rows = list(csv.DictReader(weight_csv.open(encoding='utf-8')))
food_rows = list(csv.DictReader(food_csv.open(encoding='utf-8')))
if not any(r.get('notes') == f'{marker}-weight' for r in weight_rows):
    raise SystemExit('FAIL: weight row was not written')
if not any(r.get('notes') == f'{marker}-food' for r in food_rows):
    raise SystemExit('FAIL: food row was not written')

# Validate chart files were created.
after_charts = {p.name for p in charts_dir.glob('*.png')}
new_charts = sorted(after_charts - before_charts)
if len(new_charts) < 2:
    raise SystemExit(f'FAIL: expected >=2 new charts, got {new_charts}')

# Cleanup only the e2e rows to keep dataset stable.
weight_rows = [r for r in weight_rows if r.get('notes') != f'{marker}-weight']
food_rows = [r for r in food_rows if r.get('notes') != f'{marker}-food']
with weight_csv.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date', 'weight_kg', 'notes'])
    writer.writeheader()
    writer.writerows(weight_rows)
with food_csv.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date', 'meal_type', 'food_item', 'calories', 'protein_g', 'carbs_g', 'fat_g', 'notes'])
    writer.writeheader()
    writer.writerows(food_rows)

print('PASS: VM health e2e pipeline succeeded')
print('weight_command:', out_weight)
print('food_command:', out_food)
print('macro_chart:', out_chart1)
print('weight_chart:', out_chart2)
print('new_charts:', ', '.join(new_charts))
print('tools.deny:', sorted(deny))
PY"

