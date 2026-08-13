#!/usr/bin/env bash
# Chạy lại toàn bộ notebook rồi xuất báo cáo ra HTML.
#
# Dùng:  bash report/build.sh        (hoặc: make html)
#        SKIP_EXECUTE=1 bash report/build.sh   -> chỉ xuất HTML, không chạy lại
#
# Notebook được chạy lại từ kernel mới trước khi xuất, nên mọi con số trong báo
# cáo là số vừa sinh ra chứ không phải số cũ còn sót trong file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

NB_DIR="notebooks"
OUT_DIR="report/html"
mkdir -p "$OUT_DIR"

shopt -s nullglob
notebooks=("$NB_DIR"/*.ipynb)
shopt -u nullglob

if [[ ${#notebooks[@]} -eq 0 ]]; then
  echo "Chưa có notebook nào trong $NB_DIR/ — bỏ qua." >&2
  exit 0
fi

if [[ "${SKIP_EXECUTE:-0}" != "1" ]]; then
  echo "==> Chạy lại ${#notebooks[@]} notebook (kernel mới, không giới hạn thời gian mỗi ô)"
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 \
    "${notebooks[@]}"
fi

echo "==> Xuất HTML"
# Template riêng: kế thừa `lab`, chỉ đè CSS bảng. Lý do ở report/nbtemplate/
# cpreport/index.html.j2 — CSS gốc đặt table-layout:fixed nên bảng nhiều cột
# bị chia đều bề rộng bất kể nội dung.
jupyter nbconvert --to html \
  --TemplateExporter.extra_template_basedirs="$ROOT/report/nbtemplate" \
  --template cpreport \
  --output-dir "$OUT_DIR" "${notebooks[@]}"

# ---- trang mục lục ---------------------------------------------------------
{
  cat <<'HTML'
<!DOCTYPE html>
<meta charset="utf-8">
<title>Báo cáo khảo sát CP — OPL vs DOcplex.cp vs OR-Tools</title>
<style>
  body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         max-width: 46rem; margin: 3rem auto; padding: 0 1.5rem; line-height: 1.6; }
  h1 { border-bottom: 2px solid #ddd; padding-bottom: .4rem; }
  ol { padding-left: 1.4rem; }
  li { margin: .6rem 0; }
  a { color: #0b5cad; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .sub { color: #666; font-size: .9em; }
</style>
<h1>Báo cáo khảo sát Constraint Programming</h1>
<p class="sub">So sánh IBM ILOG OPL, DOcplex.cp và Google OR-Tools trên 6 bài toán.
OPL và DOcplex.cp chung engine CP Optimizer nên tách được khác biệt do <em>ngôn ngữ</em>;
DOcplex.cp và OR-Tools chung Python nên tách được khác biệt do <em>engine</em>.</p>
<ol>
HTML
  for nb in "${notebooks[@]}"; do
    base="$(basename "${nb%.ipynb}")"
    case "$base" in
      00_intro_taxonomy) title="Dẫn nhập — phân loại ràng buộc và phương pháp ba chiều" ;;
      01_combinatorial)  title="Phần 1 — Tổ hợp: tô màu đồ thị, N-Queens" ;;
      02_scheduling)     title="Phần 2 — Lập lịch: job-shop, phân ca nhân viên" ;;
      03_assignment)     title="Phần 3 — Phân công: lịch thi đấu, thời khoá biểu" ;;
      99_comparison)     title="Tổng hợp — bảng so sánh và kết luận" ;;
      *) title="$(echo "$base" | sed -E 's/^[0-9]+_//; s/_/ /g')" ;;
    esac
    echo "  <li><a href=\"${base}.html\">${title}</a></li>"
  done
  cat <<'HTML'
</ol>
HTML
} > "$OUT_DIR/index.html"

echo "==> Xong. Mở: $OUT_DIR/index.html"
ls -1 "$OUT_DIR"
