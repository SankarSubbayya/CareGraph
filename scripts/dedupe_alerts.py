"""One-off or maintenance: remove duplicate Alert nodes (same senior + same message).

Usage:
  python3 scripts/dedupe_alerts.py

Requires Neo4j env (same as the app). Safe to run multiple times.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_db import dedupe_alerts, close_driver


def main() -> None:
    result = dedupe_alerts()
    print(
        f"Duplicate groups merged: {result['duplicate_groups']}\n"
        f"Alert nodes removed: {result['alerts_removed']}"
    )
    close_driver()


if __name__ == "__main__":
    main()
