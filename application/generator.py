
import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_events(output_path, count=100000, users=1000, seed=42):
    if count < 0 or users < 1:
        raise ValueError("count must be >= 0 and users must be >= 1")

    random_generator = random.Random(seed)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 11, 1, tzinfo=timezone.utc)
    event_types = ["login", "page_view", "click", "add_to_cart", "checkout"]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "event_id",
            "user_id",
            "event_timestamp",
            "event_type",
        ])

        for index in range(count):
            user_id = f"U{random_generator.randint(1, users):05d}"
            offset_seconds = random_generator.randint(0, 14 * 24 * 3600)
            event_time = start_time + timedelta(seconds=offset_seconds)

            writer.writerow([
                f"E{index + 1:08d}",
                user_id,
                event_time.isoformat().replace("+00:00", "Z"),
                random_generator.choice(event_types),
            ])

    print(f"Generated {count:,} events")
    print(f"Output file: {path}")
    print(f"Unique users available: {users}")
    print(f"Random seed: {seed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate reproducible clickstream test data"
    )
    parser.add_argument(
        "--output",
        default="data/input/events_100k.csv",
    )
    parser.add_argument("--count", type=int, default=100000)
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    generate_events(
        output_path=args.output,
        count=args.count,
        users=args.users,
        seed=args.seed,
    )
