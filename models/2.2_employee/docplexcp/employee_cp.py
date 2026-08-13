"""Bài 2.2 — Employee / Shift Scheduling có nguyện vọng | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: ✍️ VIẾT MỚI.

IBM KHÔNG phát hành bản CP nào của bài xếp ca nhân sự. Trong kho ví dụ chính thức
`IBMDecisionOptimization/docplex`, mọi file mang tên `nurses*` đều nằm dưới
`examples/mp/` và `docs/mp/` — nhánh **Math Programming** (`docplex.mp`, engine
CPLEX). Thư mục `examples/cp/` (107 file) không có lấy một file nào về xếp ca.
Xem NOTES.md mục (c) để có bằng chứng đầy đủ. File này vì thế viết mới hoàn toàn.

Đọc ĐÚNG file dữ liệu mà hai chiều kia dùng — `data/employee/employee.dat` — qua
`tools/opl_dat.py`, nên ba chiều không có bản dữ liệu riêng nào để lệch nhau.

Chạy:  python3 models/2.2_employee/docplexcp/employee_cp.py [data/employee/employee.dat]

VAI TRÒ CỦA CHIỀU NÀY TRONG BÁO CÁO
------------------------------------
Đây là điểm đo bản lề, tách bạch được hai nguyên nhân gây khác biệt:

    OPL         (CP Optimizer + ngôn ngữ OPL)
      ──vs── bản này (CP Optimizer + Python/docplex.cp)  → cô lập NGÔN NGỮ
      ──vs── OR-Tools (CP-SAT     + Python/ortools.sat)  → cô lập ENGINE

CHỖ CP-SAT CÓ MÀ CP OPTIMIZER KHÔNG CÓ
---------------------------------------
Bài này là bài BOOLEAN thuần: 105 biến 0/1, ba nhóm ràng buộc đếm. CP-SAT có sẵn
hai ràng buộc boolean toàn cục khớp đúng ý định:

    model.add_exactly_one(...)      # ortools
    model.add_at_most_one(...)

`docplex.cp` KHÔNG có tương đương ở tầng boolean — danh mục ràng buộc toàn cục
của CP Optimizer (all_diff, count, pack, sequence, no_overlap, alternative...)
hướng tới biến MIỀN RỜI RẠC và biến INTERVAL, không tới mệnh đề SAT. Nên ở đây
phải viết thành tổng SỐ HỌC trên biến 0/1:

    mdl.add(mdl.sum(x[e, d, s] for e in employees) == 1)

Đây là mặt trái của cùng một đồng xu đã thấy ở bài 3.2: ở đó CP Optimizer có
`alternative` và `forbid_extent` mà CP-SAT phải dựng tay; ở đây thì ngược lại.
Mỗi engine mạnh ở đúng lớp bài mà cấu trúc dữ liệu lõi của nó phục vụ.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401,E402  — trỏ docplex.cp sang cpoptimizer cục bộ
from opl_dat import load  # noqa: E402

from docplex.cp.model import CpoModel  # noqa: E402


def build_and_solve(dat_file: str, time_limit: float = 300.0,
                    workers: int = 1, seed: int = 0) -> dict:
    # ---- dữ liệu, đọc từ đúng file .dat dùng chung --------------------------
    d = load(dat_file)
    employees: list[str] = d["Employees"]
    days: list[str] = d["Days"]
    shifts: list[str] = d["Shifts"]
    requested = set(d["ShiftRequests"])          # tập bộ ba <e, d, s> được xin

    n_emp, n_days, n_shifts = len(employees), len(days), len(shifts)

    # Tổng số suất phải phủ trong kỳ, và khoảng cân bằng tải floor/ceil.
    total_slots = n_days * n_shifts
    min_load = total_slots // n_emp
    max_load = min_load if total_slots % n_emp == 0 else min_load + 1

    mdl = CpoModel(name="employee_shift_scheduling")

    # ---- biến quyết định ----------------------------------------------------
    # x[e, d, s] = 1 <=> nhân viên e làm ca s trong ngày d.
    # OPL viết được `dvar boolean x[Employees][Days][Shifts]` — mảng đánh chỉ số
    # thẳng bằng phần tử của {string}. Python không có kiểu đó, phải dựng dict.
    x = {
        (e, dd, s): mdl.binary_var(name=f"x_{e}_{dd}_{s}")
        for e in employees
        for dd in days
        for s in shifts
    }

    # ---- (C1) mỗi ca của mỗi ngày do ĐÚNG một người đảm nhiệm ---------------
    # Không có add_exactly_one như CP-SAT; diễn đạt bằng tổng số học.
    for dd in days:
        for s in shifts:
            mdl.add(mdl.sum(x[e, dd, s] for e in employees) == 1)

    # ---- (C2) mỗi người làm TỐI ĐA một ca mỗi ngày --------------------------
    for e in employees:
        for dd in days:
            mdl.add(mdl.sum(x[e, dd, s] for s in shifts) <= 1)

    # ---- (C3)-(C4) cân bằng tải --------------------------------------------
    for e in employees:
        load_e = mdl.sum(x[e, dd, s] for dd in days for s in shifts)
        mdl.add(load_e >= min_load)
        mdl.add(load_e <= max_load)

    # ---- mục tiêu: tối đa số nguyện vọng được đáp ứng -----------------------
    # Tổng chạy trên TẬP NGUYỆN VỌNG THƯA (20 hạng tử) thay vì trên toàn lưới
    # 105 ô nhân hệ số 0/1 — cùng một biểu thức toán, ít hạng tử hơn.
    mdl.add(mdl.maximize(mdl.sum(x[key] for key in requested)))

    sol = mdl.solve(TimeLimit=time_limit, Workers=workers, RandomSeed=seed,
                    LogVerbosity="Quiet")

    infos = sol.get_solver_infos() if sol else {}
    result = {
        "status": str(sol.get_solve_status()) if sol else "NoSolution",
        "objective": int(sol.get_objective_value()) if sol else None,
        "solve_time_s": round(sol.get_solve_time(), 4) if sol else None,
        "branches": infos.get("NumberOfBranches"),
        "fails": infos.get("NumberOfFails"),
        "nb_employees": n_emp,
        "nb_days": n_days,
        "nb_shifts": n_shifts,
        "nb_requests": len(requested),
        "min_load": min_load,
        "max_load": max_load,
        "nb_bool_vars": n_emp * n_days * n_shifts,
    }

    if sol:
        print(f"So nguyen vong duoc dap ung = {result['objective']} / {len(requested)}")
        for dd in days:
            print(f"Ngay {dd}")
            for s in shifts:
                for e in employees:
                    if sol[x[e, dd, s]] == 1:
                        tag = ("(dung nguyen vong)" if (e, dd, s) in requested
                               else "(khong xin)")
                        print(f"  ca {s:<8} {e}\t{tag}")
        print(f"Tai cua tung nhan vien (gioi han {min_load}..{max_load}):")
        for e in employees:
            load_e = sum(sol[x[e, dd, s]] for dd in days for s in shifts)
            print(f"  {e}\t{load_e} ca")

    return result


if __name__ == "__main__":
    dat = sys.argv[1] if len(sys.argv) > 1 else "data/employee/employee.dat"
    print("RESULT " + json.dumps(build_and_solve(dat)))
