from __future__ import annotations

import json
from pathlib import Path

import numpy as np


NPZ_WARNING = (
    "NPZ samples do not contain real dates, coordinates, or depth-value arrays; "
    "do not join them to ocean or vessel business data."
)


def inspect_npz(input_path: Path, output_path: Path) -> dict:
    """Write a small metadata/statistics report without expanding NPZ to CSV."""
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    arrays: dict[str, dict] = {}
    with np.load(input_path, allow_pickle=False) as container:
        for key in sorted(container.files):
            value = np.asarray(container[key])
            finite = np.isfinite(value) if np.issubdtype(value.dtype, np.number) else None
            item = {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "elements": int(value.size),
            }
            if finite is not None:
                valid = value[finite]
                item.update({
                    "finite_elements": int(valid.size),
                    "missing_elements": int(value.size - valid.size),
                    "min": float(valid.min()) if valid.size else None,
                    "max": float(valid.max()) if valid.size else None,
                    "mean": float(valid.mean()) if valid.size else None,
                })
            arrays[key] = item
    report = {
        "source_file": input_path.name,
        "arrays": arrays,
        "warning": NPZ_WARNING,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(output_path)
    return report
