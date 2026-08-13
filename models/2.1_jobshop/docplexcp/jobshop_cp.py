"""Bài 2.1 — Job-shop scheduling | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: LẤY MẪU CHÍNH THỨC.
  IBMDecisionOptimization/docplex — examples/cp/visu/job_shop_basic.py
  Source file provided under Apache License, Version 2.0, January 2004,
  http://www.apache.org/licenses/
  (c) Copyright IBM Corp. 2015, 2022

Phần DỰNG MÔ HÌNH (interval_var / end_before_start / no_overlap / minimize) giữ
NGUYÊN VĂN bản gốc của IBM. Bổ sung:
  - đọc dữ liệu từ data/jobshop/ft06.dat — cùng một file với chiều OPL, thay cho
    file jobshop_ft06.data riêng của bản gốc (nội dung số liệu y hệt, chỉ khác
    cách viết); xem NOTES.md mục (c);
  - cấu hình engine cục bộ qua tools/cpo_env.py;
  - dòng RESULT theo giao kèo của tools/runner.py;
  - biểu đồ Gantt bằng matplotlib thay cho docplex.cp.utils_visu của bản gốc —
    utils_visu cần môi trường đồ hoạ tương tác, không chạy được khi gọi qua runner.

Chạy:  python3 models/2.1_jobshop/docplexcp/jobshop_cp.py [data.dat] [--gantt FILE]

GHI CHÚ NGÔN NGỮ (điểm so sánh với OPL — cùng engine CP Optimizer):
  Bản OPL khai báo `dvar sequence mchs[m] in all(j, o : Ops[j][o].mch == m) itvs[j][o]`
  — một câu lệnh vừa lọc theo điều kiện, vừa gom nhóm, vừa tạo BIẾN THỨ TỰ. Python
  không có cú pháp khai báo tương ứng: bản IBM phải dựng tay danh sách
  machine_operations bằng hai vòng lặp rồi mới gọi no_overlap(mops). Cùng một ràng
  buộc, cùng một engine — khác biệt ở đây là thuần NGÔN NGỮ.
"""

import builtins
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve()
_ROOT = _HERE.parents[3]
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(0, str(_HERE.parents[1]))

import cpo_env  # noqa: F401,E402  — trỏ docplex.cp sang cpoptimizer cục bộ
import jobshop_data  # noqa: E402  — đọc data/jobshop/*.dat, dùng chung với chiều OPL

from docplex.cp.model import *  # noqa: F401,F403,E402  (bản gốc IBM import kiểu này)

# CẢNH BÁO NGÔN NGỮ: `from docplex.cp.model import *` che mất các hàm dựng sẵn của
# Python — max, min, sum, abs, round... đều bị thay bằng hàm dựng BIỂU THỨC của
# docplex. Trong khối mô hình dưới đây đó chính là điều ta muốn (max trên các
# end_of(...) phải sinh ra biểu thức, không phải tính ngay). Nhưng ở phần đọc kết
# quả thì phải gọi lại tường minh qua `builtins.` để không nhận về một CpoExpr.

# -----------------------------------------------------------------------------
# Tham số dòng lệnh
# -----------------------------------------------------------------------------
argv = sys.argv[1:]
gantt_path = None
if "--gantt" in argv:
    i = argv.index("--gantt")
    gantt_path = argv[i + 1]
    del argv[i : i + 2]
DATA = argv[0] if argv else str(_ROOT / "data" / "jobshop" / "ft06.dat")

# -----------------------------------------------------------------------------
# Initialize the problem data
# -----------------------------------------------------------------------------
# Bản gốc đọc file jobshop_ft06.data (định dạng OR-Library). Ở đây đọc chính file
# .dat mà chiều OPL dùng, để cả ba chiều chắc chắn chạy cùng một instance.
NB_JOBS, NB_MACHINES, MACHINES, DURATION = jobshop_data.load(DATA)

# -----------------------------------------------------------------------------
# Build the model  — NGUYÊN VĂN ví dụ chính thức của IBM
# -----------------------------------------------------------------------------

# Create model
mdl = CpoModel()

# Create one interval variable per job operation
job_operations = [[interval_var(size=DURATION[j][m], name='O{}-{}'.format(j, m)) for m in range(NB_MACHINES)] for j in range(NB_JOBS)]

# Each operation must start after the end of the previous
for j in range(NB_JOBS):
    for s in range(1, NB_MACHINES):
        mdl.add(end_before_start(job_operations[j][s - 1], job_operations[j][s]))

# Force no overlap for operations executed on a same machine
machine_operations = [[] for m in range(NB_MACHINES)]
for j in range(NB_JOBS):
    for s in range(NB_MACHINES):
        machine_operations[MACHINES[j][s]].append(job_operations[j][s])
for mops in machine_operations:
    mdl.add(no_overlap(mops))

# Minimize termination date
mdl.add(minimize(max(end_of(job_operations[i][NB_MACHINES - 1]) for i in range(NB_JOBS))))
# --- hết phần nguyên văn -----------------------------------------------------

# -----------------------------------------------------------------------------
# Giải và in kết quả
# -----------------------------------------------------------------------------
res = mdl.solve(TimeLimit=60, LogVerbosity="Quiet")

starts = None
makespan = None
if res:
    starts = [[res.get_var_solution(job_operations[j][o]).get_start() for o in range(NB_MACHINES)] for j in range(NB_JOBS)]
    makespan = builtins.max(
        res.get_var_solution(job_operations[j][o]).get_end()
        for j in range(NB_JOBS)
        for o in range(NB_MACHINES)
    )
    for j in range(NB_JOBS):
        print(" ".join(str(s) for s in starts[j]))
    if gantt_path:
        out = jobshop_data.write_gantt(
            gantt_path, NB_JOBS, NB_MACHINES, MACHINES, starts, DURATION,
            f"Job-shop {pathlib.Path(DATA).stem} — DOcplex.cp / CP Optimizer (makespan {makespan})",
        )
        print("GANTT", out)

infos = res.get_solver_infos() if res else {}
print("RESULT " + json.dumps({
    "status": str(res.get_solve_status()) if res else "NoSolution",
    "objective": makespan,
    "solve_time_s": builtins.round(res.get_solve_time(), 4) if res else None,
    "branches": infos.get("NumberOfBranches"),
    "fails": infos.get("NumberOfFails"),
    "nb_jobs": NB_JOBS,
    "nb_machines": NB_MACHINES,
    "nb_operations": NB_JOBS * NB_MACHINES,
    "data": str(pathlib.Path(DATA).name),
}))
