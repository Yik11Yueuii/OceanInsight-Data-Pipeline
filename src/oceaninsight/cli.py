from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from .core import RunManifest, sha256_file
from .nc import select_nc
from .vessel import select_zip


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_env_check(_: argparse.Namespace) -> int:
    checks = {
        "python": sys.version.split()[0], "platform": platform.platform(),
        "cpu_count": os.cpu_count(), "disk_free_gib": round(shutil.disk_usage(".").free / 2**30, 2),
        "java": bool(shutil.which("java")), "hdfs": bool(shutil.which("hdfs")),
        "hive": bool(shutil.which("hive")), "spark_submit": bool(shutil.which("spark-submit")),
        "mysql": bool(shutil.which("mysql")),
    }
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


def _run_transform(args: argparse.Namespace, kind: str) -> int:
    config = load_config(args.config)
    manifest = RunManifest.create(config["project_version"], config["rule_version"], args.batch_id)
    source, output = args.input.resolve(), args.output.resolve()
    manifest.sources.append({"path": str(source), "bytes": source.stat().st_size, "sha256": sha256_file(source)})
    if kind == "vessel":
        stats = select_zip(source, output, config["region"], config["region"]["grid_degrees"], manifest.batch_id)
    else:
        stats = select_nc(source, output, config["region"], config["region"]["grid_degrees"], config["depth_targets_m"], manifest.batch_id)
    manifest.metrics[kind] = stats
    manifest.outputs.append({"path": str(output), "bytes": output.stat().st_size, "sha256": sha256_file(output)})
    manifest.write(args.manifest)
    print(json.dumps(manifest.metrics, ensure_ascii=False, indent=2))
    return 0


def cmd_vessel(args: argparse.Namespace) -> int:
    return _run_transform(args, "vessel")


def cmd_nc(args: argparse.Namespace) -> int:
    return _run_transform(args, "nc")


def cmd_npz(args: argparse.Namespace) -> int:
    from .npz import inspect_npz
    report = inspect_npz(args.input, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from .generate import generate
    manifest = generate(args.source_root.resolve(), args.output_root.resolve(), args.config, args.batch_id)
    print(f"Manifest: {manifest}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="OceanInsight student data processor")
    root.add_argument("--config", type=Path, default=Path("conf/pipeline.json"))
    sub = root.add_subparsers(dest="command", required=True)
    env = sub.add_parser("env-check")
    env.set_defaults(func=cmd_env_check)
    for name, func in (("vessel", cmd_vessel), ("nc", cmd_nc)):
        item = sub.add_parser(name)
        item.add_argument("--input", required=True, type=Path)
        item.add_argument("--output", required=True, type=Path)
        item.add_argument("--manifest", required=True, type=Path)
        item.add_argument("--batch-id")
        item.set_defaults(func=func)
    npz_cmd = sub.add_parser("npz", help="Inspect NPZ keys, shapes, dtypes and numeric ranges")
    npz_cmd.add_argument("--input", required=True, type=Path)
    npz_cmd.add_argument("--output", required=True, type=Path)
    npz_cmd.set_defaults(func=cmd_npz)
    generate_cmd = sub.add_parser("generate", help="Convert the complete student source package")
    generate_cmd.add_argument("--source-root", required=True, type=Path)
    generate_cmd.add_argument("--output-root", required=True, type=Path)
    generate_cmd.add_argument("--batch-id")
    generate_cmd.set_defaults(func=cmd_generate)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
