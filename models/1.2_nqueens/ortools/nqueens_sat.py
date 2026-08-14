"""Bài 1.2 — N-Queens | Chiều OR-Tools (engine CP-SAT)

Nguồn: LẤY MẪU CHÍNH THỨC.
  https://developers.google.com/optimization/cp/queens

Phần dựng mô hình theo đúng ví dụ chính thức của Google; bổ sung tham số n qua
dòng lệnh và dòng RESULT theo giao kèo của tools/runner.py.

Chạy:  python3 models/1.2_nqueens/ortools/nqueens_sat.py [n]

GHI CHÚ ENGINE (điểm so sánh với DOcplex.cp — cùng Python, khác engine):
  Cú pháp gần như trùng khít bản DOcplex.cp: AddAllDifferent cũng nhận generator
  biểu thức. Khác biệt nằm ở BÊN DƯỚI: CP-SAT dịch toàn bộ mô hình xuống mệnh đề
  SAT + lazy clause generation, nên báo số CONFLICTS (xung đột học được) thay vì
  FAILS (nhánh chết) như CP Optimizer. Hai con số này KHÔNG so sánh trực tiếp
  được với nhau — chúng đếm hai thứ khác nhau.

  CP-SAT chạy đa luồng nên số liệu đổi giữa các lần chạy; ở đây cố định
  num_search_workers=1 và random_seed=0 để con số trong NOTES.md tái lập được.
"""

import json
import sys

from ortools.sat.python import cp_model

BOARD_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 8

model = cp_model.CpModel()

# queens[i] = cột của hậu ở hàng i.
queens = [model.new_int_var(0, BOARD_SIZE - 1, f"x_{i}") for i in range(BOARD_SIZE)]

model.add_all_different(queens)                                          # khác cột
model.add_all_different(queens[i] + i for i in range(BOARD_SIZE))        # khác đường chéo ↗
model.add_all_different(queens[i] - i for i in range(BOARD_SIZE))        # khác đường chéo ↘

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 1   # tái lập được số liệu (xem docstring)
solver.parameters.random_seed = 0
status = solver.solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    cols = [solver.value(q) for q in queens]
    print("QUEENS", cols)
    for row in range(BOARD_SIZE):
        print(" ".join("Q" if c == cols[row] else "." for c in range(BOARD_SIZE)))

    # Cấu trúc nghiệm cho phần vẽ hình (giao kèo SOLUTION của tools/runner.py).
    # `queens[i]` = cột của hậu ở hàng i — đủ để dựng lại cả bàn cờ.
    print("SOLUTION " + json.dumps({
        "problem": "nqueens",
        "n": BOARD_SIZE,
        "queens": cols,
    }))

print("RESULT " + json.dumps({
    "status": solver.status_name(status),
    "solve_time_s": round(solver.wall_time, 4),
    "branches": solver.num_branches,
    # CP-SAT không có khái niệm "fails"; conflicts là đại lượng gần nhất.
    "fails": solver.num_conflicts,
    "n": BOARD_SIZE,
}))
