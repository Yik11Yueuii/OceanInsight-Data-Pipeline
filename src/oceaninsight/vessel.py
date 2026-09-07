from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from .core import grid_cell, in_region

REQUIRED_COLUMNS = {"date", "cell_ll_lat", "cell_ll_lon", "mmsi", "hours", "fishing_hours"}
OUTPUT_COLUMNS = [
    "observation_date", "year", "month", "year_month", "source_grid_lat", "source_grid_lon",
    "grid_lat", "grid_lon", "grid_id", "mmsi", "hours", "fishing_hours", "quality_flag",
    "source_file", "batch_id"
]


def select_zip(
    zip_path: Path,
    output_path: Path,
    bounds: dict,
    grid_size: float,
    batch_id: str,
    selected_months: set[int] | None = None,
) -> dict:
    """Stream a yearly ZIP and retain every valid row inside the configured region."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats = {"files": 0, "skipped_files": 0, "input_rows": 0, "output_rows": 0, "invalid_rows": 0, "outside_region_rows": 0}
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with zipfile.ZipFile(zip_path) as archive, tmp_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for member in sorted(n for n in archive.namelist() if n.lower().endswith(".csv")):
            if selected_months:
                date_match = __import__("re").search(r"(\d{4})-(\d{2})-(\d{2})", member)
                if date_match and int(date_match.group(2)) not in selected_months:
                    stats["skipped_files"] += 1
                    continue
            stats["files"] += 1
            with archive.open(member) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
                if missing:
                    raise ValueError(f"{member} missing columns: {sorted(missing)}")
                for row in reader:
                    stats["input_rows"] += 1
                    try:
                        lat = float(row["cell_ll_lat"])
                        lon = float(row["cell_ll_lon"])
                        hours = float(row["hours"])
                        fishing_hours = float(row["fishing_hours"])
                        if not (0 <= hours <= 24 and 0 <= fishing_hours <= 24):
                            raise ValueError("hours out of range")
                        if not in_region(lat, lon, bounds):
                            stats["outside_region_rows"] += 1
                            continue
                        grid_lat, grid_lon, grid_id = grid_cell(lat, lon, grid_size)
                        date = row["date"]
                        if selected_months and int(date[5:7]) not in selected_months:
                            continue
                        writer.writerow({
                            "observation_date": date,
                            "year": date[:4],
                            "month": date[5:7],
                            "year_month": date[:7],
                            "source_grid_lat": lat,
                            "source_grid_lon": lon,
                            "grid_lat": grid_lat,
                            "grid_lon": grid_lon,
                            "grid_id": grid_id,
                            "mmsi": row["mmsi"],
                            "hours": hours,
                            "fishing_hours": fishing_hours,
                            "quality_flag": "VALID",
                            "source_file": member,
                            "batch_id": batch_id,
                        })
                        stats["output_rows"] += 1
                    except (TypeError, ValueError):
                        stats["invalid_rows"] += 1
    tmp_path.replace(output_path)
    stats["output_bytes"] = output_path.stat().st_size
    return stats
