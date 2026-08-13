"""Bài 3.1 — File PHỤ TRỢ cho phần so sánh, không phải một chiều của báo cáo.

Port mô hình `sports.mod` (biến thể A: double round-robin, min tổng break) sang
docplex.cp. Nguồn mô hình: IBM ILOG CPLEX Optimization Studio 22.2 —
opl/examples/opl/sports/sports.mod, Copyright IBM Corporation 1998, 2026.
Bản dịch sang Python: VIẾT MỚI cho dự án này.

VÌ SAO CẦN FILE NÀY
-------------------
Hai mẫu chính thức của IBM cho "sports scheduling" là HAI BÀI TOÁN KHÁC NHAU:

    opl/examples/opl/sports/sports.mod           -> biến thể A (min break)
    docplex/examples/cp/jupyter/sports_scheduling -> biến thể B (NFL hai bảng)

Nếu chỉ có hai file đó thì không trục so sánh nào sạch:
  * trục NGÔN NGỮ  (OPL vs docplex.cp, cùng engine CP Optimizer) — khác cả bài
  * trục ENGINE    (docplex.cp vs OR-Tools, cùng ngôn ngữ Python) — khác cả bài

File này cài ĐÚNG biến thể A bằng docplex.cp, nên:
  * so với models/3.1_sports/opl/sports.mod       -> cô lập được NGÔN NGỮ
  * so với models/3.1_sports/ortools/sports_sat.py -> cô lập được ENGINE

Chạy:  python3 models/3.1_sports/docplexcp/sports_portA_cp.py [data/sports/sports.dat]

QUAN SÁT TRUNG TÂM
------------------
Cả BỐN ràng buộc toàn cục của sports.mod đều có mặt trong docplex.cp với đúng ngữ
nghĩa: allowed_assignments, all_diff, inverse, count. Cùng engine thì cùng kho
ràng buộc — khác biệt OPL vs docplex.cp thuần tuý là CÚ PHÁP. Bản CP-SAT ở
../ortools/sports_sat.py thiếu `count` và phải bù bằng 180 biến bool 1-hot.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
import cpo_env  # noqa: F401,E402  — trỏ docplex.cp sang cpoptimizer cục bộ
from opl_dat import load  # noqa: E402  — đọc đúng file .dat mà chiều OPL dùng

from docplex.cp.model import CpoModel, binary_var, integer_var  # noqa: E402


def game_id(h: int, a: int, n: int) -> int:
    """Id trận (gốc 0). Bản OPL: (h-1)*(n-1) + a - (a>h), đánh số 1..n(n-1).

    Trừ 1 vì `inverse` của docplex.cp quy ước chỉ số 0-based
    (invf[f[i]] == i với i in [0, n-1]), còn `inverse` của OPL đi theo range
    khai báo của mảng, ở đây là 1..nbGames. Cùng một engine, cùng một ràng buộc,
    hai quy ước đánh chỉ số — một khác biệt thuần NGÔN NGỮ.
    """
    return (h - 1) * (n - 1) + a - int(a > h) - 1


def build_and_solve(n: int, time_limit: float = 60.0, verbose: bool = True) -> dict:
    assert n % 2 == 0, "n phải chẵn"

    nb_weeks = 2 * (n - 1)
    nb_games_per_week = n // 2
    nb_games = n * (n - 1)
    mid = nb_weeks / 2 + 1
    overlap = min(n // 2, 6) if n >= 6 else 0

    WEEKS = range(nb_weeks)          # 0-based nội bộ
    SLOTS = range(nb_games_per_week)
    TEAMS = range(1, n + 1)

    mdl = CpoModel(name="SportsRoundRobin")

    # ---- biến: tương ứng 1-1 với sports.mod ---------------------------------
    games = {(w, g): integer_var(0, nb_games - 1, f"games_{w}_{g}") for w in WEEKS for g in SLOTS}
    home = {(w, g): integer_var(1, n, f"home_{w}_{g}") for w in WEEKS for g in SLOTS}
    away = {(w, g): integer_var(1, n, f"away_{w}_{g}") for w in WEEKS for g in SLOTS}
    week_of_game = [integer_var(1, nb_weeks, f"weekOfGame_{k}") for k in range(nb_games)]
    all_slots = [integer_var(0, nb_games - 1, f"allSlots_{k}") for k in range(nb_games)]
    play_home = {(t, w): binary_var(f"playHome_{t}_{w}") for t in TEAMS for w in WEEKS}
    team_breaks = [integer_var(0, nb_weeks // 2, f"teamBreaks_{t}") for t in TEAMS]

    # (C1) ràng buộc bảng — cùng tên, cùng ngữ nghĩa với allowedAssignments của OPL
    play_slots = [(h, a, game_id(h, a, n)) for h in TEAMS for a in TEAMS if a != h]
    for w in WEEKS:
        for g in SLOTS:
            mdl.add(mdl.allowed_assignments([home[w, g], away[w, g], games[w, g]], play_slots))

    # (C2) mỗi tuần n chỗ đá là n đội khác nhau
    for w in WEEKS:
        mdl.add(mdl.all_diff([home[w, g] for g in SLOTS] + [away[w, g] for g in SLOTS]))

    # (C3) biểu diễn kép slot <-> trận
    flat = [games[w, g] for w in WEEKS for g in SLOTS]
    mdl.add(mdl.inverse(flat, all_slots))

    # (C4) tuần của một trận. docplex.cp cho viết `//` thẳng trên biểu thức biến,
    # không cần ràng buộc chuyên dụng như add_division_equality của CP-SAT.
    for k in range(nb_games):
        mdl.add(week_of_game[k] == all_slots[k] // nb_games_per_week + 1)

    # (C5)(C6) hai lượt ở hai nửa mùa, cách nhau >= overlap tuần.
    # Viết được ĐÚNG NHƯ OPL: so bằng giữa hai biểu thức bool, engine tự reify.
    for i in TEAMS:
        for j in TEAMS:
            if i >= j:
                continue
            g1, g2 = game_id(i, j, n), game_id(j, i, n)
            mdl.add((week_of_game[g1] >= mid) == (week_of_game[g2] < mid))
            if overlap:
                mdl.add(mdl.abs_of(week_of_game[g1] - week_of_game[g2]) >= overlap)

    # (C7) playHome = count(...). CP Optimizer có `count` như một biểu thức số ⇒
    # gán thẳng vào biến bool, KHÔNG sinh biến phụ nào.
    for t in TEAMS:
        for w in WEEKS:
            mdl.add(play_home[t, w] == mdl.count([home[w, g] for g in SLOTS], t))

    # (C8) không ba tuần liên tiếp cùng sân.
    # OPL viết bất đẳng thức kép `1 <= sum <= 2` thành MỘT ràng buộc; docplex.cp
    # có mdl.range(expr, lb, ub) tương đương, nên số ràng buộc sinh ra khớp nhau.
    for t in TEAMS:
        for w in range(nb_weeks - 2):
            mdl.add(mdl.range(sum(play_home[t, k] for k in (w, w + 1, w + 2)), 1, 2))

    # (C9) đếm break: cộng thẳng biểu thức so sánh vào tổng, engine tự reify
    for t in TEAMS:
        mdl.add(team_breaks[t - 1] ==
                sum((play_home[t, w - 1] == play_home[t, w]) for w in range(1, nb_weeks)))

    # (C10) mở màn sân nhà thì khép lại sân khách
    for t in TEAMS:
        mdl.add(play_home[t, 0] != play_home[t, nb_weeks - 1])

    # (C11) số trận nhà = số trận khách
    for t in TEAMS:
        mdl.add(sum(play_home[t, w] for w in WEEKS) == nb_weeks // 2)

    # (C12) số break của mỗi đội là số chẵn
    for t in TEAMS:
        mdl.add(team_breaks[t - 1] % 2 == 0)

    # (C13)(C14) phá đối xứng
    for g in SLOTS:
        mdl.add(home[0, g] == 2 * g + 1)
        mdl.add(away[0, g] == 2 * g + 2)
    for w in WEEKS:
        for g in range(1, nb_games_per_week):
            mdl.add(games[w, g] > games[w, g - 1])

    mdl.add(mdl.minimize(sum(team_breaks)))

    # Đặt ĐÚNG tham số engine mà sports.mod đặt trong khối execute của nó
    # (timeLimit=60, DefaultInferenceLevel="Extended") để phép so OPL vs
    # docplex.cp chỉ còn khác đúng một biến số: NGÔN NGỮ mô hình hoá.
    msol = mdl.solve(TimeLimit=time_limit, DefaultInferenceLevel="Extended",
                     LogVerbosity="Quiet")

    if msol and verbose:
        objs = msol.get_objective_values()
        print(f"Solution at {int(objs[0])}")
        for w in WEEKS:
            cells = "  ".join(f"{msol[home[w, g]]:>2}-{msol[away[w, g]]:<2}" for g in SLOTS)
            print(f"Week {w + 1:>2}: {cells}")

    infos = msol.get_solver_infos() if msol else {}
    objs = msol.get_objective_values() if msol else None
    return {
        "status": str(msol.get_solve_status()) if msol else "NoSolution",
        "objective": int(objs[0]) if objs else None,
        "solve_time_s": round(msol.get_solve_time(), 4) if msol else None,
        "branches": infos.get("NumberOfBranches"),
        "fails": infos.get("NumberOfFails"),
        "n": n,
        "nb_weeks": nb_weeks,
        "nb_games": nb_games,
        "aux_bool_vars": 0,   # không cần biến phụ nào: engine có đủ 4 ràng buộc toàn cục
        "variant": "A (sports.mod — min tổng break)",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dat", nargs="*", default=None)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.n is not None:
        n_teams = a.n
    else:
        files = a.dat or ["data/sports/sports.dat"]
        root = pathlib.Path(__file__).resolve().parents[3]
        n_teams = int(load(*[f if pathlib.Path(f).exists() else root / f for f in files])["n"])
    print("RESULT " + json.dumps(
        build_and_solve(n_teams, time_limit=a.time_limit, verbose=not a.quiet)))
