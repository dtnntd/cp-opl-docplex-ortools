"""Bài 1.2 — N-Queens | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: LẤY MẪU CHÍNH THỨC.
  IBMDecisionOptimization/docplex — examples/cp/basic/n_queen.py
  (c) Copyright IBM Corp. 2015, 2022 — Apache License 2.0

Phần DỰNG MÔ HÌNH giữ nguyên như bản gốc của IBM. Chỉ bổ sung: cấu hình engine
cục bộ, tham số n qua dòng lệnh, và dòng RESULT theo giao kèo của tools/runner.py.

Chạy:  python3 models/1.2_nqueens/docplexcp/nqueens_cp.py [n]

GHI CHÚ NGÔN NGỮ (điểm so sánh với OPL):
  all_diff() nhận thẳng generator các BIỂU THỨC `x[i] + i`. Bản OPL cùng engine
  phải khai báo mảng dvar phụ rồi buộc bằng == vì allDifferent của OPL chỉ nhận
  mảng biến. Cùng engine CP Optimizer, cùng mô hình toán — khác biệt ở đây là
  thuần NGÔN NGỮ.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401  — trỏ docplex.cp sang cpoptimizer cục bộ

from docplex.cp.model import CpoModel

NB_QUEEN = int(sys.argv[1]) if len(sys.argv) > 1 else 8

# --- dựng mô hình: nguyên văn ví dụ chính thức của IBM -----------------------
mdl = CpoModel()

# Cột của từng hậu; chỉ số mảng là hàng nên ràng buộc theo hàng đã tự thoả.
x = mdl.integer_var_list(NB_QUEEN, 0, NB_QUEEN - 1, "X")

mdl.add(mdl.all_diff(x))                                        # khác cột
mdl.add(mdl.all_diff(x[i] + i for i in range(NB_QUEEN)))        # khác đường chéo ↗
mdl.add(mdl.all_diff(x[i] - i for i in range(NB_QUEEN)))        # khác đường chéo ↘
# --- hết phần nguyên văn ----------------------------------------------------

msol = mdl.solve(TimeLimit=60, LogVerbosity="Quiet")

if msol:
    print("QUEENS", [msol[v] for v in x])
    for row in range(NB_QUEEN):
        qx = msol[x[row]]
        print(" ".join("Q" if c == qx else "." for c in range(NB_QUEEN)))

infos = msol.get_solver_infos() if msol else {}
print("RESULT " + json.dumps({
    "status": str(msol.get_solve_status()) if msol else "NoSolution",
    "solve_time_s": round(msol.get_solve_time(), 4) if msol else None,
    "branches": infos.get("NumberOfBranches"),
    "fails": infos.get("NumberOfFails"),
    "n": NB_QUEEN,
}))
