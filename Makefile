PY := python3
NB := $(wildcard notebooks/*.ipynb)

.PHONY: help setup check run run-all bench notebooks html pages clean

help:  ## Liệt kê các lệnh
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup:  ## Cài thư viện Python
	$(PY) -m pip install --break-system-packages -r requirements.txt

check:  ## Kiểm tra cả 3 engine (OPL / DOcplex.cp / OR-Tools) gọi được
	$(PY) tools/check_env.py

run:  ## Chạy 3 chiều của MỘT bài:  make run P=models/2.1_jobshop
	@test -n "$(P)" || { echo "Dùng: make run P=models/<bài>"; exit 2; }
	$(PY) tools/runner.py --suite $(P)

run-all:  ## Chạy toàn bộ 6 bài × 3 chiều
	$(PY) tools/runner.py --all --json results/runs.json --csv results/runs.csv \
	  --solutions results/solutions.json

bench:  ## Benchmark định lượng bài 3.2 (bài duy nhất có đo hiệu năng)
	$(PY) tools/bench_timetable.py --csv results/bench.csv

notebooks:  ## Chạy lại toàn bộ notebook tại chỗ
	jupyter nbconvert --to notebook --execute --inplace $(NB)

html: notebooks  ## Xuất báo cáo ra report/html/
	SKIP_EXECUTE=1 bash report/build.sh

pages: ## Đẩy report/html/ lên nhánh gh-pages (GitHub Pages)
	bash report/publish.sh

clean:  ## Xoá kết quả trung gian
	rm -rf report/html/* results/*.json results/*.csv .ipynb_checkpoints notebooks/.ipynb_checkpoints
