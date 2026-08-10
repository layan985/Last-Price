
from last_price.data import build_processed, data_quality_report, leakage_audit


def test_data_quality_and_leakage():
    df = build_processed()
    quality = data_quality_report(df)
    audit = leakage_audit(df)
    assert len(df) == 3000
    assert quality["passed"]
    assert audit["passed"]
    assert df.groupby("scenario_id")["city"].nunique().max() == 1
