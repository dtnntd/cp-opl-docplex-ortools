#!/usr/bin/env python3
"""Benchmark bài 3.2 — ba chiều × bốn cấu hình dữ liệu.

Đây là bài DUY NHẤT của báo cáo có đo hiệu năng định lượng. Ba chiều được xếp để
mỗi phép so chỉ đổi đúng MỘT biến số:

    opl        CP Optimizer  đếm có điều kiện  ┐
                                               ├─ so cặp này -> cô lập MÃ HOÁ
    docplexcp  CP Optimizer  interval          ┘┐
                                                ├─ so cặp này -> cô lập ENGINE
    ortools    CP-SAT        interval           ┘

Chạy:  python3 tools/bench_timetable.py [--reps 5] [--csv results/bench.csv]

Bốn cấu hình là tích Descartes {gốc, +availability} × {small, large} — bảng 2×2,
bỏ bớt một ô là hỏng phép so (PLAN.md §WP6).

Mỗi (cấu hình, chiều) chạy lặp ít nhất 5 lần và lấy TRUNG VỊ: CP-SAT chạy đa luồng
thì số liệu đổi giữa các lần chạy, nên 5 là SÀN chứ không phải mặc định hạ xuống
được (xem PLAN.md §2.4).
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from runner import ENGINE, ROOT, run  # noqa: E402

D = "data/timetable"

#: Cấu hình dữ liệu. Chiều OPL cần file availability rỗng thay vì bỏ trống tham số,
#: vì OPL bắt buộc mọi phần tử khai bằng `...` phải có giá trị.
#:
#: Hai bộ dữ liệu dùng HAI file availability khác nhau, và phải như vậy:
#: `availability.dat` viết cho bộ large (Time = 0..47, đủ 8 môn), đem chạy với bộ
#: small (Time = 0..23, ba môn) thì mọi mốc nằm ngoài tầm nên không cắt gì —
#: ô `small+avail` khi đó cho số trùng khít từng chữ số với ô `small`.
#: `availability_small.dat` là bản đúng tầm bộ small, giữ nguyên mật độ mốc/buổi
#: học của bản large để hai ô "+avail" là cùng một loại can thiệp.
CONFIGS = {
    "small":       {"data": f"{D}/small.dat", "avail": None},
    "small+avail": {"data": f"{D}/small.dat", "avail": f"{D}/availability_small.dat"},
    "large":       {"data": f"{D}/large.dat", "avail": None},
    "large+avail": {"data": f"{D}/large.dat", "avail": f"{D}/availability.dat"},
}

DIMENSIONS = {
    "opl": {
        "model": "models/3.2_timetable/opl/timetabling_avail.mod",
        "encoding": "đếm có điều kiện",
    },
    "docplexcp": {
        "model": "models/3.2_timetable/docplexcp/timetable_cp.py",
        "encoding": "interval",
    },
    "ortools": {
        "model": "models/3.2_timetable/ortools/timetable_sat.py",
        "encoding": "interval",
    },
}


def args_for(dimension: str, config: str) -> list[str]:
    cfg = CONFIGS[config]
    args = [f"{D}/base.dat", cfg["data"]]
    if dimension == "opl":
        # OPL luôn cần cả ba tập availability, rỗng hay không.
        args.append(cfg["avail"] or f"{D}/availability_none.dat")
    elif cfg["avail"]:
        args.append(cfg["avail"])
    return args


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", type=int, default=5,
                    help="số lần chạy mỗi ô (mặc định 5 — sàn theo PLAN.md §2.4)")
    ap.add_argument("--csv", default="results/bench.csv")
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()

    rows: list[dict] = []
    for config in CONFIGS:
        for dim, spec in DIMENSIONS.items():
            for rep in range(1, a.reps + 1):
                rec = run(dim, spec["model"], args_for(dim, config),
                          timeout=a.timeout, problem="3.2_timetable")
                rows.append({
                    "config": config,
                    "dimension": dim,
                    "engine": ENGINE[dim],
                    "encoding": spec["encoding"],
                    "rep": rep,
                    "ok": rec.ok,
                    "objective": rec.objective,
                    "solve_time_s": rec.solve_time_s,
                    "branches": rec.branches,
                    "fails": rec.fails,
                    "wall_s": round(rec.wall_s, 3),
                })
                flag = "OK " if rec.ok else "FAIL"
                print(f"[{flag}] {config:<12} {dim:<10} rep{rep}  "
                      f"obj={rec.objective} solve={rec.solve_time_s}s "
                      f"branches={rec.branches}")

    out = ROOT / a.csv
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nĐã ghi {len(rows)} dòng -> {out}")

    # ---- bảng trung vị ------------------------------------------------------
    def median_of(config: str, dim: str, field: str):
        vals = [r[field] for r in rows
                if r["config"] == config and r["dimension"] == dim and r[field] is not None]
        return statistics.median(vals) if vals else None

    print("\nTRUNG VỊ (n = %d lần chạy mỗi ô)\n" % a.reps)
    header = f"{'cấu hình':<13} {'chiều':<10} {'engine':<13} {'mã hoá':<18} {'obj':>5} {'solve(s)':>9} {'nhánh':>10} {'fails/confl':>12}"
    print(header)
    print("-" * len(header))
    for config in CONFIGS:
        for dim, spec in DIMENSIONS.items():
            obj = median_of(config, dim, "objective")
            t = median_of(config, dim, "solve_time_s")
            br = median_of(config, dim, "branches")
            fa = median_of(config, dim, "fails")
            print(f"{config:<13} {dim:<10} {ENGINE[dim]:<13} {spec['encoding']:<18} "
                  f"{obj if obj is not None else '—':>5} "
                  f"{t if t is not None else '—':>9} "
                  f"{int(br) if br is not None else '—':>10} "
                  f"{int(fa) if fa is not None else '—':>12}")
        print()

    # Kiểm chứng chéo: ba chiều phải cùng ra một nghiệm tối ưu.
    print("KIỂM CHỨNG CHÉO — ba chiều có cùng nghiệm tối ưu không:")
    all_agree = True
    for config in CONFIGS:
        objs = {dim: median_of(config, dim, "objective") for dim in DIMENSIONS}
        distinct = {v for v in objs.values() if v is not None}
        agree = len(distinct) == 1
        all_agree &= agree
        print(f"  {config:<13} {objs}  ->  {'KHỚP' if agree else 'LỆCH ***'}")
    return 0 if all_agree and all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
