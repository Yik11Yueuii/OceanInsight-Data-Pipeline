from __future__ import annotations

import json
from pathlib import Path

from oceaninsight.core import sha256_file
from oceaninsight.generate import filter_vessel_master


project_root = Path("/home/ecs-user/oceaninsight-project1")
activity_dir = project_root / "output/ods/vessel"
master_input = project_root / "source/vessel_master/vessel_master.csv"
output = activity_dir / "vessel_master.csv"
manifest = activity_dir / "vessel_master.manifest.json"
batch_id = "student-vessel-master"

activity_files = sorted(
    activity_dir.glob("vessel_activity_*.csv")
)

if len(activity_files) != 5:
    raise RuntimeError(
        f"应有5个船舶活动CSV，实际为{len(activity_files)}个"
    )

if output.exists() or manifest.exists():
    raise RuntimeError("船舶主数据输出已经存在，停止以避免覆盖")

stats = filter_vessel_master(
    master_input,
    activity_files,
    output,
    batch_id,
)

report = {
    "batch_id": batch_id,
    "source_master": str(master_input),
    "activity_files": [
        {
            "path": str(path),
            "bytes": path.stat().st_size,
        }
        for path in activity_files
    ],
    "output": {
        "path": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
    },
    "stats": stats,
}

tmp_manifest = manifest.with_suffix(".json.tmp")
tmp_manifest.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
tmp_manifest.replace(manifest)

print(json.dumps(report, ensure_ascii=False, indent=2))