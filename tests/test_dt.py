from dt import approx_frac, day_error, exact, frontier, gen_bases, parse_date, true_date


def test_gen_bases_deterministic_and_valid():
    a = gen_bases(30, 5, seed=1)
    b = gen_bases(30, 5, seed=1)
    assert a == b and len(a) == 5
    for iso in a:
        y, m, d = (int(x) for x in iso.split("-"))
        assert 2015 <= y <= 2025 and 1 <= m <= 12 and 1 <= d <= 28


def test_gen_bases_span_independent_streams():
    assert gen_bases(7, 5, seed=1) != gen_bases(365, 5, seed=1)


def test_true_date_known_case():
    # 30 days after 2021-03-15 is 2021-04-14 (March has 31 days)
    assert true_date("2021-03-15", 30) == "2021-04-14"
    assert true_date("2020-02-28", 1) == "2020-02-29"    # leap year


def test_parse_date_last_match_and_tolerance():
    assert parse_date("2021-04-14") == (2021, 4, 14)
    assert parse_date("The answer is 2021-4-9.") == (2021, 4, 9)
    assert parse_date("work...\nFinal: 2022-12-01") == (2022, 12, 1)
    assert parse_date("no date here") is None


def test_day_error_and_exact():
    # model said 2021-04-15 for "30 days after 2021-03-15" (true offset 30, model offset 31)
    e = day_error("2021-04-15", "2021-03-15", 30)
    assert e == 1
    assert exact(e) is False
    assert exact(day_error("2021-04-14", "2021-03-15", 30)) is True
    assert day_error("garbage", "2021-03-15", 30) is None      # unparseable -> None
    assert exact(None) is False


def test_frontier_contiguous():
    assert frontier({1: 1.0, 7: 0.8, 30: 0.3, 100: 0.0}, 0.5) == 7
    assert frontier({1: 0.4}, 0.5) == 0
    assert frontier({}, 0.5) == 0


def test_approx_frac():
    # fraction of errors within tolerance days
    assert approx_frac([1, -2, 40, 5, None], tol=5) == 0.75   # 1,-2,5 within 5 of 4 parseable
    assert approx_frac([], tol=5) == 0.0
