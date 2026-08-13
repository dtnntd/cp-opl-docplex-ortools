"""Bài 2.2 — Employee / Shift Scheduling có nguyện vọng | Chiều OR-Tools (engine CP-SAT)

Nguồn: ✅ LẤY MẪU CHÍNH THỨC.
  Google OR-Tools — "Employee scheduling / Scheduling with shift requests"
  https://developers.google.com/optimization/scheduling/employee_scheduling
  (bản `schedule_requests_sat.py`, Apache License 2.0)

Phần DỰNG MÔ HÌNH giữ nguyên như bản gốc của Google — cùng biến, cùng tên hàm
API, cùng thứ tự ràng buộc, cùng hàm mục tiêu. Chỉ bổ sung ba thứ:

  1. `shift_requests` đọc từ `data/employee/employee.dat` thay vì viết cứng
     trong code, để cả BA chiều dùng chung đúng một bộ dữ liệu. Bảng .dat là
     bản chép nguyên vẹn của mảng lồng trong ví dụ gốc (đã đối chiếu từng ô).
  2. Cố định `num_search_workers=1` và `random_seed` — CP-SAT chạy đa luồng thì
     `branches`/`conflicts` đổi giữa các lần chạy, số liệu sẽ không tái lập được
     (PLAN.md §2.4).
  3. Dòng `RESULT {json}` theo giao kèo của tools/runner.py.

Chạy:  python3 models/2.2_employee/ortools/employee_sat.py [data/employee/employee.dat]

GHI CHÚ ENGINE (điểm so sánh với DOcplex.cp, CÙNG ngôn ngữ Python)
------------------------------------------------------------------
CP-SAT có hai ràng buộc toàn cục viết thẳng được ý định của bài:

    model.add_exactly_one(...)     # mỗi ca đúng một người
    model.add_at_most_one(...)     # mỗi người tối đa một ca/ngày

Hai thứ này là ràng buộc BOOLEAN nguyên gốc: CP-SAT nạp chúng thành mệnh đề
SAT và lan truyền bằng bộ máy CDCL của chính nó. CP Optimizer không có API
tương đương ở tầng boolean — bản docplex.cp phải viết thành tổng số học
`sum(...) == 1` / `sum(...) <= 1`, tức là ràng buộc SỐ HỌC trên biến 0/1.
Đây đúng là loại bài mà brief §1 nói CP-SAT có sở trường.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from opl_dat import load  # noqa: E402

from ortools.sat.python import cp_model  # noqa: E402


def read_instance(dat_file: str):
    """Đọc bộ dữ liệu dùng chung và dựng lại đúng mảng shift_requests của Google.

    File .dat lưu nguyện vọng ở dạng THƯA (danh sách bộ ba được yêu cầu, 20 phần
    tử). Hàm này bung ra dạng DÀY shift_requests[n][d][s] gồm 105 số 0/1 — đúng
    cấu trúc mà đoạn code gốc của Google mong đợi, nên phần dựng mô hình bên dưới
    không phải sửa một dòng nào.
    """
    d = load(dat_file)
    employees, days, shifts = d["Employees"], d["Days"], d["Shifts"]
    requested = set(d["ShiftRequests"])
    shift_requests = [
        [
            [1 if (employees[n], days[dd], shifts[s]) in requested else 0
             for s in range(len(shifts))]
            for dd in range(len(days))
        ]
        for n in range(len(employees))
    ]
    return employees, days, shifts, shift_requests


def build_and_solve(dat_file: str, workers: int = 1, seed: int = 0) -> dict:
    employees, day_names, shift_names, shift_requests = read_instance(dat_file)

    # ---- dựng mô hình: nguyên văn ví dụ chính thức của Google ---------------
    num_nurses = len(employees)
    num_shifts = len(shift_names)
    num_days = len(day_names)
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.new_bool_var(f"shift_n{n}_d{d}_s{s}")

    # Each shift is assigned to exactly one nurse in .
    for d in all_days:
        for s in all_shifts:
            model.add_exactly_one(shifts[(n, d, s)] for n in all_nurses)

    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.add_at_most_one(shifts[(n, d, s)] for s in all_shifts)

    # Try to distribute the shifts evenly, so that each nurse works
    # min_shifts_per_nurse shifts. If this is not possible, because the total
    # number of shifts is not divisible by the number of nurses, some nurses will
    # be assigned one more shift.
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    if num_shifts * num_days % num_nurses == 0:
        max_shifts_per_nurse = min_shifts_per_nurse
    else:
        max_shifts_per_nurse = min_shifts_per_nurse + 1
    for n in all_nurses:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        model.add(min_shifts_per_nurse <= num_shifts_worked)
        model.add(num_shifts_worked <= max_shifts_per_nurse)

    model.maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_nurses
            for d in all_days
            for s in all_shifts
        )
    )

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    # --- hết phần nguyên văn; dưới đây là cấu hình để tái lập số liệu --------
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = seed
    status = solver.solve(model)

    ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    if ok:
        print(
            f"So nguyen vong duoc dap ung = {int(solver.objective_value)}"
            f" / {sum(map(sum, (map(sum, r) for r in shift_requests)))}"
        )
        for d in all_days:
            print(f"Ngay {day_names[d]}")
            for s in all_shifts:
                for n in all_nurses:
                    if solver.value(shifts[(n, d, s)]) == 1:
                        tag = ("(dung nguyen vong)" if shift_requests[n][d][s]
                               else "(khong xin)")
                        print(f"  ca {shift_names[s]:<8} {employees[n]}\t{tag}")
        print(f"Tai cua tung nhan vien (gioi han {min_shifts_per_nurse}"
              f"..{max_shifts_per_nurse}):")
        for n in all_nurses:
            load_n = sum(solver.value(shifts[(n, d, s)])
                         for d in all_days for s in all_shifts)
            print(f"  {employees[n]}\t{load_n} ca")

    return {
        "status": solver.status_name(status),
        "objective": int(solver.objective_value) if ok else None,
        "solve_time_s": round(solver.wall_time, 4),
        "branches": solver.num_branches,
        # CP-SAT đếm CONFLICT, CP Optimizer đếm FAIL — hai đại lượng khác nhau,
        # chỉ so trong cùng một engine (README).
        "fails": solver.num_conflicts,
        "nb_employees": num_nurses,
        "nb_days": num_days,
        "nb_shifts": num_shifts,
        "nb_requests": sum(map(sum, (map(sum, r) for r in shift_requests))),
        "min_load": min_shifts_per_nurse,
        "max_load": max_shifts_per_nurse,
        "nb_bool_vars": num_nurses * num_days * num_shifts,
    }


if __name__ == "__main__":
    dat = sys.argv[1] if len(sys.argv) > 1 else "data/employee/employee.dat"
    print("RESULT " + json.dumps(build_and_solve(dat)))
