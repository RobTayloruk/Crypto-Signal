"""Environment self-check for Crypto Signal Pro."""

from __future__ import annotations

from importlib import util
import sys

REQUIRED = ["streamlit", "plotly", "pandas", "requests", "pytest"]


def main() -> int:
    missing = []
    for dep in REQUIRED:
        if util.find_spec(dep) is None:
            missing.append(dep)

    if missing:
        print("Missing dependencies:", ", ".join(missing))
        print("Install with: python -m pip install -r requirements.txt")
        return 1

    print("All core dependencies are installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
