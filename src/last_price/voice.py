from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedVoiceQuery:
    intent: str
    metric: str | None = None
    city: str | None = None
    threshold_pct: float | None = None


CITIES = ["Amman", "Budapest", "Dubai", "Riyadh", "Cairo"]


def parse_transcript(text: str) -> ParsedVoiceQuery:
    t = text.strip().lower()
    city = next((c for c in CITIES if c.lower() in t), None)
    threshold = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", t)
    if m:
        threshold = float(m.group(1))

    if "inventory" in t or "stock" in t:
        return ParsedVoiceQuery("inventory_query", "inventory_level", city, threshold)
    if "agreement" in t or "conversion" in t:
        return ParsedVoiceQuery("conversion_query", "agreement_rate", city, threshold)
    if "price" in t or "pricing" in t:
        return ParsedVoiceQuery("pricing_query", "mean_price", city, threshold)
    if "surplus" in t or "savings" in t:
        return ParsedVoiceQuery("savings_query", "buyer_surplus", city, threshold)
    return ParsedVoiceQuery("unknown", None, city, threshold)


def compile_sql(parsed: ParsedVoiceQuery) -> tuple[str, list]:
    where = []
    params = []
    if parsed.city:
        where.append("city = ?")
        params.append(parsed.city)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    if parsed.intent == "inventory_query":
        sql = (
            "SELECT city, AVG(inventory_level) AS avg_inventory, "
            "AVG(stockout_risk) AS avg_stockout_risk "
            f"FROM negotiations{where_sql} GROUP BY city ORDER BY avg_inventory ASC"
        )
    elif parsed.intent == "conversion_query":
        sql = (
            "SELECT buyer_model, AVG(agreed) AS agreement_rate "
            f"FROM negotiations{where_sql} GROUP BY buyer_model ORDER BY agreement_rate DESC"
        )
    elif parsed.intent == "pricing_query":
        extra = "price IS NOT NULL"
        if where:
            where_sql = where_sql + " AND " + extra
        else:
            where_sql = " WHERE " + extra
        sql = (
            "SELECT buyer_model, AVG(price) AS mean_price "
            f"FROM negotiations{where_sql} GROUP BY buyer_model ORDER BY mean_price ASC"
        )
    elif parsed.intent == "savings_query":
        sql = (
            "SELECT buyer_model, AVG(buyer_surplus) AS mean_buyer_surplus "
            f"FROM negotiations{where_sql} GROUP BY buyer_model ORDER BY mean_buyer_surplus DESC"
        )
    else:
        raise ValueError("Transcript did not map to a supported intent.")
    return sql, params


def transcribe_audio(path: str) -> str:
    """Optional local Whisper adapter. Install with `pip install -e .[voice]`."""
    try:
        import whisper  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Whisper extra is not installed. Use `pip install -e .[voice]`.") from exc
    model = whisper.load_model("base")
    result = model.transcribe(path)
    return str(result["text"])
