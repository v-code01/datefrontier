#!/usr/bin/env python3
"""Independent verification of the headline, sharing NO code with src/dt.py or
tools/analyze.py. Re-reads the raw JSONL and recomputes, from scratch (its own datetime diff),
the day error, exact-date accuracy by span, the frontier, and the approximately-right fraction,
then asserts: (1) date accuracy collapses with the day span and the smaller model's frontier is
far shorter; (2) in the near regime the larger model is approximately right when wrong (errors
within a few days, the month-approximation signature) while for large spans it fails outright;
(3) the models overshoot (positive mean signed error). Exit non-zero on mismatch. In the gate.
"""
from __future__ import annotations

import datetime
import json
import statistics
import sys

PATHS = {"1.5B": "results/dt_15b.jsonl", "0.5B": "results/dt_05b.jsonl"}


def err_of(row: dict[str, object]) -> int | None:
    md = str(row["model_date"])
    if not md:
        return None
    try:
        model = datetime.date.fromisoformat(md)
        base = datetime.date.fromisoformat(str(row["base"]))
    except ValueError:
        return None
    return (model - base).days - int(str(row["span"]))


def rows_of(path: str) -> list[dict[str, object]]:
    return [json.loads(x) for x in open(path) if x.strip()]


def acc_by_span(rows: list[dict[str, object]]) -> dict[int, float]:
    out: dict[int, float] = {}
    for s in sorted({int(str(r["span"])) for r in rows}):
        sub = [r for r in rows if int(str(r["span"])) == s]
        out[s] = sum(1 for r in sub if err_of(r) == 0) / len(sub)
    return out


def frontier(acc: dict[int, float], thr: float = 0.5) -> int:
    best = 0
    for s in sorted(acc):
        if acc[s] >= thr:
            best = s
        else:
            break
    return best


def approx_frac(rows: list[dict[str, object]], span: int, tol: int = 5) -> float:
    errs = [err_of(r) for r in rows if int(str(r["span"])) == span and err_of(r) != 0]
    parse = [e for e in errs if e is not None]
    if not parse:
        return 0.0
    return sum(1 for e in parse if abs(e) <= tol) / len(parse)


def mean_signed(rows: list[dict[str, object]], span: int) -> float:
    errs = [err_of(r) for r in rows if int(str(r["span"])) == span and err_of(r) != 0]
    parse = [e for e in errs if e is not None]
    return float(statistics.mean(parse)) if parse else 0.0


def main() -> int:
    data = {m: rows_of(p) for m, p in PATHS.items()}
    fr = {m: frontier(acc_by_span(data[m])) for m in PATHS}
    for m in PATHS:
        acc = acc_by_span(data[m])
        spans = sorted(acc)
        print(f"  {m}: frontier {fr[m]} days; acc N{spans[0]}={acc[spans[0]]:.2f} "
              f"N{spans[-1]}={acc[spans[-1]]:.2f}; approx(N14)={approx_frac(data[m], 14):.2f} "
              f"approx(N365)={approx_frac(data[m], 365):.2f}; signed(N30)={mean_signed(data[m], 30):+.0f}")

    a15 = acc_by_span(data["1.5B"])
    spans15 = sorted(a15)
    collapse = a15[spans15[-1]] < a15[spans15[0]] and fr["1.5B"] <= 30
    small_shorter = fr["0.5B"] < fr["1.5B"]
    near_right = approx_frac(data["1.5B"], 14) > 0.6 and approx_frac(data["1.5B"], 365) < 0.2
    overshoot = mean_signed(data["1.5B"], 30) > 0 and mean_signed(data["0.5B"], 30) > 0
    print(f"  accuracy collapses with span, small frontier far shorter: {collapse and small_shorter}")
    print(f"  approximately right near, fails far (month approximation): {near_right}")
    print(f"  models overshoot (positive signed error at N30): {overshoot}")

    if collapse and small_shorter and near_right and overshoot:
        print("VERIFY OK: date arithmetic has a short frontier; the model is approximately right "
              "nearby (month approximation) and fails outright far out, overshooting")
        return 0
    print("VERIFY FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
