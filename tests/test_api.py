import pandas as pd

from last_price.api import health


def test_health():
    assert health()["status"] == "ok"
