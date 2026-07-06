from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from privacy_masking.semantic_placeholder import write_demo_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the synthetic semantic-placeholder masking demo."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "examples" / "semantic_placeholder_run.json",
        help="Path to write the JSON result.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = write_demo_json(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nGenerated {args.output.resolve()}")


if __name__ == "__main__":
    main()
