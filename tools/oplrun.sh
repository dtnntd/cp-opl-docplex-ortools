#!/usr/bin/env bash
# Chạy model OPL (.mod [+ .dat ...]) bằng `oplrun` của IBM ILOG CPLEX Optimization Studio.
#
# Vì sao cần wrapper: hai lý do.
#   1. oplrun không nằm trong PATH sau khi cài, và mỗi hệ điều hành đặt nó ở một
#      thư mục con khác nhau. Script này dò tìm thay cho người dùng.
#   2. Khi Python/shell chạy trong WSL còn CPLEX Studio là bản Windows (cấu hình
#      của máy gốc dự án), oplrun.exe chỉ hiểu đường dẫn kiểu Windows trong khi
#      file nguồn nằm trong filesystem Linux. `wslpath -w` dịch /home/... thành
#      \\wsl.localhost\<Distro>\home\... — oplrun.exe đọc được qua UNC.
#      Chạy native (Linux, macOS, Windows) thì KHÔNG dịch gì cả.
#
# Dùng:  tools/oplrun.sh models/2.1_jobshop/opl/sched_jobshop.mod data/jobshop/ft06.dat
#        tools/oplrun.sh --which        # chỉ in đường dẫn oplrun dò được rồi thoát
set -euo pipefail

# --------------------------------------------------------------------------
# Thư mục con chứa oplrun BÊN TRONG thư mục cài CPLEX Studio.
#
# ĐÃ KIỂM CHỨNG trên máy gốc của dự án (WSL + CPLEX Studio Community 22.2 trên
# ổ D: của Windows): `opl/bin/` chỉ chứa đúng một thư mục `x64_win64`, trong đó
# có `oplrun.exe`. Nghĩa là nhánh Windows dưới đây là chắc chắn đúng.
#
# THEO TÀI LIỆU IBM (chưa kiểm chứng được vì máy này không có bản Linux/macOS —
# cần người dùng hai hệ đó xác nhận hộ):
#   opl/bin/x86-64_linux/oplrun
#   opl/bin/x86-64_osx/oplrun     (Intel)
#   opl/bin/arm64_osx/oplrun      (Apple Silicon)
# --------------------------------------------------------------------------

OS_NAME="$(uname -s)"

# Thứ tự thử các thư mục con, ưu tiên binary native của hệ đang chạy.
case "$OS_NAME" in
  Linux)
    # Trên WSL vẫn để nhánh win64 phía sau: nếu máy không có bản Linux thì rơi
    # xuống bản Windows gọi qua interop (đúng cấu hình máy gốc dự án).
    ARCH_SUBDIRS=(
      "opl/bin/x86-64_linux/oplrun"
      "opl/bin/x64_win64/oplrun.exe"
    )
    ;;
  Darwin)
    ARCH_SUBDIRS=(
      "opl/bin/arm64_osx/oplrun"
      "opl/bin/x86-64_osx/oplrun"
    )
    ;;
  MINGW* | MSYS* | CYGWIN*)
    ARCH_SUBDIRS=("opl/bin/x64_win64/oplrun.exe")
    ;;
  *)
    # Hệ lạ: thử hết, chậm hơn chút nhưng không bỏ sót.
    ARCH_SUBDIRS=(
      "opl/bin/x86-64_linux/oplrun"
      "opl/bin/arm64_osx/oplrun"
      "opl/bin/x86-64_osx/oplrun"
      "opl/bin/x64_win64/oplrun.exe"
    )
    ;;
esac

# Ghi lại mọi chỗ đã dò để in ra khi thất bại. Mọi hàm dưới đây ghi kết quả vào
# biến toàn cục (RESOLVED, TRIED) thay vì in ra stdout: chạy trong $( ) sẽ tạo
# subshell và nuốt mất TRIED.
TRIED=()
STUDIO_ROOTS=()
RESOLVED=""

# Điền STUDIO_ROOTS bằng các thư mục cài CPLEX Studio ứng viên trên máy này.
# Bản đầy đủ (CPLEX_Studio<ver>) được xếp TRƯỚC bản Community
# (CPLEX_Studio_Community<ver>) vì bản đầy đủ không có giới hạn không gian tìm
# kiếm; trong mỗi nhóm thì phiên bản mới (số hiệu lớn) đứng trước. Glob bắt được
# mọi số hiệu: 221, 222, 2211, 2212, ...
collect_studio_roots() {
  local -a bases=()
  local d i

  case "$OS_NAME" in
    Linux)
      bases+=("/opt/ibm/ILOG" "/opt/IBM/ILOG" "$HOME/ibm/ILOG" "$HOME/IBM/ILOG")
      # WSL: bản Windows nằm trên ổ đĩa Windows được mount vào /mnt/<ổ>.
      if [[ -d /mnt ]]; then
        for d in /mnt/*; do
          [[ -d "$d/Program Files/IBM/ILOG" ]] && bases+=("$d/Program Files/IBM/ILOG")
        done
      fi
      ;;
    Darwin)
      bases+=("/Applications" "$HOME/Applications" "/opt/ibm/ILOG")
      ;;
    MINGW* | MSYS* | CYGWIN*)
      # Git Bash mount ổ C: vào /c, Cygwin vào /cygdrive/c.
      bases+=(
        "/c/Program Files/IBM/ILOG" "/c/Program Files (x86)/IBM/ILOG"
        "/cygdrive/c/Program Files/IBM/ILOG"
      )
      ;;
    *)
      bases+=("/opt/ibm/ILOG" "/Applications" "$HOME/ibm/ILOG")
      ;;
  esac

  local base pat
  local -a hits
  local had_nullglob=0
  shopt -q nullglob && had_nullglob=1
  shopt -s nullglob
  for base in "${bases[@]}"; do
    [[ -d "$base" ]] || continue
    for pat in '/CPLEX_Studio[0-9]*' '/CPLEX_Studio_Community*'; do
      hits=("$base"$pat)
      # Glob trả về thứ tự tăng dần, duyệt ngược để phiên bản mới đứng trước.
      for ((i = ${#hits[@]} - 1; i >= 0; i--)); do
        [[ -d "${hits[i]}" ]] && STUDIO_ROOTS+=("${hits[i]}")
      done
    done
  done
  [[ $had_nullglob -eq 1 ]] || shopt -u nullglob
}

# Thử một thư mục cài: đặt RESOLVED nếu tìm thấy oplrun trong đó.
probe_studio_dir() {
  local root="$1" sub cand
  for sub in "${ARCH_SUBDIRS[@]}"; do
    cand="$root/$sub"
    TRIED+=("$cand")
    if [[ -x "$cand" ]]; then
      RESOLVED="$cand"
      return 0
    fi
  done
  return 1
}

resolve_oplrun() {
  local root

  # 1. Trỏ thẳng file thực thi.
  if [[ -n "${OPLRUN_EXEC:-}" ]]; then
    TRIED+=("\$OPLRUN_EXEC = $OPLRUN_EXEC")
    if [[ -x "$OPLRUN_EXEC" ]]; then
      RESOLVED="$OPLRUN_EXEC"
      return 0
    fi
    return 1
  fi

  # 2. Trỏ thư mục cài CPLEX Studio.
  if [[ -n "${CPLEX_STUDIO_DIR:-}" ]]; then
    probe_studio_dir "$CPLEX_STUDIO_DIR" && return 0
    return 1
  fi

  # 3. Dò các vị trí cài mặc định.
  collect_studio_roots
  for root in ${STUDIO_ROOTS[@]+"${STUDIO_ROOTS[@]}"}; do
    probe_studio_dir "$root" && return 0
  done

  # 4. Cuối cùng: có sẵn trong PATH thì cũng dùng.
  TRIED+=("oplrun (trong \$PATH)")
  if RESOLVED="$(command -v oplrun 2>/dev/null)"; then
    return 0
  fi
  RESOLVED=""
  return 1
}

if resolve_oplrun; then
  OPLRUN="$RESOLVED"
else
  {
    echo "Không tìm thấy oplrun của IBM ILOG CPLEX Optimization Studio."
    echo "Hệ điều hành nhận diện được: $OS_NAME"
    echo "Đã dò các vị trí sau:"
    if [[ ${#TRIED[@]} -eq 0 ]]; then
      echo "  (không có thư mục cài CPLEX Studio nào ở các vị trí mặc định)"
    else
      printf '  %s\n' "${TRIED[@]}"
    fi
    echo
    echo "Chỉ định thủ công bằng một trong hai biến môi trường:"
    echo "  OPLRUN_EXEC       trỏ thẳng tới file thực thi oplrun (hoặc oplrun.exe)"
    echo "  CPLEX_STUDIO_DIR  trỏ tới thư mục cài CPLEX Studio, ví dụ"
    echo "                    /opt/ibm/ILOG/CPLEX_Studio2211 (Linux)"
    echo "                    /Applications/CPLEX_Studio2211 (macOS)"
    echo "                    '/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222' (WSL)"
  } >&2
  exit 127
fi

if [[ "${1:-}" == "--which" ]]; then
  printf '%s\n' "$OPLRUN"
  exit 0
fi

if [[ $# -lt 1 ]]; then
  echo "Dùng: $0 <model.mod> [data.dat ...] [-- <tham số oplrun>]" >&2
  echo "      $0 --which" >&2
  exit 2
fi

# Chỉ dịch đường dẫn khi đang chạy shell Linux/WSL mà binary lại là .exe của
# Windows (gọi qua WSL interop). Chạy native thì truyền nguyên trạng — trên
# Linux/macOS thật không có lệnh wslpath.
NEED_WSLPATH=0
if [[ "$OS_NAME" == Linux && "$OPLRUN" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
  NEED_WSLPATH=1
fi

args=()
for f in "$@"; do
  if [[ -e "$f" ]]; then
    p="$(realpath "$f")"
    if [[ $NEED_WSLPATH -eq 1 ]]; then
      p="$(wslpath -w "$p")"
    fi
    args+=("$p")
  else
    # không phải file (ví dụ cờ -v, -p) thì giữ nguyên
    args+=("$f")
  fi
done

exec "$OPLRUN" "${args[@]}"
