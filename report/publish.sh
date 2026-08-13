#!/usr/bin/env bash
# Đẩy report/html/ lên nhánh gh-pages của remote origin.
#
# Dùng:  bash report/publish.sh        (hoặc: make pages)
#
# Nhánh gh-pages là nhánh RỜI, không có tổ tiên chung với main: nó chỉ chứa
# HTML đã dựng, không chứa mã nguồn. Mỗi lần publish ghi đè toàn bộ nội dung
# nhánh đó bằng report/html/ hiện tại, nên nhánh này luôn khớp bản build mới
# nhất chứ không tích luỹ file cũ.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HTML_DIR="report/html"
BRANCH="gh-pages"

if [[ ! -f "$HTML_DIR/index.html" ]]; then
  echo "Chưa có $HTML_DIR/index.html — chạy 'make html' trước." >&2
  exit 1
fi

REMOTE_URL="$(git remote get-url origin)"

# Cây làm việc tạm, tách khỏi cây chính để không đụng file đang sửa dở.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -r "$HTML_DIR/." "$STAGE"/
touch "$STAGE/.nojekyll"   # tắt Jekyll: nó bỏ qua file bắt đầu bằng '_'

git -C "$STAGE" init -b "$BRANCH" -q
git -C "$STAGE" add -A
git -C "$STAGE" commit -q -m "Bản HTML đã dựng — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git -C "$STAGE" remote add origin "$REMOTE_URL"

# --force vì lịch sử nhánh tạm không nối tiếp lần publish trước; đây là nhánh
# chỉ chứa sản phẩm build nên viết đè là đúng ý, không mất mã nguồn nào.
git -C "$STAGE" push -q --force origin "$BRANCH"

echo "==> Đã đẩy $(ls -1 "$HTML_DIR" | wc -l) file lên nhánh $BRANCH"
echo "    $(git remote get-url origin | sed -E 's#https://github.com/([^/]+)/(.+)\.git#https://\1.github.io/\2/#')"
