"""Bài 3.2 — Thời khoá biểu có ràng buộc khả dụng | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: ✍️ VIẾT MỚI. IBM không phát hành bản CP nào của bài xếp thời khoá biểu qua
`docplex.cp` (chỉ có `timetabling.mod` bằng OPL). Bản này dựng lại đúng mô hình đó
bằng Python, cộng ba nhóm ràng buộc khả dụng RB7/RB8/RB4.

Đọc ĐÚNG những file `.dat` gốc mà hai chiều kia dùng, qua `tools/opl_dat.py`.

Chạy:
    python3 models/3.2_timetable/docplexcp/timetable_cp.py \\
        data/timetable/base.dat data/timetable/large.dat data/timetable/availability.dat

VAI TRÒ CỦA CHIỀU NÀY TRONG BÁO CÁO
------------------------------------
Đây là điểm đo thứ ba, và là điểm đo duy nhất tách bạch được hai nguyên nhân:

    OPL (CP Optimizer + đếm có điều kiện)
      ──vs── bản này (CP Optimizer + interval)      → cô lập ảnh hưởng của MÃ HOÁ
      ──vs── OR-Tools (CP-SAT + interval)           → cô lập ảnh hưởng của ENGINE

So thẳng OPL với OR-Tools thì hai yếu tố đổi cùng lúc nên không kết luận được gì.

HAI PRIMITIVE CỦA CP OPTIMIZER MÀ CP-SAT KHÔNG CÓ
--------------------------------------------------
1. `alternative(master, [alt1, alt2, ...])` — chọn đúng một tài nguyên trong nhiều
   lựa chọn, tự đồng bộ thời gian với interval chính. Bản CP-SAT phải làm tay:
   tạo literal hiện diện cho từng cặp (khoá học, tài nguyên) rồi tự buộc chúng
   khớp với biến chọn tài nguyên.

2. `forbid_extent(interval, F)` + hàm bậc thang — cấm một interval phủ lên vùng mà
   F bằng 0. Đây là cách diễn đạt LỊCH BẬN đúng nghĩa: khai báo trực tiếp lịch của
   tài nguyên, không cần biến phụ nào. Bản CP-SAT phải bung thành phép tuyển
   "bắt đầu sau t HOẶC kết thúc trước t" kèm một biến bool cho mỗi cặp
   (khoá học, thời điểm bận).

Ba nhóm ràng buộc khả dụng ở đây vì thế **không sinh thêm một biến quyết định nào**
— chúng chỉ là dữ liệu lịch gắn vào interval. Đây là thế mạnh 20 năm chuyên biệt
của CP Optimizer cho bài lập lịch mà brief §1 đã nêu.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401,E402  — trỏ docplex.cp sang cpoptimizer cục bộ
from opl_dat import load  # noqa: E402

from docplex.cp.function import CpoStepFunction  # noqa: E402
from docplex.cp.model import CpoModel  # noqa: E402

Instance = collections.namedtuple(
    "Instance", "cls discipline duration repetition id requirement_id"
)


def _blocking_function(busy_times, horizon: int) -> CpoStepFunction:
    """Hàm bậc thang: 1 ở mọi thời điểm rảnh, 0 tại các thời điểm bận.

    Dùng với forbid_extent để cấm interval phủ lên vùng bằng 0.
    """
    fn = CpoStepFunction()
    fn.set_value(0, horizon, 1)
    for t in busy_times:
        fn.set_value(t, t + 1, 0)
    return fn


def build_and_solve(dat_files: list[str], time_limit: float = 300.0,
                    workers: int = 8, seed: int = 0) -> dict:
    d = load(*dat_files)

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

    can_teach: dict[str, list[int]] = {s: [] for s in disciplines}
    for t, s in teacher_discipline:
        can_teach[s].append(teacher_id[t])

    dedicated_rooms = {x for x, _ in dedicated}
    disciplines_needing_room = {s for _, s in dedicated}
    can_use_room = {
        s: [
            room_id[x]
            for x in rooms
            if (x, s) in dedicated
            or (x not in dedicated_rooms and s not in disciplines_needing_room)
        ]
        for s in disciplines
    }

    instances: list[Instance] = []
    for req_idx, (cls, disc, dur, rep) in enumerate(requirements):
        for i in range(1, rep + 1):
            instances.append(Instance(cls, disc, dur, rep, i, req_idx))
    n = len(instances)

    mdl = CpoModel()

    # ---- interval chính cho mỗi khoá học ------------------------------------
    # end cũng bị chặn ở max_time-1, đúng như bản OPL gốc khai End thuộc Time.
    x = [
        mdl.interval_var(
            size=inst.duration,
            start=(0, max_time - 1),
            end=(0, max_time - 1),
            name=f"x{i}_{inst.cls}_{inst.discipline}",
        )
        for i, inst in enumerate(instances)
    ]

    # ---- chọn giáo viên và phòng bằng alternative ---------------------------
    # alternative(master, alts) = đúng một alt hiện diện và đồng bộ thời gian với
    # master. Bản CP-SAT phải dựng tay bằng literal hiện diện.
    xt: list[dict[int, object]] = []
    xr: list[dict[int, object]] = []
    for i, inst in enumerate(instances):
        alts_t = {
            tid: mdl.interval_var(
                size=inst.duration, start=(0, max_time - 1), end=(0, max_time - 1),
                optional=True, name=f"xt{i}_{tid}",
            )
            for tid in can_teach[inst.discipline]
        }
        mdl.add(mdl.alternative(x[i], list(alts_t.values())))
        xt.append(alts_t)

        alts_r = {
            rid: mdl.interval_var(
                size=inst.duration, start=(0, max_time - 1), end=(0, max_time - 1),
                optional=True, name=f"xr{i}_{rid}",
            )
            for rid in can_use_room[inst.discipline]
        }
        mdl.add(mdl.alternative(x[i], list(alts_r.values())))
        xr.append(alts_r)

    # ---- tài nguyên dùng một lần tại mỗi thời điểm --------------------------
    for tid in range(len(teachers)):
        ivs = [xt[i][tid] for i in range(n) if tid in xt[i]]
        if ivs:
            mdl.add(mdl.no_overlap(ivs))
    for rid in range(len(rooms)):
        ivs = [xr[i][rid] for i in range(n) if rid in xr[i]]
        if ivs:
            mdl.add(mdl.no_overlap(ivs))

    by_class: dict[str, list[int]] = collections.defaultdict(list)
    for i, inst in enumerate(instances):
        by_class[inst.cls].append(i)
    for idxs in by_class.values():
        mdl.add(mdl.no_overlap([x[i] for i in idxs]))

    # ---- một lớp học một môn thì luôn cùng một giáo viên --------------------
    by_class_discipline: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
    for i, inst in enumerate(instances):
        by_class_discipline[(inst.cls, inst.discipline)].append(i)
    for (_, disc), idxs in by_class_discipline.items():
        head = idxs[0]
        for i in idxs[1:]:
            for tid in can_teach[disc]:
                mdl.add(mdl.presence_of(xt[i][tid]) == mdl.presence_of(xt[head][tid]))

    # ---- thứ tự thời gian giữa các buổi của cùng một requirement ------------
    for i in range(n):
        for j in range(n):
            if (
                instances[i].requirement_id == instances[j].requirement_id
                and instances[i].id < instances[j].id
            ):
                mdl.add(mdl.start_of(x[i]) < mdl.start_of(x[j]))

    # ---- ràng buộc lịch, diễn đạt bằng hàm bậc thang ------------------------
    # môn buổi sáng: chỉ được BẮT ĐẦU trong buổi sáng
    morning_fn = CpoStepFunction()
    morning_fn.set_value(0, max_time, 0)
    for day in range(nb_days):
        morning_fn.set_value(day * day_duration, day * day_duration + half_day, 1)

    # khoá dài hơn 1 tiết phải nằm gọn trong một buổi
    same_halfday_fn: dict[int, CpoStepFunction] = {}
    for dur in {inst.duration for inst in instances if inst.duration > 1}:
        fn = CpoStepFunction()
        fn.set_value(0, max_time, 0)
        for s in range(max_time):
            if (s % half_day) + dur <= half_day:
                fn.set_value(s, s + 1, 1)
        same_halfday_fn[dur] = fn

    for i, inst in enumerate(instances):
        if inst.discipline in morning:
            mdl.add(mdl.forbid_start(x[i], morning_fn))
        if inst.duration > 1:
            mdl.add(mdl.forbid_start(x[i], same_halfday_fn[inst.duration]))

    # ---- không dạy trùng môn hai lần trong một ngày, với cùng một lớp -------
    for i in range(n):
        for j in range(i + 1, n):
            if (
                instances[i].discipline == instances[j].discipline
                and instances[i].cls == instances[j].cls
            ):
                mdl.add(
                    mdl.int_div(mdl.start_of(x[i]), day_duration)
                    != mdl.int_div(mdl.start_of(x[j]), day_duration)
                )

    # ---- giờ nghỉ giữa hai môn kỵ nhau --------------------------------------
    for i in range(n):
        for j in range(i + 1, n):
            a, b = instances[i].discipline, instances[j].discipline
            if instances[i].cls != instances[j].cls:
                continue
            if (a, b) not in need_break and (b, a) not in need_break:
                continue
            si, ei = mdl.start_of(x[i]), mdl.end_of(x[i])
            sj, ej = mdl.start_of(x[j]), mdl.end_of(x[j])
            gap = mdl.max([0, si - ej]) + mdl.max([0, sj - ei])
            mdl.add(
                (mdl.int_div(si, day_duration) != mdl.int_div(sj, day_duration))
                | (mdl.int_div(si, half_day) != mdl.int_div(sj, half_day))
                | (gap >= break_duration)
            )

    # ---- RB7 / RB8 / RB4 — ràng buộc khả dụng ------------------------------
    # Khai báo trực tiếp lịch bận của tài nguyên rồi cấm interval phủ lên đó.
    # Không sinh thêm biến quyết định nào — khác hẳn bản CP-SAT.
    teacher_busy: dict[str, list[int]] = collections.defaultdict(list)
    for who, t in d.get("TeacherBusySet", []):
        teacher_busy[who].append(t)
    for who, times in teacher_busy.items():
        tid = teacher_id.get(who)
        if tid is None:
            continue
        fn = _blocking_function(times, max_time)
        for i in range(n):
            if tid in xt[i]:
                mdl.add(mdl.forbid_extent(xt[i][tid], fn))

    class_busy: dict[str, list[int]] = collections.defaultdict(list)
    for who, t in d.get("ClassBusySet", []):
        class_busy[who].append(t)
    for who, times in class_busy.items():
        fn = _blocking_function(times, max_time)
        for i, inst in enumerate(instances):
            if inst.cls == who:
                mdl.add(mdl.forbid_extent(x[i], fn))

    discipline_avoid: dict[str, list[int]] = collections.defaultdict(list)
    for who, t in d.get("DisciplineAvoidSet", []):
        discipline_avoid[who].append(t)
    for who, times in discipline_avoid.items():
        fn = _blocking_function(times, max_time)
        for i, inst in enumerate(instances):
            if inst.discipline == who:
                mdl.add(mdl.forbid_extent(x[i], fn))

    # ---- mục tiêu -----------------------------------------------------------
    load_per_class = collections.Counter()
    for inst in instances:
        load_per_class[inst.cls] += inst.duration
    makespan = mdl.integer_var(0, max_time - 1, "makespan")
    mdl.add(makespan == mdl.max([mdl.end_of(x[i]) for i in range(n)]))
    mdl.add(makespan >= max(load_per_class.values()))
    mdl.add(mdl.minimize(makespan))

    t0 = time.perf_counter()
    sol = mdl.solve(TimeLimit=time_limit, Workers=workers, RandomSeed=seed,
                    LogVerbosity="Quiet")
    wall = time.perf_counter() - t0

    infos = sol.get_solver_infos() if sol else {}
    result = {
        "status": str(sol.get_solve_status()) if sol else "NoSolution",
        "objective": sol.get_objective_value() if sol else None,
        "solve_time_s": round(sol.get_solve_time(), 4) if sol else None,
        "branches": infos.get("NumberOfBranches"),
        "fails": infos.get("NumberOfFails"),
        "nb_instances": n,
        "nb_teacher_busy": len(d.get("TeacherBusySet", [])),
        "nb_class_busy": len(d.get("ClassBusySet", [])),
        "nb_discipline_avoid": len(d.get("DisciplineAvoidSet", [])),
        "wall_s": round(wall, 4),
    }

    if sol:
        print(f"Makespan = {result['objective']}  ({n} khoá học)")
        for c in classes:
            print(f"\n=== Lớp {c} ===")
            for s_val, i in sorted((sol.get_var_solution(x[i]).get_start(), i)
                                   for i in by_class[c]):
                inst = instances[i]
                who = next(teachers[t] for t in xt[i]
                           if sol.get_var_solution(xt[i][t]).is_present())
                where = next(rooms[r] for r in xr[i]
                             if sol.get_var_solution(xr[i][r]).is_present())
                print(
                    f"  ngày {s_val // day_duration + 1} tiết {s_val % day_duration + 1}"
                    f"  {inst.discipline:<10} {who:<14} phòng {where}"
                )
    return result


if __name__ == "__main__":
    files = [a for a in sys.argv[1:] if a.endswith(".dat")]
    if not files:
        files = ["data/timetable/base.dat", "data/timetable/large.dat",
                 "data/timetable/availability.dat"]
    print("RESULT " + json.dumps(build_and_solve(files)))
