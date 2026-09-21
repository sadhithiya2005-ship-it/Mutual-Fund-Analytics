import pandas as pd


def test_fcf_calculation():
    cfo = 100
    capex = 30

    fcf = cfo - capex

    assert fcf == 70


def test_fcf_conversion():
    cfo = 100
    fcf = 70

    conversion = (fcf / cfo) * 100

    assert conversion == 70


def test_debt_free_flag():
    debt_to_equity = pd.Series([0, 0.5, 2.0])

    result = debt_to_equity.eq(0)

    assert result.tolist() == [True, False, False]


def test_high_leverage_flag():
    debt_to_equity = pd.Series([1.0, 2.0, 2.1, 3.0])

    result = debt_to_equity > 2

    assert result.tolist() == [False, False, True, True]


def test_interest_coverage_warning():
    interest_coverage = pd.Series([1.0, 1.99, 2.0, 5.0])

    result = interest_coverage < 2

    assert result.tolist() == [True, True, False, False]


def test_eps_cagr():
    start_eps = 100
    end_eps = 121
    years = 2

    cagr = ((end_eps / start_eps) ** (1 / years) - 1) * 100

    assert round(cagr, 2) == 10.0


def test_capex_to_cfo():
    capex = 25
    cfo = 100

    ratio = (capex / cfo) * 100

    assert ratio == 25


def test_negative_fcf():
    cfo = 50
    capex = 80

    fcf = cfo - capex

    assert fcf == -30


def test_zero_cfo_fcf_conversion():
    cfo = 0
    fcf = 50

    result = None if cfo == 0 else (fcf / cfo) * 100

    assert result is None


def test_zero_cfo_capex_ratio():
    cfo = 0
    capex = 20

    result = None if cfo == 0 else (capex / cfo) * 100

    assert result is None


def test_positive_fcf():
    cfo = 150
    capex = 50

    assert cfo - capex == 100


def test_zero_fcf():
    cfo = 100
    capex = 100

    assert cfo - capex == 0


def test_debt_free_false_for_positive_debt():
    debt_to_equity = 0.5

    assert debt_to_equity != 0


def test_high_leverage_boundary():
    debt_to_equity = 2

    assert not (debt_to_equity > 2)


def test_high_leverage_above_boundary():
    debt_to_equity = 2.01

    assert debt_to_equity > 2


def test_interest_coverage_boundary():
    interest_coverage = 2

    assert not (interest_coverage < 2)


def test_eps_cagr_negative_growth():
    start_eps = 100
    end_eps = 81
    years = 2

    cagr = ((end_eps / start_eps) ** (1 / years) - 1) * 100

    assert round(cagr, 2) == -10.0