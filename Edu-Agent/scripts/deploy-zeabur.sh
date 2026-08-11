#!/usr/bin/env bash
# Edu-Agent 一键部署到 Zeabur（需 API Token）
#
# 用法：
#   export ZEABUR_TOKEN=你的token   # https://dash.zeabur.com/account/api-tokens
#   export PUBLIC_DOMAIN=edu-agent   # 可选，默认 edu-agent
#   export ZEABUR_REGION=tpe0        # 可选，默认 tpe0（台北）
#   bash scripts/deploy-zeabur.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TOKEN="${ZEABUR_TOKEN:-}"
DOMAIN="${PUBLIC_DOMAIN:-edu-agent}"
REGION="${ZEABUR_REGION:-tpe0}"
PROJECT_NAME="${ZEABUR_PROJECT_NAME:-edu-agent}"

if [[ -z "$TOKEN" ]]; then
  echo "错误：请先设置 ZEABUR_TOKEN"
  echo "  1. 打开 https://dash.zeabur.com/account/api-tokens 创建 Token"
  echo "  2. export ZEABUR_TOKEN=你的token"
  exit 1
fi

echo ">>> 登录 Zeabur CLI..."
npx zeabur@latest auth login --token "$TOKEN" -i=false

echo ">>> 查找或创建项目: $PROJECT_NAME ($REGION)..."
PROJECT_ID="$(npx zeabur@latest project list -i=false --json 2>/dev/null | python3 -c "
import json, sys
name = '$PROJECT_NAME'
try:
    data = json.load(sys.stdin)
except Exception:
    data = []
items = data if isinstance(data, list) else data.get('projects', data.get('items', []))
for p in items:
    if p.get('name') == name:
        print(p.get('_id') or p.get('id') or '')
        break
" || true)"

if [[ -z "$PROJECT_ID" ]]; then
  echo ">>> 创建新项目..."
  CREATE_OUT="$(npx zeabur@latest project create -n "$PROJECT_NAME" -r "$REGION" -i=false --json 2>&1)"
  PROJECT_ID="$(echo "$CREATE_OUT" | python3 -c "
import json, sys
raw = sys.stdin.read()
try:
    data = json.loads(raw)
    print(data.get('_id') or data.get('id') or '')
except Exception:
    pass
" || true)"
fi

if [[ -z "$PROJECT_ID" ]]; then
  echo "无法获取项目 ID，请在 Dashboard 手动创建项目后设置："
  echo "  export ZEABUR_PROJECT_ID=你的项目ID"
  if [[ -n "${ZEABUR_PROJECT_ID:-}" ]]; then
    PROJECT_ID="$ZEABUR_PROJECT_ID"
  else
    exit 1
  fi
fi

echo ">>> 部署模板到项目 $PROJECT_ID（域名前缀: $DOMAIN）..."
npx zeabur@latest template deploy -i=false \
  -f "$ROOT_DIR/zeabur-template.yaml" \
  --project-id "$PROJECT_ID" \
  --var "PUBLIC_DOMAIN=$DOMAIN"

echo ""
echo ">>> 部署已触发。请在 Dashboard 查看构建进度："
echo "    https://dash.zeabur.com/"
echo ""
echo ">>> 部署完成后访问："
echo "    https://${DOMAIN}.zeabur.app"
echo "    https://${DOMAIN}.zeabur.app/api/health"
