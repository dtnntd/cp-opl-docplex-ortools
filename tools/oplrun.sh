#!/usr/bin/env bash
# Chạy model OPL (.mod [+ .dat ...]) bằng oplrun.exe của CPLEX Studio (Windows) từ trong WSL.
#
# Vì sao cần wrapper: oplrun.exe là binary Windows nên chỉ hiểu đường dẫn kiểu
# Windows. File nguồn của dự án lại nằm trong filesystem WSL. wslpath -w dịch
# /home/... thành \\wsl.localhost\<Distro>\home\... — oplrun.exe đọc được qua UNC.
#
# Dùng:  tools/oplrun.sh models/2.1_jobshop/opl/sched_jobshop.mod data/jobshop/ft06.dat
set -euo pipefail

CPS="${CPLEX_STUDIO_DIR:-/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222}"
OPLRUN="$CPS/opl/bin/x64_win64/oplrun.exe"

if [[ ! -x "$OPLRUN" ]]; then
  echo "Không tìm thấy oplrun.exe tại: $OPLRUN" >&2
  echo "Đặt biến CPLEX_STUDIO_DIR trỏ tới thư mục cài CPLEX Studio nếu bạn cài chỗ khác." >&2
  exit 127
fi

if [[ $# -lt 1 ]]; then
  echo "Dùng: $0 <model.mod> [data.dat ...] [-- <tham số oplrun>]" >&2
  exit 2
fi

args=()
for f in "$@"; do
  if [[ -e "$f" ]]; then
    args+=("$(wslpath -w "$(realpath "$f")")")
  else
    # không phải file (ví dụ cờ -v, -p) thì giữ nguyên
    args+=("$f")
  fi
done

exec "$OPLRUN" "${args[@]}"
