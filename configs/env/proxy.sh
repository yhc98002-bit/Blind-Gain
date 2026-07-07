#!/usr/bin/env bash

# Source this file only in commands that need the international proxy.
# ModelScope and other domestic downloads should generally run without it.
export PROXY_URL="${PROXY_URL:-http://127.0.0.1:7890}"
export http_proxy="$PROXY_URL"
export https_proxy="$PROXY_URL"
export HTTP_PROXY="$PROXY_URL"
export HTTPS_PROXY="$PROXY_URL"

