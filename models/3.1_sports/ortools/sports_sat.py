"""Bài 3.1 — Lập lịch thi đấu thể thao (double round-robin) | Chiều OR-Tools (engine CP-SAT)

Nguồn: VIẾT MỚI. Google không phát hành ví dụ round-robin có break-minimization
trong bộ examples của OR-Tools; bản này là port ĐẦY ĐỦ mô hình `sports.mod` của
IBM (xem models/3.1_sports/opl/sports_reference.mod) sang CP-SAT.

Chạy:  python3 models/3.1_sports/ortools/sports_sat.py [data/sports/sports.dat]
       python3 models/3.1_sports/ortools/sports_sat.py --n 6 --workers 1

PHẠM VI: ĐẦY ĐỦ. Cả 14 ràng buộc của bản OPL đều được port, không lược bỏ ràng
buộc nào ⇒ objective (tổng số break) so trực tiếp được với chiều OPL.

╔══════════════════════════════════════════════════════════════════════════════╗
║ BỐN RÀNG BUỘC TOÀN CỤC CỦA sports.mod, DIỄN ĐẠT LẠI BẰNG CP-SAT              ║
╠════════════════════════╤═════════════════════════════════════════════════════╣
║ OPL / CP Optimizer     │ CP-SAT                                              ║
╠════════════════════════╪═════════════════════════════════════════════════════╣
║ allowedAssignments(    │ ✅ CÓ SẴN — add_allowed_assignments([h,a,g], tuples) ║
║   tupleSet, h, a, g)   │    Cùng ngữ nghĩa ràng buộc bảng. 0 biến phụ.       ║
╟────────────────────────┼─────────────────────────────────────────────────────╢
║ allDifferent(array)    │ ✅ CÓ SẴN — add_all_different(array). 0 biến phụ.    ║
╟────────────────────────┼─────────────────────────────────────────────────────╢
║ inverse(f, g)          │ ✅ CÓ SẴN — add_inverse(f, g).                       ║
║                        │ ⚠ CP-SAT bắt buộc miền 0..k-1; OPL đánh số 1..k     ║
║                        │    ⇒ phải đổi id trận sang gốc 0 khi dựng bảng.     ║
╟────────────────────────┼─────────────────────────────────────────────────────╢
║ count(array, t)        │ ❌ KHÔNG CÓ — phải diễn đạt vòng.                    ║
║  (reify thành          │    Mã hoá 1-hot toàn bộ home[w][g] bằng             ║
║   playHome[t][w])      │    add_map_domain, rồi playHome[t][w] = tổng bool.   ║
║                        │    Giá: n × nbWeeks × (n/2) biến bool phụ.          ║
╚════════════════════════╧═════════════════════════════════════════════════════╝

Ngoài bốn ràng buộc trên còn ba chỗ nữa CP-SAT phải diễn đạt vòng — xem các mục
(C8), (C11) và ghi chú `div`/`abs`/`%` trong thân file. Bảng đối chiếu đầy đủ kèm
số biến phụ đo được nằm ở NOTES.md mục (d).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from opl_dat import load  # noqa: E402  — đọc đúng file .dat mà chiều OPL dùng

from ortools.sat.python import cp_model  # noqa: E402


def game_id(h: int, a: int, n: int) -> int:
    """Id trận (gốc 0) của cặp <đội nhà h, đội khách a>, đúng công thức của OPL.

    Bản gốc:  (h-1)*(n-1) + a - (a > h)      -> đánh số 1..n(n-1)
    Ở đây trừ thêm 1 vì `add_inverse` của CP-SAT BẮT BUỘC miền phải là 0..k-1,
    trong khi OPL cho phép miền 1..k. Đây là khác biệt kỹ thuật đầu tiên gặp phải
    khi port `inverse`.
    """
    return (h - 1) * (n - 1) + a - int(a > h) - 1


def build_and_solve(n: int, time_limit: float = 60.0, workers: int = 1, seed: int = 0,
                    verbose: bool = True) -> dict:
    """Giải mô hình. Mặc định `workers = 1` và `seed = 0` để số liệu tái lập được:
    CP-SAT chạy đa luồng thì `branches`/`conflicts` đổi giữa các lần chạy, làm bảng
    so sánh vô nghĩa (PLAN.md §2.4). Muốn đo lợi ích đa luồng thì truyền --workers N.
    """
    assert n % 2 == 0, "n phải chẵn"

    # ---- tham số suy ra, đúng như sports.mod ---------------------------------
    nb_weeks = 2 * (n - 1)
    nb_games_per_week = n // 2
    nb_games = n * (n - 1)
    mid = nb_weeks // 2 + 1                       # tuần đầu tiên của nửa sau mùa giải
    overlap = min(n // 2, 6) if n >= 6 else 0     # khoảng cách tối thiểu giữa hai lượt

    WEEKS = range(nb_weeks)                       # 0-based nội bộ; in ra thì +1
    SLOTS = range(nb_games_per_week)
    TEAMS = range(1, n + 1)                       # 1-based, giữ như OPL

    model = cp_model.CpModel()
    nb_aux = 0                                    # đếm biến phụ do CP-SAT thiếu primitive

    # ---- biến quyết định (tương ứng 1-1 với sports.mod) ----------------------
    games = {(w, g): model.new_int_var(0, nb_games - 1, f"games_{w}_{g}")
             for w in WEEKS for g in SLOTS}
    home = {(w, g): model.new_int_var(1, n, f"home_{w}_{g}")
            for w in WEEKS for g in SLOTS}
    away = {(w, g): model.new_int_var(1, n, f"away_{w}_{g}")
            for w in WEEKS for g in SLOTS}
    # weekOfGame 0-based: tuần thật = week_of_game + 1
    week_of_game = [model.new_int_var(0, nb_weeks - 1, f"weekOfGame_{k}") for k in range(nb_games)]
    all_slots = [model.new_int_var(0, nb_games - 1, f"allSlots_{k}") for k in range(nb_games)]
    play_home = {(t, w): model.new_bool_var(f"playHome_{t}_{w}") for t in TEAMS for w in WEEKS}
    team_breaks = [model.new_int_var(0, nb_weeks // 2, f"teamBreaks_{t}") for t in TEAMS]

    # =========================================================================
    # (C1) allowedAssignments — RÀNG BUỘC BẢNG.  ✅ CP-SAT có sẵn.
    # Bộ ba (đội nhà, đội khách, id trận) phải nằm trong tập hợp lệ. Ràng buộc
    # này gánh luôn hai việc: cấm đội tự đá với mình, và ĐỊNH NGHĨA id trận theo
    # cặp (nhà, khách) — không cần viết công thức id thành ràng buộc số học.
    # =========================================================================
    play_slots = [(h, a, game_id(h, a, n)) for h in TEAMS for a in TEAMS if a != h]
    for w in WEEKS:
        for g in SLOTS:
            model.add_allowed_assignments([home[w, g], away[w, g], games[w, g]], play_slots)

    # =========================================================================
    # (C2) allDifferent — mỗi tuần, n chỗ đá (n/2 chủ nhà + n/2 khách) phải là n
    # đội khác nhau ⇒ mỗi đội đá đúng một trận mỗi tuần.  ✅ CP-SAT có sẵn.
    # =========================================================================
    for w in WEEKS:
        model.add_all_different([home[w, g] for g in SLOTS] + [away[w, g] for g in SLOTS])

    # =========================================================================
    # (C3) inverse — biểu diễn kép slot <-> trận.  ✅ CP-SAT có sẵn (add_inverse).
    # flat[s] = id trận xếp ở slot s;  all_slots[k] = slot của trận k.
    # ⚠ Khác biệt duy nhất: CP-SAT bắt hai mảng cùng kích thước và miền 0..k-1.
    # =========================================================================
    flat = [games[w, g] for w in WEEKS for g in SLOTS]   # slot s = w*nb_games_per_week + g
    model.add_inverse(flat, all_slots)

    # (C4) weekOfGame = allSlots div nbGamesPerWeek.
    # OPL viết thẳng `div` trên biểu thức biến; CP-SAT phải gọi ràng buộc chuyên
    # dụng add_division_equality (không có toán tử // trên IntVar).
    for k in range(nb_games):
        model.add_division_equality(week_of_game[k], all_slots[k], nb_games_per_week)

    # =========================================================================
    # (C5) Hai lượt của cùng một cặp đấu phải ở HAI NỬA MÙA khác nhau, và
    # (C6) cách nhau ít nhất `overlap` tuần.
    #
    # OPL viết:  (weekOfGame[g1] >= mid) == (weekOfGame[g2] < mid)
    # tức là reify hai bất đẳng thức rồi so bằng. CP-SAT không reify ngầm được:
    # phải tạo biến bool `second_half[k]` và buộc hai chiều bằng only_enforce_if.
    # Giá: nbGames biến bool phụ.
    # =========================================================================
    second_half = [model.new_bool_var(f"secondHalf_{k}") for k in range(nb_games)]
    nb_aux += nb_games
    for k in range(nb_games):
        # week_of_game là 0-based nên "nửa sau" là week_of_game >= mid-1
        model.add(week_of_game[k] >= mid - 1).only_enforce_if(second_half[k])
        model.add(week_of_game[k] <= mid - 2).only_enforce_if(~second_half[k])

    for i in TEAMS:
        for j in TEAMS:
            if i >= j:
                continue
            g1 = game_id(i, j, n)      # i đá sân nhà
            g2 = game_id(j, i, n)      # j đá sân nhà
            # đúng một trong hai lượt nằm ở nửa sau mùa giải
            model.add(second_half[g1] + second_half[g2] == 1)
            if overlap:
                # |w1 - w2| >= overlap. OPL có abs() ngay trong biểu thức ràng buộc;
                # CP-SAT phải vật chất hoá bằng add_abs_equality + 1 biến phụ.
                d = model.new_int_var(0, nb_weeks - 1, f"gap_{g1}_{g2}")
                nb_aux += 1
                model.add_abs_equality(d, week_of_game[g1] - week_of_game[g2])
                model.add(d >= overlap)

    # =========================================================================
    # (C7) playHome[t][w] == count(home[w][*], t)   ❌ CP-SAT KHÔNG CÓ `count`.
    #
    # Diễn đạt vòng: mã hoá 1-hot toàn bộ biến home[w][g] bằng add_map_domain
    #     is_home[w][g][t] = 1  <=>  home[w][g] == t
    # rồi playHome[t][w] = tổng các bool đó theo g. Vì mỗi tuần một đội đá nhiều
    # nhất một trận (C2), tổng này tự nằm trong {0,1} nên gán được cho biến bool.
    #
    # GIÁ PHẢI TRẢ: n × nbWeeks × (n/2) biến bool phụ + nbWeeks × (n/2) ràng buộc
    # exactly-one. Bản OPL: 0 biến phụ, `count` lo hết.
    # =========================================================================
    is_home = {}
    for w in WEEKS:
        for g in SLOTS:
            col = [model.new_bool_var(f"isHome_{w}_{g}_{t}") for t in TEAMS]
            nb_aux += n
            # add_map_domain: col[t-1] <=> (home[w][g] == t). offset=1 vì đội đánh số từ 1.
            model.add_map_domain(home[w, g], col, offset=1)
            for idx, t in enumerate(TEAMS):
                is_home[w, g, t] = col[idx]
    for t in TEAMS:
        for w in WEEKS:
            model.add(sum(is_home[w, g, t] for g in SLOTS) == play_home[t, w])

    # =========================================================================
    # (C8) Không được ba tuần liên tiếp cùng sân: 1 <= sum 3 tuần <= 2.
    # Thuần tuyến tính ⇒ cả hai engine viết như nhau.
    # =========================================================================
    for t in TEAMS:
        for w in range(nb_weeks - 2):
            model.add_linear_constraint(sum(play_home[t, k] for k in (w, w + 1, w + 2)), 1, 2)

    # =========================================================================
    # (C9) teamBreaks[t] = số tuần w mà playHome[t][w-1] == playHome[t][w].
    # OPL cộng thẳng biểu thức so sánh `(a == b)` vào một tổng — OPL tự reify.
    # CP-SAT không cho phép: mỗi số hạng phải là một biến bool được buộc hai chiều.
    # Giá: n × (nbWeeks-1) biến bool phụ.
    # =========================================================================
    brk = {}
    for t in TEAMS:
        for w in range(1, nb_weeks):
            b = model.new_bool_var(f"break_{t}_{w}")
            nb_aux += 1
            # b = 1  <=>  playHome[t][w-1] == playHome[t][w]
            model.add(play_home[t, w - 1] == play_home[t, w]).only_enforce_if(b)
            model.add(play_home[t, w - 1] + play_home[t, w] == 1).only_enforce_if(~b)
            brk[t, w] = b
        model.add(team_breaks[t - 1] == sum(brk[t, w] for w in range(1, nb_weeks)))

    # (C10) Mở màn sân nhà thì khép lại sân khách và ngược lại.
    for t in TEAMS:
        model.add(play_home[t, 0] + play_home[t, nb_weeks - 1] == 1)

    # ---- "Catalyzing constraints" của bản gốc: dư về logic, cần cho hiệu năng --
    # (C11) Số trận nhà = số trận khách.
    for t in TEAMS:
        model.add(sum(play_home[t, w] for w in WEEKS) == nb_weeks // 2)

    # (C12) Số break của mỗi đội phải chẵn.
    # OPL: `teamBreaks[t] % 2 == 0`. CP-SAT có add_modulo_equality nhưng cần một
    # biến đích ⇒ 1 biến phụ mỗi đội.
    for t in TEAMS:
        r = model.new_int_var(0, 1, f"breaksMod2_{t}")
        nb_aux += 1
        model.add_modulo_equality(r, team_breaks[t - 1], 2)
        model.add(r == 0)

    # ---- Phá đối xứng ---------------------------------------------------------
    # (C13) Đội hoán vị được cho nhau ⇒ cố định hẳn tuần 1.
    for g in SLOTS:
        model.add(home[0, g] == 2 * g + 1)
        model.add(away[0, g] == 2 * g + 2)

    # (C14) Thứ tự các trận trong một tuần là tuỳ ý ⇒ ép tăng dần theo id trận.
    for w in WEEKS:
        for g in range(1, nb_games_per_week):
            model.add(games[w, g] > games[w, g - 1])

    # ---- mục tiêu -------------------------------------------------------------
    total_breaks = sum(team_breaks)
    model.minimize(total_breaks)

    # ---- giải -----------------------------------------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    # Cố định để số liệu tái lập được — xem PLAN.md §2.4.
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.perf_counter()
    status = solver.solve(model)
    wall = time.perf_counter() - t0

    solved = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    obj = int(solver.value(total_breaks)) if solved else None

    if solved and verbose:
        print(f"Solution at {obj}")
        for w in WEEKS:
            cells = "  ".join(
                f"{solver.value(home[w, g]):>2}-{solver.value(away[w, g]):<2}" for g in SLOTS
            )
            print(f"Week {w + 1:>2}: {cells}")
        print("Team schedules")
        for t in TEAMS:
            row, brks, prev = [], 0, -1
            for w in WEEKS:
                for g in SLOTS:
                    if solver.value(home[w, g]) == t:
                        row.append(f"{solver.value(away[w, g]):>2}H")
                        brks += int(prev == 0)
                        prev = 0
                    elif solver.value(away[w, g]) == t:
                        row.append(f"{solver.value(home[w, g]):>2}A")
                        brks += int(prev == 1)
                        prev = 1
            print(f"T {t}:  " + " ".join(row) + f"   {brks} breaks")

    if solved:
        # Cấu trúc nghiệm cho phần vẽ hình (giao kèo SOLUTION của tools/runner.py).
        # Mang theo CẢ HAI cách nhìn cùng một lịch: `games` là lưới tuần × trận,
        # `team_weeks` là lịch riêng từng đội — chỉ ở cách nhìn thứ hai mới thấy
        # được BREAK, tức là chính hàm mục tiêu. Kèm luôn `is_break` đã tính sẵn
        # nên hình vẽ không phải dựng lại định nghĩa break.
        opponents = {}          # (đội, tuần 0-based) -> (đối thủ, có đá sân nhà không)
        games_out = []
        for w in WEEKS:
            for g in SLOTS:
                h = int(solver.value(home[w, g]))
                a = int(solver.value(away[w, g]))
                games_out.append({"week": w + 1, "slot": g, "home": h, "away": a})
                opponents[h, w] = (a, True)
                opponents[a, w] = (h, False)

        team_weeks = []
        for t in TEAMS:
            for w in WEEKS:
                opp, at_home = opponents[t, w]
                team_weeks.append({
                    "team": t,
                    "week": w + 1,
                    "opponent": opp,
                    "at_home": at_home,
                    # break = tuần này cùng sân với tuần trước (tuần 1 không có).
                    "is_break": w > 0 and at_home == opponents[t, w - 1][1],
                })

        print("SOLUTION " + json.dumps({
            "problem": "sports",
            "variant": "A",
            "n": n,
            "teams": list(TEAMS),
            "nb_weeks": nb_weeks,
            "nb_games_per_week": nb_games_per_week,
            "total_breaks": obj,
            "games": games_out,
            "team_weeks": team_weeks,
            "team_breaks": [
                {"team": t, "breaks": int(solver.value(team_breaks[t - 1]))}
                for t in TEAMS
            ],
        }))

    return {
        "status": solver.status_name(status),
        "objective": obj,
        "solve_time_s": round(solver.wall_time, 4),
        "branches": solver.num_branches,
        "fails": solver.num_conflicts,      # CP-SAT đếm conflicts, không phải fails
        "n": n,
        "nb_weeks": nb_weeks,
        "nb_games": nb_games,
        "aux_bool_vars": nb_aux,            # số biến phụ sinh ra vì CP-SAT thiếu primitive
        "wall_s": round(wall, 4),
        "variant": "A (sports.mod — min tổng break)",
    }


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dat", nargs="*", default=None,
                    help="file .dat của OPL (mặc định data/sports/sports.dat)")
    ap.add_argument("--n", type=int, default=None, help="ghi đè số đội")
    ap.add_argument("--time-limit", type=float, default=60.0)
    # Mặc định 1 worker + seed cố định: số liệu phải tái lập được (PLAN.md §2.4).
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    return ap.parse_args()


if __name__ == "__main__":
    a = _parse_args()
    if a.n is not None:
        n_teams = a.n
    else:
        files = a.dat or ["data/sports/sports.dat"]
        root = pathlib.Path(__file__).resolve().parents[3]
        n_teams = int(load(*[f if pathlib.Path(f).exists() else root / f for f in files])["n"])
    print("RESULT " + json.dumps(build_and_solve(
        n_teams, time_limit=a.time_limit, workers=a.workers, seed=a.seed, verbose=not a.quiet
    )))
