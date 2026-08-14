#!/usr/bin/env python3
"""Kiểm tra cả ba chiều của báo cáo có gọi được engine hay không.

Chạy:  python3 tools/check_env.py   (hoặc: make check)

In ra trạng thái từng chiều để biết ngay thiếu gì trước khi chạy notebook.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OK, BAD = "  OK  ", " THIẾU"


def check_ortools() -> tuple[bool, str]:
    try:
        from ortools.sat.python import cp_model
    except ImportError as e:
        return False, f"chưa cài ortools ({e})"
    m = cp_model.CpModel()
    x = m.new_int_var(0, 3, "x")
    m.add(x == 2)
    s = cp_model.CpSolver()
    if s.solve(m) != cp_model.OPTIMAL:
        return False, "solve thử thất bại"
    import ortools

    return True, f"ortools {ortools.__version__} — engine CP-SAT"


def check_docplexcp() -> tuple[bool, str]:
    try:
        import docplex
    except ImportError as e:
        return False, f"chưa cài docplex ({e})"
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import cpo_env
    except RuntimeError as e:
        return False, str(e).replace("\n", "\n         ")
    from docplex.cp.model import CpoModel

    m = CpoModel()
    x = m.integer_var(0, 3, "x")
    m.add(x == 2)
    try:
        sol = m.solve(LogVerbosity="Quiet", TimeLimit=10)
    except Exception as e:  # noqa: BLE001 — muốn báo mọi lỗi engine ra cho người dùng
        return False, f"gọi engine thất bại: {e}"
    if not sol:
        return False, "solve thử không ra nghiệm"
    return True, f"docplex {docplex.__version__} — engine CP Optimizer\n         {cpo_env.EXECFILE}"


def check_opl() -> tuple[bool, str]:
    script = ROOT / "tools" / "oplrun.sh"
    if not script.exists():
        return False, "thiếu tools/oplrun.sh"

    # oplrun.sh --which chỉ dò tìm rồi in đường dẫn, không giải gì cả. In ra để
    # người dùng trên hệ điều hành khác biết script đang gọi đúng file nào.
    try:
        w = subprocess.run(
            [str(script), "--which"], capture_output=True, text=True, timeout=60
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return False, f"không chạy được tools/oplrun.sh: {e}"
    if w.returncode != 0:
        return False, w.stderr.strip().replace("\n", "\n         ")
    oplrun_path = w.stdout.strip()

    probe = ROOT / "results" / "_probe.mod"
    probe.parent.mkdir(exist_ok=True)
    probe.write_text(
        "using CP;\n"
        "dvar int x in 0..3;\n"
        "subject to { x == 2; }\n"
        'execute { writeln("PROBE_OK ", x); }\n',
        encoding="utf-8",
    )
    try:
        p = subprocess.run(
            [str(script), str(probe)], capture_output=True, text=True, timeout=120
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return False, f"không chạy được oplrun: {e}"
    finally:
        probe.unlink(missing_ok=True)
    if "PROBE_OK" not in p.stdout:
        tail = (p.stdout + p.stderr).strip().splitlines()[-4:]
        return False, "oplrun không giải được model thử:\n         " + "\n         ".join(tail)
    return True, f"oplrun — engine CP Optimizer\n         {oplrun_path}"


def main() -> int:
    checks = [
        ("OPL", check_opl),
        ("DOcplex.cp", check_docplexcp),
        ("OR-Tools", check_ortools),
    ]
    all_ok = True
    print("Kiểm tra ba chiều của báo cáo:\n")
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:  # noqa: BLE001
            ok, msg = False, f"lỗi không lường trước: {e}"
        all_ok &= ok
        print(f"[{OK if ok else BAD}] {name:<12} {msg}")
    print()
    if not all_ok:
        print("Có chiều chưa sẵn sàng — xem README.md phần Cài đặt.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
