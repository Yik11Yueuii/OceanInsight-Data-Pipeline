#!/usr/bin/env bash
set -euo pipefail
cat >&2 <<'EOF'
项目一 ECS 环境已经实测完成并封板。本脚本不再执行任何安装，避免破坏已验证环境。
请运行 preflight.sh 做只读检查；ECS 重启后运行 recover_services.sh。
EOF
