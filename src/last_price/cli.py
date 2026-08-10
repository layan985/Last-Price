from __future__ import annotations

import argparse
import json

from .data import build_processed, data_quality_report, leakage_audit
from .models import train_models


def main():
    parser = argparse.ArgumentParser(prog="last-price")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-data")
    sub.add_parser("train")
    sub.add_parser("audit")
    args = parser.parse_args()

    if args.command == "build-data":
        df = build_processed()
        print(f"built {len(df)} rows")
    elif args.command == "train":
        df = build_processed()
        out = train_models(df)
        print(json.dumps(out["metrics"], indent=2))
    elif args.command == "audit":
        df = build_processed()
        print(json.dumps({"quality": data_quality_report(df), "leakage": leakage_audit(df)}, indent=2))


if __name__ == "__main__":
    main()
