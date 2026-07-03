#!/usr/bin/env bash
# Regenerate the date-arithmetic sweep for both models.
# Usage: ./reproduce.sh PORT_15B PORT_05B
set -euo pipefail
cd "$(dirname "$0")"
P15="${1:-8081}"; P05="${2:-8082}"
. .venv/bin/activate
python tools/run_sweep.py --port "$P15" --model qwen-dt   --n 40 --spans 1,3,7,14,30,60,100,365 --out results/dt_15b.jsonl
python tools/run_sweep.py --port "$P05" --model qwen-dt05 --n 40 --spans 1,3,7,14,30,60,100,365 --out results/dt_05b.jsonl
python tools/analyze.py
python tools/verify.py
echo "regenerated results; see bench_results/frontier.md"
