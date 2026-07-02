"""Sweep exact date arithmetic over the day span N for one model. Base dates are generated
deterministically per span, so every model sees identical questions. The model is asked for a
direct ISO date; the ground truth is Python's datetime, and the model's returned date is parsed
and its signed day error recorded. No judge. Writes results/<model>.jsonl.

Direct answers only: the models' step-by-step reasoning for dates is itself broken (it
increments by months where it should increment by days and does not converge), so a
chain-of-thought condition would measure that pathology rather than date arithmetic - noted in
the README as an observation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dt import day_error, exact, gen_bases, parse_date, true_date  # noqa: E402

_SYS = "Answer with only the date in YYYY-MM-DD format, nothing else."


def ask(url: str, model: str, base: str, span: int) -> str:
    q = f"What date is {span} days after {base}?"
    payload = json.dumps({"model": model,
                          "messages": [{"role": "system", "content": _SYS},
                                       {"role": "user", "content": q}],
                          "temperature": 0.0, "max_tokens": 24, "seed": 1}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read())
        return str(j["choices"][0]["message"]["content"])
    except Exception:  # noqa: BLE001
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="8081")
    ap.add_argument("--model", default="qwen-dt")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--spans", default="1,3,7,14,30,60,100,365")
    ap.add_argument("--seed", type=int, default=20260712)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}/v1/chat/completions"
    spans = [int(x) for x in args.spans.split(",")]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    jobs = []
    for span in spans:
        for i, base in enumerate(gen_bases(span, args.n, args.seed)):
            jobs.append((span, i, base))

    def run(job: tuple[int, int, str]) -> dict[str, object]:
        span, i, base = job
        raw = ask(url, args.model, base, span)
        parsed = parse_date(raw)
        model_iso = f"{parsed[0]:04d}-{parsed[1]:02d}-{parsed[2]:02d}" if parsed else ""
        err = day_error(raw, base, span)
        return {"model": args.model, "span": span, "idx": i, "base": base,
                "true_date": true_date(base, span), "raw": raw, "model_date": model_iso,
                "day_error": err, "exact": exact(err)}

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool, \
            open(args.out, "w", buffering=1) as f:
        for c, row in enumerate(pool.map(run, jobs)):
            f.write(json.dumps(row) + "\n")
            if (c + 1) % 100 == 0:
                print(f"  {args.model} {c + 1}/{len(jobs)}", flush=True)
    print(f"# SWEEP_DONE {args.model}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
