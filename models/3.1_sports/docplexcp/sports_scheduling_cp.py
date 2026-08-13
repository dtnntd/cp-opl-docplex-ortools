"""Bài 3.1 — Lập lịch thi đấu thể thao | Chiều DOcplex.cp (engine CP Optimizer)

Nguồn: LẤY MẪU CHÍNH THỨC.
  IBMDecisionOptimization/docplex — examples/cp/jupyter/sports_scheduling.ipynb
  "Use decision optimization to help a sports league schedule its games"
  Copyright (c) 2017, 2018 IBM. IPLA licensed Sample Materials.
  Bản sao cục bộ: vendor/docplex/examples/cp/jupyter/sports_scheduling.ipynb

Phần DỰNG MÔ HÌNH giữ NGUYÊN VĂN các ô code của notebook (ô 7, 8, 16, 18, 20, 22,
24, 26). Chỉ bổ sung: cấu hình engine cục bộ, tham số n qua dòng lệnh, in lời giải
bằng text thay cho pandas/HTML của notebook, và dòng RESULT theo giao kèo của
tools/runner.py. KHÔNG thêm/bớt/sửa một ràng buộc nào.

Chạy:  python3 models/3.1_sports/docplexcp/sports_scheduling_cp.py [n]

╔══════════════════════════════════════════════════════════════════════════════╗
║ CẢNH BÁO QUAN TRỌNG — HAI MẪU CHÍNH THỨC CỦA IBM LÀ HAI BÀI TOÁN KHÁC NHAU   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ sports.mod (chiều OPL)        : double round-robin có sân nhà/sân khách,      ║
║                                 mục tiêu MIN tổng số break.      -> biến thể A║
║ sports_scheduling.ipynb (file này): lịch NFL hai bảng đấu, không phân biệt    ║
║                                 sân nhà/khách theo tuần, mục tiêu MAX tổng    ║
║                                 tuần của các trận liên bảng.     -> biến thể B║
║                                                                              ║
║ IBM đặt cùng tên "sports scheduling" cho hai mô hình khác hẳn nhau. Vì vậy    ║
║ KHÔNG so objective của chiều này với hai chiều còn lại. Chi tiết ở NOTES.md   ║
║ mục (c). Bản port biến thể A sang docplex.cp — để so được TRỤC NGÔN NGỮ và    ║
║ TRỤC ENGINE trên cùng một bài — nằm ở sports_portA_cp.py cạnh file này.       ║
╚══════════════════════════════════════════════════════════════════════════════╝

GHI CHÚ NGÔN NGỮ (điểm so sánh với OPL):
  `allowed_assignments` ở đây được dùng như một BIỂU THỨC BOOL rồi nhân với hệ số
  và cộng vào một tổng:

      sum(intra(t1,t2) * allowed_assignments(plays[...], FIRST_HALF_WEEKS)) >= k

  Cùng cái tên đó trong sports.mod lại là RÀNG BUỘC BẢNG ba ngôi trên một tupleset.
  Một cái tên, hai chữ ký, hai ngữ nghĩa — và bản OPL không reify được nó thành số
  hạng của một tổng. Xem NOTES.md mục (d).
"""

import json
import pathlib
import sys
from collections import namedtuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401  — trỏ docplex.cp sang cpoptimizer cục bộ

from docplex.cp.model import CpoModel, all_diff, allowed_assignments, integer_var, maximize

# ---------------------------------------------------------------------------
# n lấy từ dòng lệnh (mặc định 6) để BA CHIỀU DÙNG CHUNG cùng một số đội.
# Notebook gốc tham số hoá bằng nbTeamsInDivision; ở đây n = 2*nbTeamsInDivision.
# Với numberOfMatchesToPlay = 2, công thức số tuần của notebook
#     (k-1)*2 + k*2 = 4k-2
# TRÙNG KHÍT với công thức của sports.mod:  2*(n-1) = 2*(2k-1) = 4k-2.
# ⇒ n = 6 cho 10 tuần ở cả hai biến thể. Số tuần khớp nhau, bài toán thì không.
# ---------------------------------------------------------------------------
N_TEAMS_ARG = int(sys.argv[1]) if len(sys.argv) > 1 else 6
assert N_TEAMS_ARG % 2 == 0, "n phải chẵn"
NB_TEAMS_IN_DIVISION = N_TEAMS_ARG // 2

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 7: dữ liệu đội =============================
# Teams in 1st division
TEAM_DIV1 = ["Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers", "Houston Texans",
             "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans", "Buffalo Bills", "Miami Dolphins",
             "New England Patriots", "New York Jets", "Denver Broncos", "Kansas City Chiefs", "Oakland Raiders",
             "San Diego Chargers"]

# Teams in 2nd division
TEAM_DIV2 = ["Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings", "Atlanta Falcons",
             "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers", "Dallas Cowboys", "New York Giants",
             "Philadelphia Eagles", "Washington Redskins", "Arizona Cardinals", "San Francisco 49ers",
             "Seattle Seahawks", "St. Louis Rams"]

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 8: tham số =================================
NUMBER_OF_MATCHES_TO_PLAY = 2  # Number of match to play between two teams on the league

T_SCHEDULE_PARAMS = (namedtuple("TScheduleParams",
                                ["nbTeamsInDivision",
                                 "maxTeamsInDivision",
                                 "numberOfMatchesToPlayInsideDivision",
                                 "numberOfMatchesToPlayOutsideDivision"
                                 ]))
# Schedule parameters: depending on their values, you may overreach the Community Edition of CPLEX
SCHEDULE_PARAMS = T_SCHEDULE_PARAMS(NB_TEAMS_IN_DIVISION,   # nbTeamsInDivision  (gốc: 5)
                                    10,  # maxTeamsInDivision
                                    NUMBER_OF_MATCHES_TO_PLAY,  # numberOfMatchesToPlayInsideDivision
                                    NUMBER_OF_MATCHES_TO_PLAY   # numberOfMatchesToPlayOutsideDivision
                                    )

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 16: chuẩn bị dữ liệu =======================
NB_TEAMS = 2 * SCHEDULE_PARAMS.nbTeamsInDivision
TEAMS = range(NB_TEAMS)

# Calculate the number of weeks necessary
NB_WEEKS = (SCHEDULE_PARAMS.nbTeamsInDivision - 1) * SCHEDULE_PARAMS.numberOfMatchesToPlayInsideDivision \
            + SCHEDULE_PARAMS.nbTeamsInDivision * SCHEDULE_PARAMS.numberOfMatchesToPlayOutsideDivision

# Weeks to schedule
WEEKS = tuple(range(NB_WEEKS))

# Season is split into two halves
FIRST_HALF_WEEKS = tuple(range(NB_WEEKS // 2))
NB_FIRST_HALS_WEEKS = NB_WEEKS // 3          # (lỗi chính tả "HALS" là của bản gốc)

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 18: biến quyết định ========================
mdl = CpoModel(name="SportsScheduling")

# Variables of the model
plays = {}
for i in range(NUMBER_OF_MATCHES_TO_PLAY):
    for t1 in TEAMS:
        for t2 in TEAMS:
            if t1 != t2:
                plays[(t1, t2, i)] = integer_var(1, NB_WEEKS, name="team1_{}_team2_{}_match_{}".format(t1, t2, i))

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 20: đối xứng cặp đấu =======================
# Constraints of the model
for t1 in TEAMS:
    for t2 in TEAMS:
        if t2 != t1:
            for i in range(NUMBER_OF_MATCHES_TO_PLAY):
                mdl.add(plays[(t1, t2, i)] == plays[(t2, t1, i)])  ### symmetrical match t1->t2 = t2->t1 at the ieme match

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 22: mỗi đội một trận mỗi tuần ==============
for t1 in TEAMS:
    mdl.add(all_diff([plays[(t1, t2, i)] for t2 in TEAMS if t2 != t1 for i in
                      range(NUMBER_OF_MATCHES_TO_PLAY)]))  ### team t1 must play one match per week

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 24: một phần trận nội bảng ở nửa đầu mùa ===
# Function that returns 1 if the two teams are in same division, 0 if not
def intra_divisional_pair(t1, t2):
    return int((t1 <= SCHEDULE_PARAMS.nbTeamsInDivision and t2 <= SCHEDULE_PARAMS.nbTeamsInDivision) or
               (t1 > SCHEDULE_PARAMS.nbTeamsInDivision and t2 > SCHEDULE_PARAMS.nbTeamsInDivision))

# Some intradivisional games should be in the first half
mdl.add(sum([intra_divisional_pair(t1, t2) * allowed_assignments(plays[(t1, t2, i)], FIRST_HALF_WEEKS)
             for t1 in TEAMS for t2 in [a for a in TEAMS if a != t1]
             for i in range(NUMBER_OF_MATCHES_TO_PLAY)]) >= NB_FIRST_HALS_WEEKS)

# === PHẦN NGUYÊN VĂN NOTEBOOK — ô 26: hàm mục tiêu ===========================
# Objective of the model is to schedule intradivisional games to be played late in the schedule
sm = []
for t1 in TEAMS:
    for t2 in TEAMS:
        if t1 != t2:
            if not intra_divisional_pair(t1, t2):
                for i in range(NUMBER_OF_MATCHES_TO_PLAY):
                    sm.append(plays[(t1, t2, i)])
mdl.add(maximize(sum(sm)))
# === HẾT PHẦN NGUYÊN VĂN =====================================================

msol = mdl.solve(TimeLimit=60, LogVerbosity="Quiet")

if msol:
    # Notebook gốc dựng bảng pandas + HTML; ở đây in text cho chạy được ngoài Jupyter.
    print(f"n = {NB_TEAMS} đội ({NB_TEAMS_IN_DIVISION} mỗi bảng), {NB_WEEKS} tuần")
    by_week = {w: [] for w in range(1, NB_WEEKS + 1)}
    for (t1, t2, i), var in plays.items():
        if t1 < t2:                     # mỗi cặp xuất hiện hai lần do ràng buộc đối xứng
            by_week[msol[var]].append((t1, t2, i, intra_divisional_pair(t1, t2)))
    for w in sorted(by_week):
        cells = " ".join(
            f"{t1}-{t2}{'*' if intra else ''}#{i}" for t1, t2, i, intra in sorted(by_week[w])
        )
        print(f"Week {w:>2}: {cells}")
    print("(* = trận nội bảng, #i = lượt đấu thứ i)")

infos = msol.get_solver_infos() if msol else {}
objs = msol.get_objective_values() if msol else None
print("RESULT " + json.dumps({
    "status": str(msol.get_solve_status()) if msol else "NoSolution",
    "objective": objs[0] if objs else None,
    "solve_time_s": round(msol.get_solve_time(), 4) if msol else None,
    "branches": infos.get("NumberOfBranches"),
    "fails": infos.get("NumberOfFails"),
    "n": NB_TEAMS,
    "nb_weeks": NB_WEEKS,
    "variant": "B (NFL hai bảng — max tổng tuần trận liên bảng); KHÔNG so objective với biến thể A",
}))
