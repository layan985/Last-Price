import sqlite3

from last_price.data import build_processed, build_sqlite_database


def test_sql_database_builds():
    df = build_processed()
    path = build_sqlite_database(df)
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT COUNT(*) FROM negotiations").fetchone()[0]
        scenarios = conn.execute("SELECT COUNT(DISTINCT scenario_id) FROM negotiations").fetchone()[0]
    finally:
        conn.close()
    assert rows == 3000
    assert scenarios == 500
