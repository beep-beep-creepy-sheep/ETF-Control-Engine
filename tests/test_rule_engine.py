from etfctl.controls.rule_engine import ExceptionBuilder


def test_rule_engine_maps_exception_severity_from_yaml() -> None:
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", {"severity": {"MISSING_PRICE": "HIGH"}})
    exception = builder.build("MISSING_PRICE", "SECURITY", "NVDA", "missing", "none")
    assert exception["severity"] == "HIGH"

