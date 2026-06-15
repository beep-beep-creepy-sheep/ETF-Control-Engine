from etfctl.pricing.nav import calculate_indicative_nav


def test_inav_calculation_is_correct() -> None:
    net, nav = calculate_indicative_nav(100_000, 1_000, -500, 250, 50_000)
    assert net == 100_750
    assert nav == 2.015

