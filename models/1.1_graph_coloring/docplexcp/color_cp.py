"""Bài 1.1 — Tô màu đồ thị (Graph Coloring) | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: LẤY MẪU CHÍNH THỨC.
  IBMDecisionOptimization/docplex — examples/cp/basic/color.py
  Source file provided under Apache License, Version 2.0, January 2004
  (c) Copyright IBM Corp. 2015, 2022
  Bản cục bộ: vendor/docplex/examples/cp/basic/color.py

Phần DỰNG MÔ HÌNH (6 `integer_var` + 9 ràng buộc `!=`) giữ NGUYÊN VĂN bản gốc của
IBM. Những thứ dự án này thêm vào đều nằm ngoài phần đó:

  (1) cấu hình engine cục bộ (`import cpo_env`);
  (2) đọc dữ liệu chung data/coloring/map6.dat và `assert` rằng phần hardcode của
      IBM khớp đúng với nó — ba chiều không có đường nào chạy trên hai đồ thị khác nhau;
  (3) kiểm tra nghiệm theo tập cạnh của dữ liệu chung + dòng RESULT theo giao kèo
      của tools/runner.py;
  (4) tuỳ chọn `--min`: phần mở rộng tối ưu sắc số (xem cuối file).

Chạy:
    python3 models/1.1_graph_coloring/docplexcp/color_cp.py data/coloring/map6.dat
    python3 models/1.1_graph_coloring/docplexcp/color_cp.py data/coloring/map6.dat --min

GHI CHÚ NGÔN NGỮ (điểm so sánh với OPL — cùng engine CP Optimizer):
  Hai bản mẫu chính thức là bản dịch gần như từng dòng của nhau:

      OPL          Belgium != France;
      DOcplex.cp   mdl.add(Belgium != France)

  Khác biệt thật nằm ở tầng bao quanh, không ở tầng ràng buộc: OPL có tầng dữ liệu
  `.dat` tách rời và khối `execute` bằng ILOG Script để hậu xử lý, còn DOcplex.cp
  không có `.dat` — dữ liệu vào bằng chính cấu trúc dữ liệu Python, hậu xử lý bằng
  chính Python. Xem NOTES.md mục (d).
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401,E402  — trỏ docplex.cp sang cpoptimizer cục bộ
from opl_dat import load  # noqa: E402

from docplex.cp.model import CpoModel  # noqa: E402

# --- (2) dữ liệu dùng chung -------------------------------------------------
args = [a for a in sys.argv[1:] if not a.startswith("-")]
MIN_COLORS = "--min" in sys.argv
DAT = args[0] if args else "data/coloring/map6.dat"

data = load(DAT)
NB_COLORS = data["NbColors"]
COLOR_NAMES = data["ColorNames"]
COUNTRIES = data["Countries"]
EDGES = [tuple(e) for e in data["Edges"]]

# --- dựng mô hình: nguyên văn ví dụ chính thức của IBM -----------------------
# Create CPO model
mdl = CpoModel()

# Create model variables containing colors of the countries
Belgium     = mdl.integer_var(0, 3, "Belgium")
Denmark     = mdl.integer_var(0, 3, "Denmark")
France      = mdl.integer_var(0, 3, "France")
Germany     = mdl.integer_var(0, 3, "Germany")
Luxembourg  = mdl.integer_var(0, 3, "Luxembourg")
Netherlands = mdl.integer_var(0, 3, "Netherlands")
ALL_COUNTRIES = (Belgium, Denmark, France, Germany, Luxembourg, Netherlands)

# Create constraints
mdl.add(Belgium != France)
mdl.add(Belgium != Germany)
mdl.add(Belgium != Netherlands)
mdl.add(Belgium != Luxembourg)
mdl.add(Denmark != Germany)
mdl.add(France  != Germany)
mdl.add(France  != Luxembourg)
mdl.add(Germany != Luxembourg)
mdl.add(Germany != Netherlands)
# --- hết phần nguyên văn ----------------------------------------------------

# --- (2, tiếp) chốt chặn: bản hardcode của IBM PHẢI trùng dữ liệu chung -------
# Nếu ai đó sửa data/coloring/map6.dat mà quên rằng hai chiều lấy mẫu chính thức
# viết thẳng đồ thị vào model, chương trình dừng ngay tại đây thay vì âm thầm so
# sánh ba chiều trên ba bài toán khác nhau.
VAR_OF = dict(zip(COUNTRIES, ALL_COUNTRIES))
assert NB_COLORS == 4, f"Mẫu chính thức hardcode 4 màu, dữ liệu chung có {NB_COLORS}"
assert [v.get_name() for v in ALL_COUNTRIES] == COUNTRIES, (
    "Tập đỉnh hardcode không khớp Countries trong " + DAT
)
_HARDCODED_EDGES = {
    ("Belgium", "France"), ("Belgium", "Germany"), ("Belgium", "Netherlands"),
    ("Belgium", "Luxembourg"), ("Denmark", "Germany"), ("France", "Germany"),
    ("France", "Luxembourg"), ("Germany", "Luxembourg"), ("Germany", "Netherlands"),
}
assert _HARDCODED_EDGES == {tuple(e) for e in EDGES}, (
    "Tập cạnh hardcode không khớp Edges trong " + DAT
)

# --- (4) phần mở rộng: tối ưu sắc số ----------------------------------------
# Màu chỉ là NHÃN, nên mọi nghiệm dùng k màu đều đánh lại nhãn được thành 0..k-1
# ⇒ min(max nhãn + 1) chính là sắc số χ(G). Ràng buộc `<= K-1` vừa định nghĩa K
# vừa phá bớt đối xứng hoán vị màu. Chỉ 3 dòng chồng lên mô hình gốc.
if MIN_COLORS:
    K = mdl.integer_var(1, NB_COLORS, "K")
    for v in ALL_COUNTRIES:
        mdl.add(v <= K - 1)
    mdl.minimize(K)

# --- (1) giải ---------------------------------------------------------------
msol = mdl.solve(TimeLimit=10, LogVerbosity="Quiet")

violations = []
colors_used = None
objective = None
if msol:
    assign = {name: msol[var] for name, var in VAR_OF.items()}
    for a, b in EDGES:
        if assign[a] == assign[b]:
            violations.append((a, b))
    colors_used = len(set(assign.values()))
    objective = msol[K] if MIN_COLORS else None

    print("Solution status: " + str(msol.get_solve_status()))
    for country in ALL_COUNTRIES:
        print("   " + country.get_name() + ": " + COLOR_NAMES[msol[country]])
    print(f"CHECK violations={len(violations)} colorsUsed={colors_used}"
          f" (dữ liệu chung: {len(COUNTRIES)} đỉnh, {len(EDGES)} cạnh, {NB_COLORS} màu)")
else:
    print("No solution found")

infos = msol.get_solver_infos() if msol else {}
status = "NoSolution" if not msol else ("Invalid" if violations else str(msol.get_solve_status()))
print("RESULT " + json.dumps({
    "status": status,
    "objective": objective,
    "solve_time_s": round(msol.get_solve_time(), 4) if msol else None,
    "branches": infos.get("NumberOfBranches"),
    "fails": infos.get("NumberOfFails"),
    "colors_used": colors_used,
    "violations": len(violations),
    "n_vertices": len(COUNTRIES),
    "n_edges": len(EDGES),
    "mode": "min_colors" if MIN_COLORS else "csp",
}))
