"""Run the Last Price GLEE agent against the live competition."""

from __future__ import annotations

import os

from glee_sdk import GleeClient

from last_price.glee_agent import strategy


def main() -> None:
    api_key = os.environ.get("GLEE_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Set GLEE_API_KEY from the GLEE dashboard before running.")

    client = GleeClient(api_key=api_key)
    print("Starting Last Price GLEE agent")
    print(client.stats())
    client.run(
        strategy,
        concurrency=int(os.getenv("GLEE_CONCURRENCY", "6")),
        max_games=int(os.getenv("GLEE_MAX_GAMES", "100")),
    )
    print(client.stats())


if __name__ == "__main__":
    main()
