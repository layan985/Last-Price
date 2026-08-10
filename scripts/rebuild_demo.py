from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from last_price.config import MONITOR_DIR, PROJECT_ROOT, REPORT_DIR, SQLITE_DB
from last_price.data import (
    build_processed,
    build_sqlite_database,
    data_quality_report,
    dataset_fingerprint,
    leakage_audit,
    write_json,
)
from last_price.models import train_models
from last_price.monitoring import make_drifted_batch, monitor_batch
from last_price.multimodal import fused_features
from last_price.policy import evaluate_policy
from last_price.registry import register_run
from last_price.voice import compile_sql, parse_transcript


def write_predictions(run_id, result):
    conn = sqlite3.connect(SQLITE_DB)
    now = pd.Timestamp.utcnow().isoformat()
    try:
        rows = []
        for r in result["agreement_predictions"].itertuples():
            rows.append(
                (
                    run_id,
                    int(r.scenario_id),
                    str(r.treatment_id),
                    "agreement",
                    float(r.agreement_probability),
                    float(r.agreed),
                    now,
                )
            )
        for r in result["price_predictions"].itertuples():
            rows.append(
                (
                    run_id,
                    int(r.scenario_id),
                    str(r.treatment_id),
                    "price",
                    float(r.price_prediction),
                    float(r.price),
                    now,
                )
            )
        conn.executemany(
            """
            INSERT INTO model_predictions
            (run_id, scenario_id, treatment_id, target, prediction, observed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def multimodal_smoke_benchmark():
    out_dir = PROJECT_ROOT / "examples" / "multimodal_images"
    out_dir.mkdir(parents=True, exist_ok=True)
    categories = {
        "electronics": ((60, 110, 220), "phone charger"),
        "fashion": ((200, 80, 110), "leather shoe"),
        "home": ((90, 170, 90), "table lamp"),
    }
    rows = []
    rng = np.random.default_rng(20260810)
    for label, (base_color, phrase) in categories.items():
        for i in range(30):
            noise = rng.integers(-25, 26, size=3)
            color = tuple(np.clip(np.array(base_color) + noise, 0, 255).astype(int))
            p = out_dir / f"{label}_{i:02d}.png"
            img = Image.new("RGB", (64, 64), color)
            draw = ImageDraw.Draw(img)
            if label == "electronics":
                draw.rectangle((20, 8, 44, 56), outline=(255, 255, 255), width=3)
            elif label == "fashion":
                draw.ellipse((10, 25, 54, 48), outline=(255, 255, 255), width=3)
            else:
                draw.line((32, 8, 32, 48), fill=(255, 255, 255), width=4)
                draw.rectangle((18, 45, 46, 54), outline=(255, 255, 255), width=3)
            img.save(p)
            text = f"{phrase} listing {i}"
            feats = fused_features(p, text, float(rng.uniform(15, 200)), int(rng.integers(1, 80)))
            feats["label"] = label
            rows.append(feats)

    frame = pd.DataFrame(rows)
    feature_cols = [c for c in frame.columns if c != "label"]
    train = frame.sample(frac=0.75, random_state=20260810)
    test = frame.drop(train.index)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=20260810))
    model.fit(train[feature_cols], train["label"])
    pred = model.predict(test[feature_cols])
    return {
        "task": "synthetic product-category multimodal smoke benchmark",
        "rows": int(len(frame)),
        "held_out_rows": int(len(test)),
        "accuracy": float(accuracy_score(test["label"], pred)),
        "feature_count": int(len(feature_cols)),
        "note": "Synthetic images/text only; proves a fusion pipeline, not real-world vision performance.",
    }


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)

    df = build_processed()
    quality = data_quality_report(df)
    leakage = leakage_audit(df)
    if not quality["passed"] or not leakage["passed"]:
        raise SystemExit("Data or leakage audit failed.")

    build_sqlite_database(df)
    trained = train_models(df)
    fingerprint = dataset_fingerprint(df)
    run = register_run(fingerprint, trained["metrics"])
    write_predictions(run["run_id"], trained)

    policy = evaluate_policy(
        trained["split"].test,
        trained["agreement_model"],
        trained["price_model"],
        trained["round_means"],
    )

    drifted = make_drifted_batch(trained["split"].test)
    drift = monitor_batch(
        trained["split"].train,
        drifted,
        trained["agreement_model"],
    )

    voice_examples = []
    for text in [
        "Show me inventory in Amman",
        "What is the conversion rate in Dubai?",
        "Compare pricing in Budapest",
        "Show buyer savings in Riyadh",
    ]:
        parsed = parse_transcript(text)
        sql, params = compile_sql(parsed)
        voice_examples.append(
            {
                "transcript": text,
                "intent": parsed.intent,
                "sql": sql,
                "params": params,
            }
        )

    multimodal = multimodal_smoke_benchmark()

    write_json(REPORT_DIR / "data_quality.json", quality)
    write_json(REPORT_DIR / "leakage_audit.json", leakage)
    write_json(REPORT_DIR / "model_metrics.json", trained["metrics"])
    write_json(REPORT_DIR / "policy_kpis.json", policy)
    write_json(REPORT_DIR / "run_manifest.json", run)
    write_json(MONITOR_DIR / "drift_report.json", drift)
    write_json(REPORT_DIR / "voice_demo.json", {"examples": voice_examples})
    write_json(REPORT_DIR / "multimodal_demo.json", multimodal)

    summary = {
        "dataset_sha256": fingerprint,
        "quality_passed": quality["passed"],
        "leakage_audit_passed": leakage["passed"],
        "metrics": trained["metrics"],
        "policy": policy,
        "drift_status": drift["status"],
        "drift_alert_count": len(drift["alerts"]),
        "multimodal": multimodal,
    }
    write_json(REPORT_DIR / "build_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
