
import argparse
import json

from application.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Clickstream Event Sessionization Pipeline"
    )

    parser.add_argument(
        "--input",
        default="data/input/events.csv",
        help="Path to input CSV file",
    )

    parser.add_argument(
        "--db",
        default="data/output/sessionization.db",
        help="Path to SQLite database",
    )

    parser.add_argument(
        "--gap",
        type=int,
        default=30,
        help="Inactivity gap in minutes",
    )

    args = parser.parse_args()

    results = run_pipeline(
        input_path=args.input,
        db_path=args.db,
        gap_minutes=args.gap,
    )

    print("\n=== SESSIONIZATION PIPELINE RESULTS ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
