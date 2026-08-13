"""Bài 2.1 — Job-shop scheduling | Chiều OR-Tools (engine CP-SAT)

Nguồn: VIẾT MỚI. Google có bài hướng dẫn job-shop
(https://developers.google.com/optimization/scheduling/job_shop) nhưng bản đó
nhúng cứng dữ liệu 3x3 trong mã nguồn. Ở đây mô hình được viết lại để đọc đúng
file dữ liệu dùng chung `data/jobshop/ft06.dat` của bài, giữ nguyên cách mã hoá
mà tài liệu Google khuyến nghị: new_interval_var + add_no_overlap.

Chạy:  python3 models/2.1_jobshop/ortools/jobshop_sat.py [data.dat] [--gantt FILE]
                                                        [--workers N] [--seed S]

GHI CHÚ ENGINE (điểm so sánh với DOcplex.cp — cùng Python, cùng cách mã hoá interval):
  Cả hai engine đều có BIẾN INTERVAL và ràng buộc KHÔNG CHỒNG LẤN nguyên bản, nên
  hai bản Python gần như ánh xạ một-một:

      docplex.cp                          ortools.sat
      -----------------------------       ------------------------------------
      interval_var(size=d)                new_interval_var(start, d, end, name)
      no_overlap(list)                    add_no_overlap(list)
      end_before_start(a, b)              add(start_b >= end_a)
      minimize(max(end_of(...)))          add_max_equality + minimize

  Hai khác biệt thật sự:

  1. CP-SAT KHÔNG có `end_before_start`. Nó cũng không cần: interval của CP-SAT
     phơi ra ba biến nguyên start/size/end nên precedence viết thẳng thành bất
     đẳng thức tuyến tính. CP Optimizer thì giấu interval sau một API chuyên biệt
     và bù lại bằng cả một họ ràng buộc thời gian (endBeforeStart, startAtEnd,
     endAtStart, ...) cùng khái niệm interval VẮNG MẶT (optional interval) —
     thứ CP-SAT chỉ có dạng rút gọn qua new_optional_interval_var.

  2. CP-SAT cần HORIZON hữu hạn cho mọi biến nguyên. Tổng thời gian gia công là
     chặn trên hiển nhiên. CP Optimizer không cần vì miền mặc định của interval
     đã là 0..INTERVAL_MAX.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import jobshop_data  # noqa: E402  — đọc data/jobshop/*.dat, dùng chung với chiều OPL

from ortools.sat.python import cp_model  # noqa: E402

# -----------------------------------------------------------------------------
# Tham số dòng lệnh
# -----------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[3]
argv = sys.argv[1:]


def _take(flag, default):
    if flag in argv:
        i = argv.index(flag)
        value = argv[i + 1]
        del argv[i : i + 2]
        return value
    return default


gantt_path = _take("--gantt", None)
WORKERS = int(_take("--workers", 1))
SEED = int(_take("--seed", 42))
DATA = argv[0] if argv else str(ROOT / "data" / "jobshop" / "ft06.dat")

NB_JOBS, NB_MACHINES, MACHINES, DURATION = jobshop_data.load(DATA)

# Chặn trên của makespan: xếp tuần tự mọi công đoạn thì chắc chắn xong.
HORIZON = sum(DURATION[j][o] for j in range(NB_JOBS) for o in range(NB_MACHINES))

# -----------------------------------------------------------------------------
# Dựng mô hình
# -----------------------------------------------------------------------------
model = cp_model.CpModel()

start = {}
end = {}
interval = {}
for j in range(NB_JOBS):
    for o in range(NB_MACHINES):
        d = DURATION[j][o]
        s = model.new_int_var(0, HORIZON - d, f"s_{j}_{o}")
        e = model.new_int_var(d, HORIZON, f"e_{j}_{o}")
        start[j, o] = s
        end[j, o] = e
        # Biến interval: gói (start, size, end) thành một đối tượng mà các ràng
        # buộc lập lịch của CP-SAT hiểu được. Kích thước cố định nên công đoạn
        # không thể bị ngắt quãng.
        interval[j, o] = model.new_interval_var(s, d, e, f"O{j}-{o}")

# (C2) Thứ tự công nghệ trong mỗi job: công đoạn o phải xong trước khi o+1 bắt đầu.
for j in range(NB_JOBS):
    for o in range(1, NB_MACHINES):
        model.add(start[j, o] >= end[j, o - 1])

# (C3) Mỗi máy chỉ chạy một công đoạn tại một thời điểm.
for m in range(NB_MACHINES):
    model.add_no_overlap(
        [interval[j, o] for j in range(NB_JOBS) for o in range(NB_MACHINES) if MACHINES[j][o] == m]
    )

# (C4)+(OBJ) makespan = thời điểm kết thúc công đoạn cuối cùng của các job.
makespan = model.new_int_var(0, HORIZON, "makespan")
model.add_max_equality(makespan, [end[j, NB_MACHINES - 1] for j in range(NB_JOBS)])
model.minimize(makespan)

# -----------------------------------------------------------------------------
# Giải
# -----------------------------------------------------------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
# CP-SAT chạy đa luồng nên số nhánh/xung đột đổi giữa các lần chạy. Cố định số
# worker và seed để con số in ra tái lập được (xem PLAN.md §2.4).
solver.parameters.num_workers = WORKERS
solver.parameters.random_seed = SEED
status = solver.solve(model)

obj = None
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    obj = solver.value(makespan)
    starts = [[solver.value(start[j, o]) for o in range(NB_MACHINES)] for j in range(NB_JOBS)]
    for j in range(NB_JOBS):
        print(" ".join(str(s) for s in starts[j]))
    if gantt_path:
        out = jobshop_data.write_gantt(
            gantt_path, NB_JOBS, NB_MACHINES, MACHINES, starts, DURATION,
            f"Job-shop {pathlib.Path(DATA).stem} — OR-Tools / CP-SAT (makespan {obj})",
        )
        print("GANTT", out)

print("RESULT " + json.dumps({
    "status": solver.status_name(status),
    "objective": obj,
    "solve_time_s": round(solver.wall_time, 4),
    "branches": solver.num_branches,
    # CP-SAT không có khái niệm "fails" của CP Optimizer; conflicts là đại lượng
    # gần nhất nhưng KHÔNG so trực tiếp được — xem NOTES.md mục (d).
    "fails": solver.num_conflicts,
    "nb_jobs": NB_JOBS,
    "nb_machines": NB_MACHINES,
    "nb_operations": NB_JOBS * NB_MACHINES,
    "workers": WORKERS,
    "seed": SEED,
    "data": pathlib.Path(DATA).name,
}))
