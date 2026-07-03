# datefrontier

How far ahead can a small language model count calendar days? This asks "what date is N days
after D?" for two instruction-tuned models (Qwen2.5 1.5B and 0.5B), with the ground truth from
Python's `datetime`, and measures not just whether the answer is right but - when it is wrong -
how wrong, which turns out to reveal exactly how the models "do" date arithmetic.

The headline: **the models do not count days, they shift months.** The 1.5B reliably lands the
exact date only about two weeks out, the 0.5B only one day out; but in that near regime, when the
1.5B is wrong it is wrong by just a few days (median 2-4), because it approximates N days as a
whole number of months and misses only the month-length and boundary corrections. Push the span
to a year and it fails outright, off by months, overshooting.

## Method

- Ask "What date is N days after D?" for spans N in {1, 3, 7, 14, 30, 60, 100, 365}, base dates
  drawn deterministically per span, direct ISO answer.
- Ground truth is `date(D) + timedelta(days=N)`. The model's returned date is parsed and its
  **signed day error** recorded (model's offset minus N).
- Exact-date accuracy by span, the **frontier** (largest span solved at >=0.5, contiguous), and,
  among the errors, the **median absolute day error**, the **mean signed error**, and the
  fraction within 5 days ("approximately right").
- Greedy decoding, both models, n=40 per span.
- Direct answers only. The models' step-by-step date reasoning is itself broken - it increments
  by months where it should increment by days ("April 22 plus 1 day is May 22") and does not
  converge before running out of tokens - so a chain-of-thought condition would measure that
  pathology rather than date arithmetic. It is noted here as an observation, not a variable.

## Pre-registered prediction

Written down before the full run (a pilot showed a short frontier and month-shaped errors):

> (1) Exact date accuracy falls with the day span N, with a frontier of about a week. (2) The
> smaller model's frontier is shorter. (3) Even when wrong the models are approximately right -
> errors cluster at small day offsets, the signature of naive month arithmetic rather than random
> guessing.

All three held, with a refinement: the "approximately right" behaviour is a near-regime effect.
Within about a month the 1.5B's errors are a few days; past that it fails outright, so the
month-approximation is visible where the answer is close and gives way to plain failure far out.

## Results (n=40 per span)

```
1.5B (frontier 14 days)
  span   acc    median|err|  mean signed  approx(<=5d)
     1   0.82        1          +14         0.57
     7   0.90        2           +7         0.75
    14   0.60        2           +3         0.81
    30   0.25        4          +10         0.53
    60   0.05       12           +8         0.29
   100   0.03       28          -23         0.10
   365   0.03       94          +46         0.03

0.5B (frontier 1 day)
  span   acc    median|err|  mean signed  approx(<=5d)
     1   0.80        4           +6         0.62
     7   0.23       22          +22         0.40
    14   0.00       16          +22         0.08
    30   0.15       23          +70         0.47
   100   0.00      996        +1719         0.00
   365   0.03      335          +57         0.00
```

Full numbers in `bench_results/frontier.md`.

## What this shows

1. **The exact-date frontier is short.** The 1.5B reliably nails the date only to a two-week
   span; the 0.5B only to a single day. Beyond that, exact accuracy collapses.
2. **When it is close, it is approximately right.** In the near regime (about a week to a month)
   the 1.5B's wrong answers are off by a median of 2-4 days, and half to four-fifths of them are
   within 5 days - the fingerprint of approximating N days as whole months and missing only the
   month-length correction (e.g. "30 days after March 15" answered as April 15, one day over
   because March has 31 days).
3. **Far out, it fails outright.** At 100 and 365 days the errors are tens to hundreds of days and
   the approximately-right fraction falls to near zero - the month approximation is abandoned for
   plain failure.
4. **Both models overshoot.** Mean signed errors are mostly positive (the 0.5B is +70 at 30 days),
   the same runaway-overshoot direction seen when these models are asked to produce a fixed count
   of items - they add too much when they cannot track the exact amount.

## Limitations and falsifiers

- Two model sizes, one phrasing, greedy decoding, n=40 per span. Direct answers only (CoT
  excluded for the reason above). Not a claim about larger models or tool-assisted date math.
- The day error is exact (datetime difference); the "approximately right" tolerance of 5 days is
  reported alongside the full median and signed errors so the threshold is transparent.
- **Falsifier:** if accuracy had held as the span grew, there would be no frontier. It collapses
  from 0.90 at 7 days to 0.03 at 365.
- **Falsifier:** if the near-regime errors had been large and random, the month-approximation
  claim would fail. They are a median of 2-4 days on the 1.5B at 7-30 days.
- The adversarial pass that tried to refute each claim is in `REVIEW.md`.

## Reproduce

```bash
./scripts/gate.sh                 # ruff + mypy --strict + pytest + ASCII + independent verify
./reproduce.sh 8081 8082          # rerun both models against two OpenAI-compatible endpoints
```

`tools/verify.py` recomputes the day errors (with its own datetime difference), the frontiers,
and the approximately-right fractions straight from the raw JSONL, sharing no code with the
analysis, and the ship gate runs it.

## Layout

```
src/dt.py            deterministic bases + exact datetime ground truth + parse + day-error + frontier
tests/test_dt.py     7 unit tests, including a known date case and parse tolerance
tools/run_sweep.py   direct date-arithmetic sweep over the day span
tools/analyze.py     accuracy by span, frontier, day-error mechanism (median, signed, approx)
tools/verify.py      independent recompute of the headline claims (in the gate)
bench_results/       frontier.md + curve.json
claims.toml          every claim tied to its evidence
REVIEW.md            adversarial refutation attempt
```

MIT licensed.
