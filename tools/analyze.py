"""Derive the date-arithmetic picture for each model: exact-date accuracy by day span, the
frontier (largest span solved at >=0.5, contiguous), and - the distinctive angle - how wrong the
model is when it is wrong: the median absolute day error, the fraction of errors within a few
days ("approximately right", the signature of naive month arithmetic), and the mean signed error.
Writes bench_results/frontier.md and curve.json. Pure derivation from results/*.jsonl.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from typing import Optional, TypedDict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dt import approx_frac, frontier  # noqa: E402

MODELS = [("1.5B", "results/dt_15b.jsonl"), ("0.5B", "results/dt_05b.jsonl")]
THRESH = 0.5
TOL = 5


class Row(TypedDict):
    model: str
    span: int
    idx: int
    base: str
    day_error: Optional[int]
    exact: bool


def load(path: str) -> list[Row]:
    return [json.loads(x) for x in open(path) if x.strip()]


def acc_by_span(rows: list[Row]) -> dict[int, float]:
    out: dict[int, float] = {}
    for s in sorted({r["span"] for r in rows}):
        sub = [r for r in rows if r["span"] == s]
        if sub:
            out[s] = sum(1 for r in sub if r["exact"]) / len(sub)
    return out


def analyze_model(label: str, rows: list[Row]) -> dict[str, object]:
    acc = acc_by_span(rows)
    spans = sorted(acc)
    err_stats = {}
    for s in spans:
        errs = [r["day_error"] for r in rows if r["span"] == s and not r["exact"]]
        parse = [e for e in errs if e is not None]
        err_stats[str(s)] = {
            "n_err": len(errs),
            "median_abs_err": float(statistics.median([abs(e) for e in parse])) if parse else 0.0,
            "mean_signed_err": float(statistics.mean(parse)) if parse else 0.0,
            "approx_frac": approx_frac(errs, TOL),
            "parse_fail": sum(1 for e in errs if e is None) / len(errs) if errs else 0.0,
        }
    return {"label": label, "acc": {str(s): acc[s] for s in spans},
            "frontier": frontier(acc, THRESH), "err_stats": err_stats}


def render(r: dict[str, object]) -> list[str]:
    acc = r["acc"]
    es = r["err_stats"]
    assert isinstance(acc, dict) and isinstance(es, dict)
    spans = sorted(int(s) for s in acc)
    lines = [f"## {r['label']} (frontier {r['frontier']} days)", "",
             "  span   acc    median|err|  mean signed  approx(<=5d)  parse-fail"]
    for s in spans:
        a = acc[str(s)]
        e = es[str(s)]
        lines.append(f"  {s:>4}   {a:.2f}   {e['median_abs_err']:>7.0f}     "
                     f"{e['mean_signed_err']:>+7.0f}      {e['approx_frac']:.2f}"
                     f"         {e['parse_fail']:.2f}")
    lines.append("")
    return lines


def main() -> int:
    results = []
    for label, path in MODELS:
        if not os.path.exists(path):
            print(f"MISSING {path}", file=sys.stderr)
            return 1
        results.append(analyze_model(label, load(path)))
    os.makedirs("bench_results", exist_ok=True)
    with open("bench_results/curve.json", "w") as f:
        json.dump(results, f, indent=2)
    lines = ["# datefrontier: how far ahead can a model count calendar days?", "",
             "Ask 'What date is N days after D?' with the ground truth from Python's datetime.",
             "Exact-date accuracy by the day span N, the frontier (largest N solved at >=0.5),",
             "and how wrong the model is when wrong: the median absolute day error, the mean",
             "signed error, and the fraction of errors within 5 days (approximately right).", ""]
    for r in results:
        lines += render(r)
    with open("bench_results/frontier.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
