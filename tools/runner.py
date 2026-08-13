#!/usr/bin/env python3
"""Chạy một mô hình CP ở một trong ba chiều và thu số liệu về một bản ghi thống nhất.

Ba chiều của báo cáo:

    opl        oplrun.exe   -> engine CP Optimizer
    docplexcp  python3      -> engine CP Optimizer (qua cpoptimizer.exe)
    ortools    python3      -> engine CP-SAT

GIAO KÈO VỚI MODEL — mọi model, ở cả ba chiều, phải in ra stdout đúng một dòng:

    RESULT {"status": ..., "objective": ..., "solve_time_s": ..., ...}

Quét dòng này đáng tin hơn nhiều so với việc đọc log của solver, vì OPL và
DOcplex.cp in log CP Optimizer còn OR-Tools in log CP-SAT — ba định dạng khác
nhau. Nếu model không in RESULT, runner sẽ lùi về đọc log CP Optimizer (dùng
được cho cả chiều opl lẫn docplexcp vì chung engine).

Dùng như CLI:
    tools/runner.py opl       models/2.1_jobshop/opl/jobshop.mod data/jobshop/ft06.dat
    tools/runner.py ortools   models/2.1_jobshop/ortools/jobshop_sat.py
    tools/runner.py --suite   models/3.2_timetable      # chạy cả 3 chiều của một bài

Dùng như thư viện (trong notebook):
    from runner import run, run_suite
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
OPLRUN = ROOT / "tools" / "oplrun.sh"

#: Chiều -> engine thật đứng sau. Đây là bảng tra dùng cho phần so sánh trong báo cáo.
ENGINE = {
    "opl": "CP Optimizer",
    "docplexcp": "CP Optimizer",
    "ortools": "CP-SAT",
}

#: Ngôn ngữ mô hình hoá của từng chiều — trục còn lại của phép so sánh.
LANGUAGE = {
    "opl": "OPL",
    "docplexcp": "Python (docplex.cp)",
    "ortools": "Python (ortools.sat)",
}

_RESULT_RE = re.compile(r"^RESULT\s+(\{.*\})\s*$", re.MULTILINE)

#: Các giá trị `status` được tính là chạy thành công, so khớp không phân biệt hoa thường.
#:
#: Đây là DANH SÁCH TRẮNG, cố ý. Dùng danh sách đen thì mỗi trạng thái lỗi mới lại
#: lọt lưới: model tự kiểm tra nghiệm rồi báo "Invalid", hay CP-SAT trả
#: "MODEL_INVALID"/"UNKNOWN", đều sẽ bị tính nhầm là OK. Trạng thái lạ phải mặc
#: định là hỏng, không phải mặc định là ổn.
_SUCCESS_STATUS = frozenset(
    {"optimal", "feasible", "completed", "sat", "satisfiable", "solution"}
)


def _is_success(status: str | None) -> bool:
    return status is not None and status.strip().lower() in _SUCCESS_STATUS

# Log CP Optimizer — chỉ dùng khi model không in RESULT.
_CPO_PATTERNS = {
    "branches": re.compile(r"!\s*Number of branches\s*:\s*([\d,]+)"),
    "fails": re.compile(r"!\s*Number of fails\s*:\s*([\d,]+)"),
    "solve_time_s": re.compile(r"!\s*Time spent in solve\s*:\s*([\d.]+)s"),
    "objective": re.compile(r"^OBJECTIVE:\s*(-?[\d.]+)", re.MULTILINE),
}
#: Phát hiện chạm trần Community Edition (không gian tìm kiếm > 2^1000).
#:
#: CẨN THẬN: oplrun LUÔN in câu "Problem size limit exceeded." trong banner giấy
#: phép, kể cả khi model giải xong bình thường — bắt trần bằng chuỗi đó sẽ báo
#: nhầm mọi lần chạy OPL. Tín hiệu thật là ngoại lệ từ engine.
_LIMIT_TEXT_RE = re.compile(r"Problem size limit exceeded", re.IGNORECASE)
_ENGINE_FATAL_RE = re.compile(r"FATAL\[ENGINE_\d+\]|### ENGINE exception")


def _hit_community_limit(dimension: str, text: str) -> bool:
    if not _LIMIT_TEXT_RE.search(text):
        return False
    if dimension == "opl":
        # Chỉ tính là chạm trần khi engine thực sự ném ngoại lệ, không tính banner.
        return bool(_ENGINE_FATAL_RE.search(text))
    # docplex.cp không in banner giấy phép, nên xuất hiện chuỗi này là tín hiệu thật.
    return True


@dataclass
class RunRecord:
    """Một lần chạy của một model ở một chiều."""

    problem: str
    dimension: str
    engine: str
    language: str
    model_file: str
    ok: bool
    #: "official" = lấy mẫu chính thức (ô ✅ trong brief), "new" = viết mới (ô ✍️).
    source: str | None = None
    #: Biến thể bài toán. Vài bài có hai mẫu chính thức trùng tên nhưng khác bài
    #: (PLAN.md §2.7); chỉ được đối chiếu objective giữa các bản CÙNG variant.
    variant: str | None = None
    #: Nhãn hiển thị — mặc định là tên chiều, khác đi với bản port phụ trợ.
    label: str | None = None
    status: str | None = None
    objective: float | None = None
    solve_time_s: float | None = None
    branches: int | None = None
    fails: int | None = None
    wall_s: float = 0.0
    community_limit_hit: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    stdout_tail: str = ""

    def as_row(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("stdout_tail", None)
        d.pop("extra", None)
        return d


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


def _command(dimension: str, model: pathlib.Path, args: list[str]) -> list[str]:
    if dimension == "opl":
        # oplrun.sh tự dịch những tham số nào là đường dẫn có thật sang kiểu Windows.
        return [str(OPLRUN), str(model), *args]
    if dimension in ("docplexcp", "ortools"):
        return [sys.executable, str(model), *args]
    raise ValueError(f"Chiều không hợp lệ: {dimension!r} (chọn: {', '.join(ENGINE)})")


def run(
    dimension: str,
    model: str | pathlib.Path,
    args: list[str] | None = None,
    timeout: int = 600,
    problem: str | None = None,
    source: str | None = None,
    variant: str | None = None,
    label: str | None = None,
) -> RunRecord:
    """Chạy một model, trả về bản ghi số liệu đã chuẩn hoá.

    `args` là tham số truyền cho model: file .dat với chiều OPL, tham số dòng
    lệnh với hai chiều Python. Đường dẫn nên viết tương đối so với gốc dự án.
    """
    model = pathlib.Path(model)
    if not model.is_absolute():
        model = ROOT / model
    if not model.exists():
        raise FileNotFoundError(model)

    rec = RunRecord(
        problem=problem or model.parent.parent.name,
        dimension=dimension,
        engine=ENGINE[dimension],
        language=LANGUAGE[dimension],
        model_file=str(model.relative_to(ROOT) if model.is_relative_to(ROOT) else model),
        ok=False,
        source=source,
        variant=variant,
        label=label or dimension,
    )

    cmd = _command(dimension, model, [str(a) for a in (args or [])])
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT
        )
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        rec.wall_s = time.perf_counter() - t0
        rec.status = "Timeout"
        rec.stdout_tail = f"(quá {timeout}s)"
        return rec
    rec.wall_s = time.perf_counter() - t0

    combined = out + "\n" + err
    rec.community_limit_hit = _hit_community_limit(dimension, combined)

    # Ưu tiên dòng RESULT do model tự in.
    m = _RESULT_RE.search(out)
    if m:
        try:
            payload = json.loads(m.group(1))
        except json.JSONDecodeError:
            payload = {}
        for key in ("status", "objective", "solve_time_s", "branches", "fails"):
            if key in payload:
                setattr(rec, key, payload[key])
        rec.extra = {
            k: v
            for k, v in payload.items()
            if k not in ("status", "objective", "solve_time_s", "branches", "fails")
        }
    else:
        # Lùi về đọc log CP Optimizer (dùng chung cho opl và docplexcp).
        for key, pat in _CPO_PATTERNS.items():
            hit = pat.search(combined)
            if not hit:
                continue
            raw = hit.group(1)
            setattr(rec, key, _to_int(raw) if key in ("branches", "fails") else float(raw))
        if "Search completed" in combined:
            rec.status = "Completed"
        elif "No solution found" in combined:
            rec.status = "Infeasible"

    rec.ok = code == 0 and _is_success(rec.status)
    tail = combined.strip().splitlines()[-25:]
    rec.stdout_tail = "\n".join(tail)
    return rec


def load_manifest(problem_dir: str | pathlib.Path) -> dict[str, Any]:
    """Đọc manifest.json của một bài.

    manifest.json khai báo, cho từng chiều: file model, tham số truyền vào, và
    nguồn gốc (lấy mẫu chính thức hay viết mới). Notebook và runner dùng chung
    file này nên bảng ✅/✍️ trong báo cáo luôn khớp với code thực tế đang chạy.
    """
    problem_dir = pathlib.Path(problem_dir)
    if not problem_dir.is_absolute():
        problem_dir = ROOT / problem_dir
    return json.loads((problem_dir / "manifest.json").read_text(encoding="utf-8"))


def run_suite(problem_dir: str | pathlib.Path, timeout: int = 600) -> list[RunRecord]:
    """Chạy mọi chiều khai báo trong manifest.json của một bài."""
    manifest = load_manifest(problem_dir)
    records: list[RunRecord] = []
    for dim, spec in manifest["dimensions"].items():
        if spec.get("skip"):
            continue
        records.append(
            run(
                dim,
                spec["model"],
                spec.get("args", []),
                timeout=spec.get("timeout", timeout),
                problem=manifest.get("problem", pathlib.Path(problem_dir).name),
                source=spec.get("source"),
                variant=spec.get("variant"),
                label=dim,
            )
        )
    return records


def run_companions(problem_dir: str | pathlib.Path, timeout: int = 600) -> list[RunRecord]:
    """Chạy các bản phụ trợ khai trong khoá `companion` của manifest.

    Bản phụ trợ KHÔNG phải một chiều của báo cáo. Nó tồn tại khi mẫu chính thức
    của một nền tảng lại giải một biến thể khác (PLAN.md §2.7): khi đó cần thêm
    một bản port sang đúng biến thể chung thì hai trục so sánh mới có số liệu
    trên cùng một bài toán.
    """
    manifest = load_manifest(problem_dir)
    records: list[RunRecord] = []
    for name, spec in manifest.get("companion", {}).items():
        if spec.get("skip"):
            continue
        # Tên bản phụ trợ có dạng "<chiều>_<hậu tố>", ví dụ "docplexcp_portA".
        dim = next((d for d in ENGINE if name.startswith(d)), None)
        if dim is None:
            continue
        records.append(
            run(
                dim,
                spec["model"],
                spec.get("args", []),
                timeout=spec.get("timeout", timeout),
                problem=manifest.get("problem", pathlib.Path(problem_dir).name),
                source=spec.get("source"),
                variant=spec.get("variant"),
                label=name,
            )
        )
    return records


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suite", metavar="PROBLEM_DIR", help="chạy cả 3 chiều của một bài")
    ap.add_argument("--all", action="store_true", help="chạy mọi bài có manifest.json")
    ap.add_argument("--csv", metavar="FILE", help="ghi kết quả ra file CSV")
    ap.add_argument("--json", metavar="FILE", help="ghi kết quả ra file JSON")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("dimension", nargs="?", choices=sorted(ENGINE))
    ap.add_argument("model", nargs="?")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    if a.all:
        records = []
        for manifest in sorted((ROOT / "models").glob("*/manifest.json")):
            print(f"=== {manifest.parent.name} ===")
            for r in run_suite(manifest.parent, timeout=a.timeout):
                records.append(r)
    elif a.suite:
        records = run_suite(a.suite, timeout=a.timeout)
    elif a.dimension and a.model:
        records = [run(a.dimension, a.model, a.args, timeout=a.timeout)]
    else:
        ap.error("cần --all, --suite <dir>, hoặc <dimension> <model> [tham số ...]")

    for r in records:
        flag = "OK " if r.ok else "FAIL"
        print(
            f"[{flag}] {r.dimension:<10} {r.engine:<13} "
            f"status={r.status} obj={r.objective} "
            f"solve={r.solve_time_s}s wall={r.wall_s:.2f}s"
        )
        if not r.ok:
            print("  " + r.stdout_tail.replace("\n", "\n  "))

    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps([r.as_row() for r in records], indent=2, ensure_ascii=False)
        )
    if a.csv:
        import csv

        rows = [r.as_row() for r in records]
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return 0 if all(r.ok for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
