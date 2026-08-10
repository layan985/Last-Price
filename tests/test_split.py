from last_price.data import build_processed
from last_price.models import temporal_group_split


def test_time_group_split_has_no_scenario_overlap():
    df = build_processed()
    split = temporal_group_split(df)
    assert set(split.train.scenario_id).isdisjoint(set(split.test.scenario_id))
    assert split.train.timestamp.max() < split.test.timestamp.max()
