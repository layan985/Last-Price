from last_price.voice import compile_sql, parse_transcript


def test_voice_query_to_sql():
    parsed = parse_transcript("Show me inventory in Amman")
    assert parsed.intent == "inventory_query"
    sql, params = compile_sql(parsed)
    assert "inventory_level" in sql
    assert params == ["Amman"]
