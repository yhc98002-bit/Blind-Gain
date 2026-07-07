#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain}"
ssh an29 "cd '$ROOT' && bash -lc '$*'"

