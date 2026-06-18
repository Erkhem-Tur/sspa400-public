"""Convert the SSPA terminology CSV export into browser-ready JSON."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = (
    "item_id",
    "module",
    "item_type",
    "front",
    "back_mn",
    "definition_en",
    "example_en",
    "audio_script",
    "difficulty",
    "priority",
    "tags",
    "source_reference",
    "review_note",
)


def convert(source: Path, destination: Path) -> None:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(FIELDS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        items = [
            {field: (row.get(field) or "").strip() for field in FIELDS}
            for row in reader
        ]

    ids = [item["item_id"] for item in items]
    if len(items) != 310:
        raise ValueError(f"Expected 310 rows, found {len(items)}")
    if len(ids) != len(set(ids)):
        raise ValueError("item_id values must be unique")
    if any(not item["front"] or not item["back_mn"] or not item["audio_script"] for item in items):
        raise ValueError("Every item needs English, Mongolian, and an audio script")

    payload = {
        "meta": {
            "course": "SSPA Protection Operations English",
            "version": 1,
            "item_count": len(items),
            "modules": sorted({item["module"] for item in items}),
            "levels": ["A2", "B1", "B2", "C1"],
        },
        "items": items,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    convert(args.source, args.destination)


if __name__ == "__main__":
    main()
