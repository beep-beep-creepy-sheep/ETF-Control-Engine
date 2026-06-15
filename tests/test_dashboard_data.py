from __future__ import annotations

import pandas as pd

from etfctl.report.dashboard_data import _severity_counts


def test_dashboard_severity_counts_include_empty_buckets() -> None:
    exceptions = pd.DataFrame([{"severity": "HIGH"}, {"severity": "HIGH"}, {"severity": "LOW"}])
    counts = _severity_counts(exceptions)
    assert counts == {"HIGH": 2, "MEDIUM": 0, "LOW": 1}

