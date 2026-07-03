# Adversarial review

An attempt to refute each headline claim before publishing. Every objection I could construct
is listed with how the data answers it. Claims that survived are the ones reported.

## Claim A: the exact-date frontier is short

- **"Your parser misreads the model's date, so accuracy only looks low."** The parse-fail rate is
  essentially zero (0.00-0.03), so almost every reply yields a date; the accuracy is measured on
  parsed dates against an exact datetime difference. verify.py recomputes the day error with its
  own datetime, independent of src, and gets the same frontiers.
- **"1-day accuracy is only 0.82, so even the easy case fails - something is off."** The 1-day
  misses are off-by-one (median absolute error 1 day), i.e. the model lands an adjacent date, which
  is the same month-boundary approximation showing up even at N=1. That is a finding, not a bug.

## Claim B: the errors are month approximation (approximately right near, failing far)

- **"'Approximately right' is just a loose threshold."** The full median absolute error and mean
  signed error are reported next to the 5-day fraction, so the reader can see the effect without
  the threshold: median error is 2-4 days at 7-30 days on the 1.5B and 28-94 days at 100-365. The
  threshold only labels a pattern that the raw medians already show.
- **"The month-approximation story is post hoc."** It is a concrete, checkable mechanism: adding
  whole months to a date reproduces exactly the small, boundary-sized errors observed near the
  frontier (e.g. 30 days after March 15 answered as April 15). It was pre-registered as the
  predicted signature, and the near/far split is reported honestly as a refinement.

## Claim C: both models overshoot

- **"A few huge outliers drive the positive mean."** The overshoot is asserted at the 30-day span
  where errors are moderate (the 0.5B mean is +70 with a median absolute error of 23), not only at
  the extreme spans; and it matches the overshoot direction found in a separate output-count study,
  so it is a consistent bias, not an artifact of one span.

## Confounds checked

- Base dates chosen deterministically per span, so both models see identical questions.
- Ground truth is Python's datetime; the day error is an exact date difference; no judge.
- Greedy decoding, temperature 0, fixed seed: outputs are deterministic.
- Parse-fail rate is near zero, so accuracy is not depressed by unparseable replies.

## What this does NOT claim

- Not that the models cannot handle any date - they land short spans often and are close on
  medium ones; the frontier and the error shape describe where and how it breaks.
- Not that chain-of-thought would not help in principle - it is excluded because these models'
  step-by-step date reasoning is itself broken, which is a different question.
- Not a claim about larger models or tool-assisted date arithmetic.
