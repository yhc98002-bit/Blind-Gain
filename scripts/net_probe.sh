#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-reports/network_probe.md}"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"
DOMESTIC_PROXY="${DOMESTIC_PROXY:-}"
PYPI_MIRROR="${PYPI_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}"

mkdir -p "$(dirname "$OUT")"

probe_curl() {
  local label="$1"
  local url="$2"
  shift 2
  local tmp
  tmp="$(mktemp)"
  local code time size speed rc
  set +e
  read -r code time size speed < <(curl -L --max-time 30 --connect-timeout 10 -o "$tmp" -w "%{http_code} %{time_total} %{size_download} %{speed_download}" "$@" "$url")
  rc=$?
  set -e
  rm -f "$tmp"
  printf '| %s | `%s` | %s | %s | %s | %s | %s |\n' "$label" "$url" "$rc" "$code" "$time" "$size" "$speed"
}

{
  echo "# Network Probe"
  echo
  echo "- Timestamp: $(date -Is)"
  echo "- Host: $(hostname)"
  echo "- PROXY_URL: \`$PROXY_URL\`"
  echo "- DOMESTIC_PROXY: \`${DOMESTIC_PROXY:-none}\`"
  echo
  echo "| Route | URL | curl rc | HTTP | seconds | bytes | bytes/s |"
  echo "| --- | --- | ---: | ---: | ---: | ---: | ---: |"

  if [[ -n "$DOMESTIC_PROXY" ]]; then
    probe_curl "ModelScope domestic proxy" "https://www.modelscope.cn/api/v1/models" --proxy "$DOMESTIC_PROXY"
  else
    probe_curl "ModelScope direct" "https://www.modelscope.cn/api/v1/models"
  fi

  probe_curl "GitHub proxy" "https://github.com/" --proxy "$PROXY_URL"
  probe_curl "HuggingFace proxy" "https://huggingface.co/" --proxy "$PROXY_URL"
  probe_curl "PyPI mirror direct" "$PYPI_MIRROR"
  probe_curl "ModelScope small file" "https://modelscope.cn/api/v1/datasets/modelscope/hellaswag/repo/files?Revision=master&Recursive=false"
  probe_curl "HF small file proxy" "https://huggingface.co/bert-base-uncased/raw/main/config.json" --proxy "$PROXY_URL"
} > "$OUT"

echo "$OUT"

