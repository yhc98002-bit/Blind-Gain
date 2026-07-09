#!/usr/bin/env bash

short_ray_tmp_dir() {
  if [[ $# -ne 1 || -z "$1" ]]; then
    echo "short_ray_tmp_dir requires a non-empty run id" >&2
    return 2
  fi

  local digest
  digest="$(printf '%s' "$1" | sha256sum | awk '{print substr($1, 1, 12)}')"
  printf '/tmp/bg-ray-%s\n' "${digest}"
}
