"""dt core: deterministic base dates, exact date arithmetic ground truth (via datetime), robust
parsing of a model's returned date, the signed day error of its answer, the accuracy frontier
over the day span, and the "approximately right" fraction (errors within a few days, the
signature of naive month arithmetic). Deterministic and exact; the ground truth is Python's
datetime, no judge.
"""
from __future__ import annotations

import datetime
import random
import re
from typing import Mapping, Optional, Sequence

_DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def gen_bases(span: int, n: int, seed: int) -> list[str]:
    """n base dates (ISO strings) in 2015-2025, days 1-28 to keep the base unambiguous. Seeded
    from (seed, span) so each span has its own reproducible stream.
    """
    rng = random.Random(f"{seed}:{span}")
    out = []
    for _ in range(n):
        y = rng.randint(2015, 2025)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28)
        out.append(datetime.date(y, m, d).isoformat())
    return out


def true_date(base_iso: str, span: int) -> str:
    """The exact date `span` days after `base_iso`, as an ISO string."""
    base = datetime.date.fromisoformat(base_iso)
    return (base + datetime.timedelta(days=span)).isoformat()


def parse_date(text: str) -> Optional[tuple[int, int, int]]:
    """The last YYYY-M-D date in the text (1-2 digit month/day tolerated), or None."""
    matches = _DATE.findall(text)
    if not matches:
        return None
    y, m, d = matches[-1]
    return int(y), int(m), int(d)


def day_error(model_iso: str, base_iso: str, span: int) -> Optional[int]:
    """(model offset from base) - span, in days. None if the model's date does not parse or is
    not a valid calendar date.
    """
    parsed = parse_date(model_iso)
    if parsed is None:
        return None
    try:
        model = datetime.date(*parsed)
    except ValueError:
        return None
    base = datetime.date.fromisoformat(base_iso)
    return (model - base).days - span


def exact(err: Optional[int]) -> bool:
    return err == 0


def frontier(acc_by_span: Mapping[int, float], threshold: float) -> int:
    """Largest day span solved at or above `threshold`, contiguous from the smallest span up."""
    best = 0
    for span in sorted(acc_by_span):
        if acc_by_span[span] >= threshold:
            best = span
        else:
            break
    return best


def approx_frac(errors: Sequence[Optional[int]], tol: int) -> float:
    """Among parseable errors, the fraction within `tol` days of correct (|error| <= tol)."""
    parseable = [e for e in errors if e is not None]
    if not parseable:
        return 0.0
    return sum(1 for e in parseable if abs(e) <= tol) / len(parseable)
