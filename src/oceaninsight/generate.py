from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

from .cli import load_config
from .core import RunManifest, sha256_file
from .nc import _year_month, select_nc
from .vessel import select_zip


INDICATOR_DIRS = {
    "1-": "temperature", "2-": "salinity", "3-": "heat_content",
    "4-": "current", "5-": "oxygen",
}

INDICATOR_NAMES = {"temperature", "salinity", "heat_content", "current", "oxygen"}


def _indicator(path: Path) -> str:
    for parent in path.parents:
        if parent.name in INDICATOR_NAMES:
            return parent.name
        for prefix, indicator in INDICATOR_DIRS.items():
            if parent.name.startswith(prefix):
                return indicator
    raise ValueError(f"Cannot identify indicator for {path}")


def _record_output(manifest: RunManifest, path: Path, kind: str, stats: dict, elapsed: float) -> None:
    manifest.outputs.append({
        "kind": kind, "path": str(path.resolve()), "bytes": path.stat().st_size,
        "sha256": sha256_file(path), "elapsed_seconds": round(elapsed, 3), "stats": stats,
    })


def filter_vessel_master(master_path: Path, vessel_outputs: list[Path], output_path: Path, batch_id: str) -> dict:
    keys: set[tuple[str, str]] = set()
    for path in vessel_outputs:
        with path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                keys.add((row["mmsi"], row["year"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".csv.tmp")
    stats = {"required_keys": len(keys), "input_rows": 0, "output_rows": 0, "missing_keys": 0}
    with master_path.open(encoding="utf-8-sig", newline="") as source, tmp.open("w", encoding="utf-8", newline="") as target:
        reader = csv.DictReader(source)
        source_fields = list(reader.fieldnames or [])
        fields = [
            field
            for field in source_fields
            if field not in {"batch_id", "source_file"}
        ] + ["batch_id", "source_file"]
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for row in reader:
            stats["input_rows"] += 1
            key = (row.get("mmsi", ""), row.get("year", ""))
            if key in keys:
                writer.writerow({**row, "batch_id": batch_id, "source_file": master_path.name})
                keys.remove(key)
                stats["output_rows"] += 1
    tmp.replace(output_path)
    stats["missing_keys"] = len(keys)
    stats["output_bytes"] = output_path.stat().st_size
    return stats


def generate(source_root: Path, output_root: Path, config_path: Path, batch_id: str | None = None) -> Path:
    config = load_config(config_path)
    manifest = RunManifest.create(config["project_version"], config["rule_version"], batch_id)
    start_year = int(config["time"]["start"][:4])
    end_year = int(config["time"]["end"][:4])
    output_root.mkdir(parents=True, exist_ok=True)

    nc_files = []
    for path in source_root.rglob("*.nc"):
        try:
            ym = _year_month(path)
        except ValueError:
            continue
        if config["time"]["start"] <= ym <= config["time"]["end"]:
            nc_files.append(path)
    for index, path in enumerate(sorted(nc_files), 1):
        indicator, ym = _indicator(path), _year_month(path)
        destination = output_root / "ods" / "ocean" / indicator / f"{ym}.csv"
        started = time.perf_counter()
        stats = select_nc(path, destination, config["region"], config["region"]["grid_degrees"], config["depth_targets_m"], manifest.batch_id)
        _record_output(manifest, destination, f"ocean:{indicator}", stats, time.perf_counter() - started)
        print(f"NC {index}/{len(nc_files)} {indicator} {ym}: {stats['output_rows']} rows", flush=True)

    packaged_vessel_dir = source_root / "vessel_zip"
    packaged_master = source_root / "vessel_master" / "vessel_master.csv"
    if packaged_vessel_dir.is_dir() and packaged_master.is_file():
        vessel_dir = packaged_vessel_dir
        master_path = packaged_master
        vessel_pattern = "vessel-teaching-{year}.zip"
    else:
        vessel_dir = next((p for p in source_root.rglob("数据集") if (p / "fishing-vessels-v3.csv").exists()), None)
        if vessel_dir is None:
            raise FileNotFoundError("Cannot locate vessel ZIPs and vessel master data")
        master_path = vessel_dir / "fishing-vessels-v3.csv"
        vessel_pattern = "*{year}.zip"
    vessel_outputs = []
    for year in range(start_year, end_year + 1):
        matches = list(vessel_dir.glob(vessel_pattern.format(year=year)))
        if len(matches) != 1:
            raise FileNotFoundError(f"Expected one vessel ZIP for {year}, got {len(matches)}")
        destination = output_root / "ods" / "vessel" / f"vessel_activity_{year}.csv"
        started = time.perf_counter()
        stats = select_zip(
            matches[0], destination, config["region"], config["region"]["grid_degrees"],
            manifest.batch_id, set(config.get("vessel_representative_months", [])) or None,
        )
        _record_output(manifest, destination, "vessel:activity", stats, time.perf_counter() - started)
        vessel_outputs.append(destination)
        print(f"VESSEL {year}: {stats['output_rows']} / {stats['input_rows']} rows", flush=True)

    master_output = output_root / "ods" / "vessel" / "vessel_master.csv"
    started = time.perf_counter()
    master_stats = filter_vessel_master(master_path, vessel_outputs, master_output, manifest.batch_id)
    _record_output(manifest, master_output, "vessel:master", master_stats, time.perf_counter() - started)

    manifest.metrics = {
        "nc_files": len(nc_files), "vessel_years": end_year - start_year + 1,
        "total_output_files": len(manifest.outputs),
        "total_output_bytes": sum(item["bytes"] for item in manifest.outputs),
    }
    manifest_path = output_root / "manifest.json"
    manifest.write(manifest_path)
    return manifest_path
