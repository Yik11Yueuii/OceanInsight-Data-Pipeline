from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
from scipy.io import netcdf_file

from .core import current_metrics, depth_level, grid_cell, in_region

VARIABLES = {
    "temp": ("TEMP", "temperature_c"),
    "salinity": ("SALINITY", "salinity_g_kg"),
    "oxygen": ("OXYGEN", "oxygen_umol_kg"),
    "u": ("CURRENT_U", "current_u_ms"),
    "v": ("CURRENT_V", "current_v_ms"),
}

OUTPUT_COLUMNS = [
    "year_month", "indicator_code", "depth_m", "depth_level", "source_lat", "source_lon",
    "grid_lat", "grid_lon", "grid_id", "value", "unit", "quality_flag", "source_file", "batch_id"
]


def _nearest_depth_indexes(depths: np.ndarray, targets: list[float]) -> list[int]:
    return sorted({int(np.abs(depths.astype(float) - target).argmin()) for target in targets})


def _year_month(path: Path) -> str:
    match = re.search(r"year_(\d{4})_month_(\d{1,2})", path.name)
    if not match:
        raise ValueError(f"Cannot parse year/month from {path.name}")
    return f"{match.group(1)}-{int(match.group(2)):02d}"


def select_nc(
    nc_path: Path,
    output_path: Path,
    bounds: dict,
    grid_size: float,
    depth_targets: list[float],
    batch_id: str,
) -> dict:
    """Select region/depths from a NetCDF3 file without expanding the global cube."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stats = {"input_cells": 0, "output_rows": 0, "invalid_values": 0}
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with netcdf_file(nc_path, "r", mmap=False) as dataset, tmp_path.open("w", newline="", encoding="utf-8") as target:
        lats = np.asarray(dataset.variables["lat"][:], dtype=float)
        lons = np.asarray(dataset.variables["lon"][:], dtype=float)
        lat_idx = [i for i, lat in enumerate(lats) if bounds["lat_min"] <= lat <= bounds["lat_max"]]
        lon_idx = [i for i, lon in enumerate(lons) if in_region(0, lon, {**bounds, "lat_min": -1, "lat_max": 1})]
        depth_name = "depth_std" if "depth_std" in dataset.variables else "depth" if "depth" in dataset.variables else None
        depths = np.asarray(dataset.variables[depth_name][:], dtype=float) if depth_name else np.array([])
        depth_idx = _nearest_depth_indexes(depths, depth_targets) if depth_name else []
        variables = [name for name in VARIABLES if name in dataset.variables]
        ohc_variables = sorted(name for name in dataset.variables if re.fullmatch(r"OHC\d+", name))
        if not variables and not ohc_variables:
            raise ValueError(f"No supported observation variable in {nc_path}")
        writer = csv.DictWriter(target, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for var_name in variables:
            indicator, unit_name = VARIABLES[var_name]
            values = np.asarray(dataset.variables[var_name][:])
            fill = getattr(dataset.variables[var_name], "_FillValue", None)
            for i in lat_idx:
                for j in lon_idx:
                    for k in depth_idx:
                        stats["input_cells"] += 1
                        value = float(values[i, j, k])
                        invalid = not np.isfinite(value) or (fill is not None and np.isclose(value, float(fill)))
                        if var_name == "salinity" and value >= 900:
                            invalid = True
                        quality = "MISSING" if invalid else "VALID"
                        if invalid:
                            stats["invalid_values"] += 1
                            value_out = ""
                        else:
                            value_out = value
                        grid_lat, grid_lon, grid_id = grid_cell(lats[i], lons[j], grid_size)
                        writer.writerow({
                            "year_month": _year_month(nc_path), "indicator_code": indicator,
                            "depth_m": float(depths[k]), "depth_level": depth_level(depths[k]),
                            "source_lat": float(lats[i]), "source_lon": float(lons[j]),
                            "grid_lat": grid_lat, "grid_lon": grid_lon, "grid_id": grid_id,
                            "value": value_out, "unit": unit_name, "quality_flag": quality,
                            "source_file": nc_path.name, "batch_id": batch_id,
                        })
                        stats["output_rows"] += 1
        if "u" in dataset.variables and "v" in dataset.variables:
            u_values = np.asarray(dataset.variables["u"][:])
            v_values = np.asarray(dataset.variables["v"][:])
            for i in lat_idx:
                for j in lon_idx:
                    for k in depth_idx:
                        u_value, v_value = float(u_values[i, j, k]), float(v_values[i, j, k])
                        if not (np.isfinite(u_value) and np.isfinite(v_value)):
                            continue
                        speed, direction = current_metrics(u_value, v_value)
                        grid_lat, grid_lon, grid_id = grid_cell(lats[i], lons[j], grid_size)
                        common = {
                            "year_month": _year_month(nc_path), "depth_m": float(depths[k]),
                            "depth_level": depth_level(depths[k]), "source_lat": float(lats[i]),
                            "source_lon": float(lons[j]), "grid_lat": grid_lat, "grid_lon": grid_lon,
                            "grid_id": grid_id, "quality_flag": "VALID", "source_file": nc_path.name,
                            "batch_id": batch_id,
                        }
                        writer.writerow({**common, "indicator_code": "CURRENT_SPEED", "value": speed, "unit": "current_speed_ms"})
                        writer.writerow({**common, "indicator_code": "CURRENT_DIRECTION", "value": direction, "unit": "current_direction_deg"})
                        stats["output_rows"] += 2
        for var_name in ohc_variables:
            integration_depth = float(var_name[3:])
            values = np.asarray(dataset.variables[var_name][:])
            fill = getattr(dataset.variables[var_name], "_FillValue", None)
            for i in lat_idx:
                for j in lon_idx:
                    stats["input_cells"] += 1
                    value = float(values[i, j])
                    invalid = (
                        not np.isfinite(value)
                        or abs(value) >= 1e29
                        or (fill is not None and np.isclose(value, float(fill)))
                    )
                    if invalid:
                        stats["invalid_values"] += 1
                    grid_lat, grid_lon, grid_id = grid_cell(lats[i], lons[j], grid_size)
                    writer.writerow({
                        "year_month": _year_month(nc_path), "indicator_code": var_name.upper(),
                        "depth_m": integration_depth, "depth_level": "INTEGRATED",
                        "source_lat": float(lats[i]), "source_lon": float(lons[j]),
                        "grid_lat": grid_lat, "grid_lon": grid_lon, "grid_id": grid_id,
                        "value": "" if invalid else value, "unit": "ocean_heat_content_j_m2",
                        "quality_flag": "MISSING" if invalid else "VALID",
                        "source_file": nc_path.name, "batch_id": batch_id,
                    })
                    stats["output_rows"] += 1
    tmp_path.replace(output_path)
    stats["output_bytes"] = output_path.stat().st_size
    return stats
