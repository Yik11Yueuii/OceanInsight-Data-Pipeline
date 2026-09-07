from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def normalize_lon(lon: float) -> float:
    """TODO 1: Normalize longitude to [-180, 180), keeping 180 as -180."""
    raise NotImplementedError("TODO 1: complete normalize_lon")


def grid_cell(lat: float, lon: float, size: float = 2.0) -> tuple[float, float, str]:
    """TODO 2: Return grid lower-left latitude, longitude and grid id."""
    raise NotImplementedError("TODO 2: complete grid_cell")


def in_region(lat: float, lon: float, bounds: dict) -> bool:
    """TODO 3: Normalize longitude and test the inclusive region bounds."""
    raise NotImplementedError("TODO 3: complete in_region")


def depth_level(depth_m: float) -> str:
    """TODO 4: Classify depth using 10 m, 200 m and 750 m boundaries."""
    raise NotImplementedError("TODO 4: complete depth_level")


def current_metrics(u: float, v: float) -> tuple[float, float]:
    """TODO 5: Return speed and direction-to clockwise from north."""
    raise NotImplementedError("TODO 5: complete current_metrics")


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class RunManifest:
    batch_id: str
    project_version: str
    rule_version: str
    started_at: str
    sources: list[dict]
    outputs: list[dict]
    metrics: dict

    @classmethod
    def create(cls, project_version: str, rule_version: str, batch_id: str | None = None):
        now = datetime.now(timezone.utc)
        return cls(
            batch_id=batch_id or now.strftime("%Y%m%dT%H%M%SZ"),
            project_version=project_version,
            rule_version=rule_version,
            started_at=now.isoformat(),
            sources=[],
            outputs=[],
            metrics={},
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_months(start: str, end: str) -> Iterable[str]:
    year, month = map(int, start.split("-"))
    end_year, end_month = map(int, end.split("-"))
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1
