"""Bài 3.2 — Thời khoá biểu có ràng buộc khả dụng | Chiều OR-Tools (engine CP-SAT)

Nguồn: ✍️ VIẾT MỚI. Port đầy đủ mô hình `timetabling.mod` của IBM (CPLEX Studio
22.2) sang CP-SAT, cộng ba nhóm ràng buộc khả dụng RB7/RB8/RB4 mà bản gốc không có.

Đọc ĐÚNG những file `.dat` gốc mà chiều OPL dùng, qua `tools/opl_dat.py` — ba
chiều không có bản dữ liệu riêng nào để lệch nhau.

Chạy:
    python3 models/3.2_timetable/ortools/timetable_sat.py \\
        data/timetable/base.dat data/timetable/large.dat data/timetable/availability.dat

    # bỏ availability để đo chi phí của nó:
    python3 models/3.2_timetable/ortools/timetable_sat.py \\
        data/timetable/base.dat data/timetable/large.dat

KHÁC BIỆT MÃ HOÁ SO VỚI BẢN OPL (điểm so sánh cốt lõi của bài này)
------------------------------------------------------------------
Bản OPL gốc diễn đạt "tài nguyên chỉ dùng một lần tại mỗi thời điểm" bằng TỔNG CÓ
ĐIỀU KIỆN — với mỗi khoá học r nó đếm xem có bao nhiêu khoá khác bắt đầu trong
khoảng [Start[r], End[r]) rồi bắt tổng đó < 2:

    (sum(o in InstanceSet : o.Class == x)
       (1 == (Start[o] >= Start[r])*(Start[o] < End[r]))) < 2;

Bản này dùng BIẾN INTERVAL + no-overlap, thứ cả CP Optimizer lẫn CP-SAT đều có
sẵn thuật toán lan truyền chuyên dụng:

    model.add_no_overlap([...các interval của cùng một lớp...])

Hai cách tương đương về nghiệm (hai đoạn giao nhau thì điểm bắt đầu muộn hơn luôn
nằm trong khoảng của đoạn kia), nhưng khác hẳn về sức lan truyền. Với tài nguyên
được chọn bằng BIẾN (giáo viên, phòng), ở đây dùng interval TUỲ CHỌN gắn literal
hiện diện — đúng cách mà một solver lập lịch mong nhận được bài toán.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from opl_dat import load  # noqa: E402

from ortools.sat.python import cp_model  # noqa: E402

Instance = collections.namedtuple(
    "Instance", "cls discipline duration repetition id requirement_id"
)


def build_and_solve(dat_files: list[str], time_limit: float = 300.0, workers: int = 8,
                    seed: int = 0) -> dict:
    d = load(*dat_files)

    # ---- từ vựng, dựng đúng như phần đầu timetabling.mod ---------------------
    requirements = d["RequirementSet"]
    teacher_discipline = d["TeacherDisciplineSet"]
    rooms = d["Room"]
    dedicated = set(d["DedicatedRoomSet"])
    need_break = set(d.get("NeedBreak", []))
    morning = set(d.get("MorningDiscipline", []))
    break_duration = d["BreakDuration"]
    day_duration = d["DayDuration"]
    nb_days = d["NumberOfDaysPerPeriod"]

    classes = sorted({r[0] for r in requirements})
    teachers = sorted({t for t, _ in teacher_discipline})
    disciplines = sorted({s for _, s in teacher_discipline})

    half_day = day_duration // 2
    max_time = day_duration * nb_days

    teacher_id = {t: i for i, t in enumerate(teachers)}
    room_id = {r: i for i, r in enumerate(rooms)}

    # Giáo viên nào dạy được môn nào.
    can_teach: dict[str, list[int]] = {s: [] for s in disciplines}
    for t, s in teacher_discipline:
        can_teach[s].append(teacher_id[t])

    # Phòng nào dùng được cho môn nào — công thức PossibleRoom của bản gốc:
    # phòng x dùng được cho môn s nếu <x,s> là phòng chuyên dụng, HOẶC nếu x không
    # chuyên dụng cho môn nào và s cũng không đòi phòng chuyên dụng nào.
    dedicated_rooms = {x for x, _ in dedicated}
    disciplines_needing_room = {s for _, s in dedicated}
    can_use_room: dict[str, list[int]] = {}
    for s in disciplines:
        ok = [
            room_id[x]
            for x in rooms
            if (x, s) in dedicated
            or (x not in dedicated_rooms and s not in disciplines_needing_room)
        ]
        can_use_room[s] = ok

    # Mỗi requirement lặp `repetition` lần, mỗi lần là một instance.
    instances: list[Instance] = []
    for req_idx, (cls, disc, dur, rep) in enumerate(requirements):
        for i in range(1, rep + 1):
            instances.append(Instance(cls, disc, dur, rep, i, req_idx))
    n = len(instances)

    # ---- biến quyết định ----------------------------------------------------
    model = cp_model.CpModel()
    dom = cp_model.Domain(0, max_time - 1)

    start = [model.new_int_var(0, max_time - 1, f"start{i}") for i in range(n)]
    # Bản gốc khai End cũng thuộc Time nên khoá học phải kết thúc trước MaxTime-1.
    end = [model.new_int_var_from_domain(dom, f"end{i}") for i in range(n)]
    teacher = [
        model.new_int_var_from_domain(
            cp_model.Domain.from_values(can_teach[inst.discipline]), f"teacher{i}"
        )
        for i, inst in enumerate(instances)
    ]
    room = [
        model.new_int_var_from_domain(
            cp_model.Domain.from_values(can_use_room[inst.discipline]), f"room{i}"
        )
        for i, inst in enumerate(instances)
    ]
    makespan = model.new_int_var(0, max_time - 1, "makespan")

    # classTeacher[c,s]: một lớp học một môn thì luôn cùng một giáo viên.
    class_teacher = {}
    for c in classes:
        for s in disciplines:
            class_teacher[(c, s)] = model.new_int_var(
                0, len(teachers) - 1, f"classTeacher_{c}_{s}"
            )

    for i, inst in enumerate(instances):
        model.add(end[i] == start[i] + inst.duration)
        model.add(teacher[i] == class_teacher[(inst.cls, inst.discipline)])

    # ---- makespan -----------------------------------------------------------
    model.add_max_equality(makespan, end)
    load_per_class = collections.Counter()
    for inst in instances:
        load_per_class[inst.cls] += inst.duration
    model.add(makespan >= max(load_per_class.values()))   # chặn dưới, giúp chứng minh tối ưu

    # ---- thứ tự thời gian giữa các buổi của cùng một requirement -------------
    for i in range(n):
        for j in range(n):
            if (
                instances[i].requirement_id == instances[j].requirement_id
                and instances[i].id < instances[j].id
            ):
                model.add(start[i] < start[j])

    # ---- lớp học một môn tại một thời điểm: interval thường + no-overlap -----
    by_class: dict[str, list[int]] = collections.defaultdict(list)
    for i, inst in enumerate(instances):
        by_class[inst.cls].append(i)
    for c, idxs in by_class.items():
        model.add_no_overlap(
            [
                model.new_interval_var(start[i], instances[i].duration, end[i], f"iv_c{c}_{i}")
                for i in idxs
            ]
        )

    # ---- giáo viên và phòng: interval TUỲ CHỌN + no-overlap -----------------
    # Tài nguyên ở đây do BIẾN chọn, nên mỗi cặp (khoá học, tài nguyên) có một
    # interval chỉ "hiện diện" khi biến chọn đúng tài nguyên đó.
    teacher_lit: dict[tuple[int, int], object] = {}
    teacher_intervals: dict[int, list] = collections.defaultdict(list)
    for i, inst in enumerate(instances):
        for tid in can_teach[inst.discipline]:
            lit = model.new_bool_var(f"t_{i}_{tid}")
            model.add(teacher[i] == tid).only_enforce_if(lit)
            model.add(teacher[i] != tid).only_enforce_if(~lit)
            teacher_lit[(i, tid)] = lit
            teacher_intervals[tid].append(
                model.new_optional_interval_var(
                    start[i], inst.duration, end[i], lit, f"iv_t{tid}_{i}"
                )
            )
    for tid, ivs in teacher_intervals.items():
        model.add_no_overlap(ivs)

    room_intervals: dict[int, list] = collections.defaultdict(list)
    for i, inst in enumerate(instances):
        for rid in can_use_room[inst.discipline]:
            lit = model.new_bool_var(f"r_{i}_{rid}")
            model.add(room[i] == rid).only_enforce_if(lit)
            model.add(room[i] != rid).only_enforce_if(~lit)
            room_intervals[rid].append(
                model.new_optional_interval_var(
                    start[i], inst.duration, end[i], lit, f"iv_r{rid}_{i}"
                )
            )
    for rid, ivs in room_intervals.items():
        model.add_no_overlap(ivs)

    # ---- chỉ số ngày / buổi, cần cho các ràng buộc lịch ---------------------
    day = [model.new_int_var(0, nb_days - 1, f"day{i}") for i in range(n)]
    hd_start = [model.new_int_var(0, 2 * nb_days - 1, f"hds{i}") for i in range(n)]
    hd_end = [model.new_int_var(0, 2 * nb_days - 1, f"hde{i}") for i in range(n)]
    slot = [model.new_int_var(0, day_duration - 1, f"slot{i}") for i in range(n)]
    for i in range(n):
        model.add_division_equality(day[i], start[i], day_duration)
        model.add_division_equality(hd_start[i], start[i], half_day)
        model.add_modulo_equality(slot[i], start[i], day_duration)
        end_minus_1 = model.new_int_var(0, max_time - 1, f"em1_{i}")
        model.add(end_minus_1 == end[i] - 1)
        model.add_division_equality(hd_end[i], end_minus_1, half_day)

    # khoá học phải bắt đầu và kết thúc trong cùng một buổi
    for i, inst in enumerate(instances):
        if inst.duration > 1:
            model.add(hd_start[i] == hd_end[i])

    # môn buổi sáng phải nằm trong buổi sáng
    for i, inst in enumerate(instances):
        if inst.discipline in morning:
            model.add(slot[i] < half_day)

    # không dạy trùng môn hai lần trong một ngày, với cùng một lớp
    for i in range(n):
        for j in range(i + 1, n):
            if (
                instances[i].discipline == instances[j].discipline
                and instances[i].cls == instances[j].cls
            ):
                model.add(day[i] != day[j])

    # ---- giờ nghỉ giữa hai môn kỵ nhau --------------------------------------
    for i in range(n):
        for j in range(i + 1, n):
            a, b = instances[i].discipline, instances[j].discipline
            if instances[i].cls != instances[j].cls:
                continue
            if (a, b) not in need_break and (b, a) not in need_break:
                continue
            diff_day = model.new_bool_var(f"bd_{i}_{j}")
            model.add(day[i] != day[j]).only_enforce_if(diff_day)
            model.add(day[i] == day[j]).only_enforce_if(~diff_day)

            diff_hd = model.new_bool_var(f"bh_{i}_{j}")
            model.add(hd_start[i] != hd_start[j]).only_enforce_if(diff_hd)
            model.add(hd_start[i] == hd_start[j]).only_enforce_if(~diff_hd)

            # khoảng cách giữa hai khoá; hai khoá cùng lớp không chồng nhau nên
            # nhiều nhất một trong hai số hạng dương.
            g1 = model.new_int_var(0, max_time, f"g1_{i}_{j}")
            g2 = model.new_int_var(0, max_time, f"g2_{i}_{j}")
            model.add_max_equality(g1, [0, start[i] - end[j]])
            model.add_max_equality(g2, [0, start[j] - end[i]])
            far = model.new_bool_var(f"bg_{i}_{j}")
            model.add(g1 + g2 >= break_duration).only_enforce_if(far)
            model.add(g1 + g2 < break_duration).only_enforce_if(~far)

            model.add_bool_or([diff_day, diff_hd, far])

    # ---- RB7 / RB8 / RB4 — ràng buộc khả dụng (phần bài 3.2 thêm vào) -------
    # Khoá học i chiếm [start, end). Nó KHÔNG phủ thời điểm t khi start > t hoặc
    # end <= t. Biến `after` chọn một trong hai vế của phép tuyển đó.
    def forbid(i: int, t: int, tag: str, extra_lit=None) -> None:
        after = model.new_bool_var(f"av_{tag}_{i}_{t}")
        guard = [after] if extra_lit is None else [extra_lit, after]
        model.add(start[i] > t).only_enforce_if(guard)
        guard = [~after] if extra_lit is None else [extra_lit, ~after]
        model.add(end[i] <= t).only_enforce_if(guard)

    # RB7 — giáo viên bận. Giáo viên là BIẾN nên phải gắn thêm literal hiện diện.
    for who, t in d.get("TeacherBusySet", []):
        tid = teacher_id.get(who)
        if tid is None:
            continue
        for i, inst in enumerate(instances):
            if tid in can_teach[inst.discipline]:
                forbid(i, t, "t", teacher_lit[(i, tid)])

    # RB8 — lớp bận. Lớp là HẰNG của instance nên lọc thẳng, không cần literal.
    for who, t in d.get("ClassBusySet", []):
        for i, inst in enumerate(instances):
            if inst.cls == who:
                forbid(i, t, "c")

    # RB4 — khung giờ cần tránh của môn.
    for who, t in d.get("DisciplineAvoidSet", []):
        for i, inst in enumerate(instances):
            if inst.discipline == who:
                forbid(i, t, "d")

    # ---- giải ---------------------------------------------------------------
    model.minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    # Cố định để số liệu benchmark tái lập được — xem PLAN.md §2.4.
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.perf_counter()
    status = solver.solve(model)
    wall = time.perf_counter() - t0

    result = {
        "status": solver.status_name(status),
        "objective": solver.value(makespan) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
        "solve_time_s": round(solver.wall_time, 4),
        "branches": solver.num_branches,
        "fails": solver.num_conflicts,      # CP-SAT đếm conflicts, không phải fails
        "nb_instances": n,
        "nb_teacher_busy": len(d.get("TeacherBusySet", [])),
        "nb_class_busy": len(d.get("ClassBusySet", [])),
        "nb_discipline_avoid": len(d.get("DisciplineAvoidSet", [])),
        "wall_s": round(wall, 4),
    }

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"Makespan = {solver.value(makespan)}  ({n} khoá học)")
        for c in classes:
            print(f"\n=== Lớp {c} ===")
            rows = sorted(
                (solver.value(start[i]), i) for i in by_class[c]
            )
            for s_val, i in rows:
                inst = instances[i]
                print(
                    f"  ngày {s_val // day_duration + 1} tiết {s_val % day_duration + 1}"
                    f"  {inst.discipline:<10} {teachers[solver.value(teacher[i])]:<14}"
                    f" phòng {rooms[solver.value(room[i])]}"
                )
    return result


if __name__ == "__main__":
    files = [a for a in sys.argv[1:] if a.endswith(".dat")]
    if not files:
        files = ["data/timetable/base.dat", "data/timetable/large.dat",
                 "data/timetable/availability.dat"]
    print("RESULT " + json.dumps(build_and_solve(files)))
