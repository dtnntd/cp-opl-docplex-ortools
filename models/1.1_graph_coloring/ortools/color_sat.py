"""Bài 1.1 — Tô màu đồ thị (Graph Coloring) | Chiều OR-Tools (engine CP-SAT)

Nguồn: ✍️ VIẾT MỚI. Bộ hướng dẫn chính thức của CP-SAT
(developers.google.com/optimization) không có trang graph coloring — phần CP chỉ
có N-Queens và cryptarithmetic, phần scheduling có job-shop và nurse rostering.
Trong kho or-tools chỉ có bản đóng góp ở `examples/contrib`, không phải tài liệu
chính thức, và gói `ortools` cài qua pip không kèm thư mục examples.

Khác hai chiều lấy mẫu chính thức (vốn viết thẳng 6 nước và 9 cạnh vào model),
bản này DỰNG MÔ HÌNH TỪ DỮ LIỆU: đọc data/coloring/map6.dat — đúng file mà chiều
OPL nạp cho oplrun — qua tools/opl_dat.py. Ba chiều vì thế chạy trên cùng một đồ
thị và cùng một số màu.

Chạy:
    python3 models/1.1_graph_coloring/ortools/color_sat.py data/coloring/map6.dat
    python3 models/1.1_graph_coloring/ortools/color_sat.py data/coloring/map6.dat --min

GHI CHÚ ENGINE (điểm so sánh với DOcplex.cp — cùng Python, khác engine):
  Cú pháp gần như trùng khít: `mdl.add(x != y)` ↔ `model.add(x != y)`. Khác biệt
  nằm bên dưới. CP-SAT dịch mỗi biến nguyên miền {0..3} thành các literal SAT rồi
  giải bằng lazy clause generation, nên nó báo CONFLICTS (mệnh đề xung đột học
  được) chứ không phải FAILS (nhánh chết) như CP Optimizer — hai đại lượng KHÔNG
  so sánh trực tiếp với nhau được.

  Bài này nhỏ tới mức presolve của CP-SAT nuốt gọn: nó ra nghiệm với 0 conflict,
  trong khi CP Optimizer phải duyệt vài trăm nhánh. Đó không phải "engine mạnh
  hơn" — đó là hai chiến lược khác nhau, và ở bài 3.2 thứ tự bị đảo lại.

  CP-SAT chạy đa luồng nên số liệu đổi giữa các lần chạy; ở đây cố định
  num_search_workers=1 và random_seed=0 để con số trong NOTES.md tái lập được.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from opl_dat import load  # noqa: E402

from ortools.sat.python import cp_model  # noqa: E402

# ---- dữ liệu dùng chung: đúng file .dat mà chiều OPL nạp cho oplrun ---------
argv = [a for a in sys.argv[1:] if not a.startswith("-")]
MIN_COLORS = "--min" in sys.argv
DAT = argv[0] if argv else "data/coloring/map6.dat"

data = load(DAT)
NB_COLORS: int = data["NbColors"]
COLOR_NAMES: list[str] = data["ColorNames"]
COUNTRIES: list[str] = data["Countries"]
EDGES: list[tuple[str, str]] = [tuple(e) for e in data["Edges"]]

unknown = {c for e in EDGES for c in e} - set(COUNTRIES)
assert not unknown, f"Cạnh trỏ tới đỉnh không khai báo: {sorted(unknown)}"

# ---- dựng mô hình ----------------------------------------------------------
model = cp_model.CpModel()

# color[c] = chỉ số màu của đỉnh c. Miền 0..NbColors-1 đã nuốt luôn ràng buộc
# "mỗi đỉnh đúng một màu" — không phải viết thành ràng buộc riêng như khi mã hoá
# nhị phân x[c][k]. Đây là nét đặc trưng của CP so với MILP.
color = {c: model.new_int_var(0, NB_COLORS - 1, c) for c in COUNTRIES}

# Hai đỉnh kề nhau khác màu.
for a, b in EDGES:
    model.add(color[a] != color[b])

# ---- phần mở rộng: tối ưu sắc số -------------------------------------------
# Màu chỉ là NHÃN nên mọi nghiệm dùng k màu đều đánh lại nhãn được thành 0..k-1
# ⇒ min(max nhãn + 1) chính là sắc số χ(G).
K = None
if MIN_COLORS:
    K = model.new_int_var(1, NB_COLORS, "K")
    for c in COUNTRIES:
        model.add(color[c] <= K - 1)
    model.minimize(K)

# ---- giải ------------------------------------------------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 1   # tái lập được số liệu (xem docstring)
solver.parameters.random_seed = 0
status = solver.solve(model)

violations: list[tuple[str, str]] = []
colors_used = None
objective = None
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assign = {c: solver.value(color[c]) for c in COUNTRIES}
    violations = [(a, b) for a, b in EDGES if assign[a] == assign[b]]
    colors_used = len(set(assign.values()))
    objective = solver.value(K) if MIN_COLORS else None

    for c in COUNTRIES:
        print(f"   {c}: {COLOR_NAMES[assign[c]]}")
    print(f"CHECK violations={len(violations)} colorsUsed={colors_used}"
          f" (dữ liệu chung: {len(COUNTRIES)} đỉnh, {len(EDGES)} cạnh, {NB_COLORS} màu)")
else:
    print("No solution found")

print("RESULT " + json.dumps({
    "status": "Invalid" if violations else solver.status_name(status),
    "objective": objective,
    "solve_time_s": round(solver.wall_time, 4),
    "branches": solver.num_branches,
    # CP-SAT không có khái niệm "fails"; conflicts là đại lượng gần nhất.
    "fails": solver.num_conflicts,
    "colors_used": colors_used,
    "violations": len(violations),
    "n_vertices": len(COUNTRIES),
    "n_edges": len(EDGES),
    "mode": "min_colors" if MIN_COLORS else "csp",
}))
