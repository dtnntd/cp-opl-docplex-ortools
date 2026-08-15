"""Vẽ NGHIỆM của từng bài — phần trực quan của báo cáo.

VÌ SAO CÓ FILE NÀY. Bảng số trả lời “nhanh bao nhiêu”, không trả lời “nghiệm
trông thế nào”. Người đọc thấy `makespan = 55` mà không thấy cái lịch, thấy
`13/20 nguyện vọng` mà không thấy ai trực ca nào. Module này lấy đúng cấu trúc
nghiệm mà model đã in ra (dòng `SOLUTION` — xem giao kèo ở đầu `tools/runner.py`)
rồi vẽ lại bằng matplotlib.

    from nbviz import *
    show_solution("2.1_jobshop")

BA NGUYÊN TẮC:

1. **Không chạy lại solver.** Bản ghi lấy qua `nbutil.runs()`, tức là dùng đúng
   kết quả đã cache trong phiên. Chạy lại thì hình vẽ có thể là một nghiệm KHÁC
   với nghiệm mà bảng số ngay phía trên vừa mô tả.
2. **Chỉ vẽ nghiệm của chiều `ortools`.** Đây là chiều duy nhất không cần giấy
   phép IBM, nên báo cáo dựng được trên mọi máy (kể cả Google Colab — xem
   `COLAB.md`). Ba chiều đã được đối chiếu ở ô `cross_check` ngay phía trên; hình
   vẽ là một minh hoạ cụ thể, không phải một phép kiểm thứ hai.
3. **Thiếu nghiệm thì IN MỘT DÒNG GIẢI THÍCH, không ném exception.** Máy không có
   CP Optimizer vẫn phải dựng được cả báo cáo; một cái hình không vẽ được không
   phải lý do để cả notebook dừng.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.lines as mlines  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

import nbutil  # noqa: E402

# --------------------------------------------------------------------------- #
# Bảng màu — DÙNG CHUNG toàn báo cáo
# --------------------------------------------------------------------------- #

#: Màu định danh của ba chiều. Giữ khớp với biểu đồ hiệu năng ở `nbcharts.py`:
#: cùng một chiều phải mang cùng một màu ở mọi hình, nếu không thì màu không còn
#: là định danh mà chỉ là trang trí.
#:
#: Bộ ba này ĐÃ QUA kiểm định của skill `dataviz` (nền sáng #fcfcfb và #ffffff, cả
#: `--pairs adjacent` lẫn `--pairs all`): dải sáng PASS · sàn chroma PASS · tách cặp
#: ΔE 9.7 ở protan/deutan và 14.5 ở tritan (ngưỡng 8) · thị lực thường ΔE 18.6 (sàn
#: 15) · tương phản nền ≥ 3:1. Bộ cũ (#0b5cad/#6a3d9a/#c1440e) TRƯỢT: cặp opl ↔
#: docplexcp chỉ ΔE 3.4 dưới mắt deutan — đúng hai chiều tạo nên trục NGÔN NGỮ.
#: Xuất phát từ họ Okabe–Ito (xanh #0072B2, tím hồng #CC79A7, đỏ cam #D55E00); tím
#: hồng và đỏ cam chỉnh tối thêm một bậc để qua sàn tương phản 3:1 trên nền #fcfcfb
#: và để chữ trắng in đè lên ô makespan (bài 3.2) còn đủ 5:1.
#: Đổi màu ở đây thì đổi luôn `DIMENSION_COLOR` của `nbcharts.py` — và chạy lại
#: validator, đừng ước lượng bằng mắt.
DIMENSION_COLORS = {
    "opl": "#0072b2",
    "docplexcp": "#c47ca8",
    "ortools": "#b85000",
}

#: Chiều dựng ra mọi hình trong file này (xem nguyên tắc 2 ở docstring).
VIZ_DIMENSION = "ortools"

#: Bảng màu phân loại, dùng cho các thực thể KHÔNG có thứ tự tự nhiên (job của
#: bài 2.1). Thứ tự slot là cơ chế an toàn cho người mù màu, không phải thẩm mỹ:
#: bộ 6 màu này đã qua kiểm tra dải sáng, sàn chroma, tách cặp kề dưới ba kiểu mù
#: màu và sàn thị lực thường. Đừng đảo thứ tự, đừng sinh thêm màu thứ 7.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]

# Nền và mực — một tông sáng, cố định (báo cáo xuất ra HTML nền trắng).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
#: Ô lưới trống / ô sáng của bàn cờ.
CELL_EMPTY = "#f0efec"
#: Ô tối của bàn cờ. Dùng lại cho ô "bị chặn" ở lưới thời khoá biểu (bài 3.2).
CELL_DARK = "#c9c8c1"
#: Ô ĐÃ XẾP của lưới thời khoá biểu (bài 3.2). Đây KHÔNG phải màu phân loại: bài
#: đó có 8 môn, quá bảng 6 màu đã kiểm định, nên môn được nhận diện bằng CHỮ còn
#: màu chỉ tách ba trạng thái của một ô (đã xếp / trống / lớp bận).
CELL_BOOKED = "#d6e3f3"
#: Màu trạng thái “đạt” — dùng cho ô trực ĐÚNG NGUYỆN VỌNG ở bài 2.2. Màu trạng
#: thái không bao giờ đứng một mình: ô đó còn mang thêm dấu ✓.
STATUS_GOOD = "#0ca30c"

#: Tên màu trong dữ liệu bài 1.1 -> mã màu vẽ. Ở bài này màu KHÔNG phải là lựa
#: chọn thẩm mỹ: nó chính là nghiệm, nên phải vẽ đúng màu mà model đã gán.
_COLOR_FILL = {
    "blue": "#2a78d6",
    "white": "#ffffff",
    "yellow": "#eda100",
    "green": "#008300",
    "red": "#e34948",
    "orange": "#eb6834",
    "black": "#0b0b0b",
    "gray": "#898781",
    "grey": "#898781",
}

#: Toạ độ đỉnh của bài 1.1, đặt cứng theo vị trí địa lý tương đối của 6 nước.
#: Cố ý KHÔNG dùng `networkx`: đồ thị có đúng 6 đỉnh, một layout tự động vừa
#: thêm một phụ thuộc vừa cho ra hình xáo trộn giữa các lần chạy.
_MAP6_XY = {
    "Belgium": (-0.95, 0.95),
    "Denmark": (0.75, 2.35),
    "France": (-1.35, -0.35),
    "Germany": (1.20, 1.10),
    "Luxembourg": (0.08, 0.28),
    "Netherlands": (-0.15, 1.85),
}


# --------------------------------------------------------------------------- #
# Hạ tầng chung
# --------------------------------------------------------------------------- #

def _ink_on(fill: str) -> str:
    """Mực đọc được trên một nền đã cho — trắng trên nền tối, đen trên nền sáng.

    Nhãn nằm TRONG một mảng màu là ngoại lệ duy nhất của quy tắc “chữ không mặc
    màu dữ liệu”; chọn theo độ sáng thì nhãn nào cũng đủ tương phản.
    """
    r, g, b = mcolors.to_rgb(fill)
    return "#ffffff" if (0.2126 * r + 0.7152 * g + 0.0722 * b) < 0.55 else INK


def _bare_axes(ax):
    """Trục trần: nền đúng tông giấy, không khung. Lưới ô tự nó là khung rồi."""
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _new_figure(size):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor(SURFACE)
    _bare_axes(ax)
    return fig, ax


def _title(fig, main: str, sub: str) -> float:
    """Đặt tiêu đề + câu chú thích, trả về mép trên còn lại cho vùng vẽ.

    Vị trí tính theo INCH tính từ mép trên rồi mới quy về toạ độ figure. Đặt
    thẳng bằng toạ độ figure (0.985 / 0.935) thì khoảng cách hai dòng co giãn
    theo chiều cao hình: cùng một cặp số, hình cao 5.6" thì rộng rãi còn hình cao
    3.6" thì tiêu đề chồng lên câu chú thích.
    """
    import textwrap

    h = fig.get_figheight()
    # Bề rộng ngắt dòng phải theo BỀ RỘNG HÌNH, không phải một hằng số: ở cỡ chữ
    # 9pt một ký tự rộng chừng 0.066", nên hình 5.8" chứa ~88 ký tự còn hình 11"
    # chứa ~165. Ngắt cứng ở một con số thì hình hẹp bị chữ tràn ra ngoài mép.
    lines = textwrap.wrap(sub, width=max(40, int(15.0 * fig.get_figwidth())))
    fig.suptitle(main, fontsize=13, fontweight="semibold", color=INK,
                 x=0.5, y=1 - 0.30 / h, ha="center", va="center")
    for i, line in enumerate(lines):
        fig.text(0.5, 1 - (0.50 + 0.18 * i) / h, line,
                 fontsize=9, color=INK_SECONDARY, ha="center", va="top")
    return 1 - (0.62 + 0.18 * len(lines)) / h


def _provenance(rec) -> str:
    """Câu ghi nguồn gốc của hình — chiều nào, engine nào."""
    return f"nghiệm của chiều `{rec.label or rec.dimension}` (engine {rec.engine})"


def _emit(fig):
    """Hiển thị hình trong notebook, trả về `Figure` khi chạy ngoài notebook.

    Trong notebook, trả thẳng `fig` sẽ khiến hình hiện HAI lần (một lần do
    backend inline dọn figure cuối ô, một lần do giá trị trả về). Hiển thị rồi
    đóng ngay là cách duy nhất chắc chắn chỉ có một ảnh.
    """
    try:
        from IPython import get_ipython
        from IPython.display import display
    except ImportError:
        return fig
    if get_ipython() is None:
        return fig
    display(fig)
    plt.close(fig)
    return None


# --------------------------------------------------------------------------- #
# Bài 1.1 — tô màu đồ thị
# --------------------------------------------------------------------------- #

def _draw_graph_coloring(sol: dict, rec):
    vertices = list(sol["vertices"])
    names = list(sol["color_names"])
    assign = sol["assignment"]

    # Đỉnh lạ (bộ dữ liệu khác map6) thì rải đều trên một vòng tròn.
    import math
    xy = dict(_MAP6_XY)
    unknown = [v for v in vertices if v not in xy]
    for i, v in enumerate(unknown):
        a = 2 * math.pi * i / max(len(unknown), 1)
        xy[v] = (1.4 * math.cos(a), 1.0 + 1.4 * math.sin(a))

    fig, ax = _new_figure((6.8, 5.8))

    for a, b in sol["edges"]:
        (x0, y0), (x1, y1) = xy[a], xy[b]
        ax.plot([x0, x1], [y0, y1], color=AXIS, linewidth=1.6,
                solid_capstyle="round", zorder=1)

    for v in vertices:
        x, y = xy[v]
        name = names[assign[v]]
        fill = _COLOR_FILL.get(name.lower(), SERIES[assign[v] % len(SERIES)])
        # Vòng viền mảnh là thứ duy nhất giữ cho đỉnh màu "white" còn nhìn thấy
        # được trên nền sáng — nó không phải đường phân tách giữa hai mảng màu.
        ax.scatter([x], [y], s=1250, c=[fill], edgecolors=AXIS,
                   linewidths=1.1, zorder=3)
        ax.text(x, y + 0.30, v, ha="center", va="bottom",
                fontsize=10, color=INK, zorder=4)
        # Tên màu viết ngay dưới đỉnh: định danh không bao giờ chỉ nằm ở màu.
        ax.text(x, y - 0.32, name, ha="center", va="top",
                fontsize=8.5, color=INK_SECONDARY, zorder=4)

    ax.set_aspect("equal")
    ax.margins(0.22, 0.20)
    ax.set_xticks([])
    ax.set_yticks([])

    used = sol.get("colors_used")
    bad = sol.get("violations", 0)
    top = _title(
        fig,
        f"Bài 1.1 — Tô màu đồ thị: nghiệm dùng {used} màu, {bad} cạnh vi phạm",
        f"{len(vertices)} đỉnh · {len(sol['edges'])} cạnh · {_provenance(rec)}. "
        "Bài CSP thuần nên ba chiều đều tìm được nghiệm khả thi, không nhất "
        "thiết trùng phép tô.",
    )
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


# --------------------------------------------------------------------------- #
# Bài 1.2 — N-Queens
# --------------------------------------------------------------------------- #

def _draw_nqueens(sol: dict, rec):
    n = int(sol["n"])
    cols = list(sol["queens"])

    fig, ax = _new_figure((5.8, 5.8))

    for r in range(n):
        for c in range(n):
            ax.add_patch(mpatches.Rectangle(
                (c, r), 1, 1,
                facecolor=CELL_EMPTY if (r + c) % 2 == 0 else CELL_DARK,
                edgecolor="none", zorder=1))

    glyph_size = max(9.0, 220.0 / n)
    for r, c in enumerate(cols):
        ax.text(c + 0.5, r + 0.5, "♛", ha="center", va="center",
                fontsize=glyph_size, color=DIMENSION_COLORS[VIZ_DIMENSION],
                zorder=3)

    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)                      # hàng 0 ở TRÊN, khớp bàn cờ model in ra
    ax.set_aspect("equal")
    ax.set_xticks([i + 0.5 for i in range(n)], [str(i) for i in range(n)])
    ax.set_yticks([i + 0.5 for i in range(n)], [str(i) for i in range(n)])
    ax.tick_params(length=0, colors=INK_MUTED, labelsize=9)
    ax.set_xlabel("cột", fontsize=9, color=INK_SECONDARY)
    ax.set_ylabel("hàng", fontsize=9, color=INK_SECONDARY)

    top = _title(
        fig,
        f"Bài 1.2 — N-Queens: một nghiệm {n} hậu trên bàn cờ {n}×{n}",
        f"Không hai hậu nào cùng hàng, cùng cột hay cùng đường chéo · "
        f"{_provenance(rec)}. Bài CSP thuần nên ba chiều đều tìm được nghiệm, "
        "không nhất thiết trùng nhau.",
    )
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


# --------------------------------------------------------------------------- #
# Bài 2.1 — job-shop
# --------------------------------------------------------------------------- #

def _draw_jobshop(sol: dict, rec):
    tasks = sol["tasks"]
    nb_machines = int(sol["nb_machines"])
    nb_jobs = int(sol["nb_jobs"])
    makespan = sol.get("makespan") or max(t["start"] + t["duration"] for t in tasks)

    fig, ax = _new_figure((11.0, 4.6))

    # Ngưỡng để nhãn nằm LỌT trong thanh. Thanh hẹp thì bỏ nhãn chứ không cắt
    # chữ — chú giải và trục vẫn nói đủ.
    label_min = makespan * 0.055

    for t in tasks:
        fill = SERIES[t["job"] % len(SERIES)]
        ax.barh(t["machine"], t["duration"], left=t["start"], height=0.55,
                color=fill, edgecolor=SURFACE, linewidth=1.5, zorder=3)
        if t["duration"] >= label_min:
            ax.text(t["start"] + t["duration"] / 2, t["machine"], f"J{t['job']}",
                    ha="center", va="center", fontsize=8,
                    color=_ink_on(fill), zorder=4)

    accent = DIMENSION_COLORS[VIZ_DIMENSION]
    ax.axvline(makespan, color=accent, linewidth=1.5, zorder=5)
    ax.text(makespan, -0.95, f"makespan = {makespan}", ha="right", va="bottom",
            fontsize=9, color=accent)

    ax.set_ylim(nb_machines - 0.5, -1.0)   # máy 0 ở trên cùng
    ax.set_xlim(0, makespan * 1.04)
    ax.set_yticks(range(nb_machines), [f"máy {m}" for m in range(nb_machines)])
    ax.tick_params(length=0, colors=INK_MUTED, labelsize=9)
    ax.set_xlabel("thời gian", fontsize=9, color=INK_SECONDARY)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    top = _title(
        fig,
        f"Bài 2.1 — Job-shop {sol.get('instance', '')}: lịch tối ưu, "
        f"makespan = {makespan}",
        f"{nb_jobs} job × {nb_machines} máy, màu theo job · {_provenance(rec)}. "
        "Cả ba chiều cùng ra giá trị tối ưu này (xem kiểm chứng chéo ở trên).",
    )
    # Bố cục đặt tay chứ KHÔNG dùng tight_layout: chú giải neo theo toạ độ trục
    # (`bbox_to_anchor`) cộng với tight_layout tạo một vòng lặp phản hồi —
    # tight_layout thu nhỏ trục để lấy chỗ, trục nhỏ đi thì chú giải neo ở
    # `-0.14` lại trồi lên đè vào nhãn trục.
    fig.subplots_adjust(left=0.065, right=0.985, top=top, bottom=0.20)
    fig.legend(
        handles=[mpatches.Patch(facecolor=SERIES[j % len(SERIES)], label=f"job {j}")
                 for j in range(nb_jobs)],
        loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=nb_jobs,
        frameon=False, fontsize=9, labelcolor=INK_SECONDARY, handlelength=1.4,
    )
    return fig


# --------------------------------------------------------------------------- #
# Bài 2.2 — xếp ca nhân sự
# --------------------------------------------------------------------------- #

def _draw_employee(sol: dict, rec):
    employees = list(sol["employees"])
    days = list(sol["days"])
    shifts = list(sol["shifts"])
    nb_cols = len(days) * len(shifts)

    fig, ax = _new_figure((11.0, 3.9))

    # Nền lưới: mọi ô (nhân viên × ca) đều có mặt, ô trống nghĩa là không trực.
    for r in range(len(employees)):
        for c in range(nb_cols):
            ax.add_patch(mpatches.Rectangle(
                (c + 0.06, r + 0.10), 0.88, 0.80,
                facecolor=CELL_EMPTY, edgecolor="none", zorder=1))

    granted = 0
    for a in sol["assignments"]:
        c = a["day"] * len(shifts) + a["shift"]
        r = a["employee"]
        wish = bool(a["requested"])
        granted += wish
        fill = STATUS_GOOD if wish else SERIES[0]
        ax.add_patch(mpatches.Rectangle(
            (c + 0.06, r + 0.10), 0.88, 0.80,
            facecolor=fill, edgecolor="none", zorder=2))
        if wish:
            # Dấu ✓ để “đúng nguyện vọng” không chỉ nằm ở màu.
            ax.text(c + 0.5, r + 0.5, "✓", ha="center", va="center",
                    fontsize=11, color=_ink_on(fill), zorder=3)

    # Vạch ngăn giữa các ngày.
    for d in range(1, len(days)):
        ax.axvline(d * len(shifts), color=AXIS, linewidth=1, zorder=4)

    # Tên ngày, đặt trên đầu mỗi cụm ba ca. Toạ độ y tính theo TỈ LỆ CHIỀU CAO
    # TRỤC (`get_xaxis_transform`) chứ không theo dữ liệu: đặt theo dữ liệu thì
    # khoảng hở đổi theo số nhân viên và theo chiều cao hình, đủ để nhãn ngày
    # trèo lên đè vào câu chú thích dưới tiêu đề.
    for d, day in enumerate(days):
        ax.text((d + 0.5) * len(shifts), 1.05, day,
                transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=9.5, color=INK_SECONDARY)

    ax.set_xlim(0, nb_cols)
    ax.set_ylim(len(employees), 0)
    ax.set_xticks([c + 0.5 for c in range(nb_cols)],
                  [s[0] for _ in days for s in shifts])
    ax.set_yticks([r + 0.5 for r in range(len(employees))], employees)
    ax.tick_params(length=0, colors=INK_MUTED, labelsize=9)
    ax.set_xlabel(
        "ca trong ngày: " + " · ".join(f"{s[0]} = {s}" for s in shifts),
        fontsize=9, color=INK_SECONDARY, labelpad=12,
    )

    total = sol.get("nb_requests")
    top = _title(
        fig,
        f"Bài 2.2 — Xếp ca nhân sự: {sol.get('granted', granted)}/{total} "
        "nguyện vọng được đáp ứng",
        f"{len(employees)} nhân viên × {len(days)} ngày × {len(shifts)} ca, "
        f"mỗi ca đúng một người · {_provenance(rec)}. "
        "Cả ba chiều cùng ra giá trị tối ưu này (xem kiểm chứng chéo ở trên).",
    )
    # Bố cục đặt tay, cùng lý do như bài 2.1 (xem `_draw_jobshop`).
    # Trừ thêm chỗ cho hàng tên ngày nằm ngoài trục.
    fig.subplots_adjust(left=0.045, right=0.99, top=top - 0.06, bottom=0.30)
    fig.legend(
        handles=[
            mpatches.Patch(facecolor=STATUS_GOOD, label="✓ trực đúng nguyện vọng"),
            mpatches.Patch(facecolor=SERIES[0], label="trực nhưng không xin ca này"),
            # Ô "nghỉ" gần như trùng màu nền, phải có viền mảnh mới thấy được ô
            # mẫu trong chú giải.
            mpatches.Patch(facecolor=CELL_EMPTY, edgecolor=AXIS, linewidth=0.8,
                           label="nghỉ"),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=3,
        frameon=False, fontsize=9, labelcolor=INK_SECONDARY, handlelength=1.4,
    )
    return fig


# --------------------------------------------------------------------------- #
# Bài 3.1 — lịch thi đấu vòng tròn hai lượt
# --------------------------------------------------------------------------- #

#: Sân nhà / sân khách — hai màu lấy từ hai slot đầu của `SERIES`, đã chạy qua
#: validator của skill `dataviz` ở đúng cặp này (nền #fcfcfb, chế độ sáng):
#: ΔE protan 24.7 · tritan 32.7 · thị lực thường 33.6, tương phản nền ≥ 3:1.
#: Màu vẫn không đứng một mình: mỗi ô còn mang chữ "N" (nhà) hoặc "K" (khách).
HOME_FILL = SERIES[0]
AWAY_FILL = SERIES[1]


def _draw_sports(sol: dict, rec):
    """Hai cách nhìn CÙNG một lịch, cạnh nhau.

    Lưới tuần × trận (trái) trả lời "tuần này ai đá với ai, ở sân của ai". Nhưng
    BREAK — thứ đang được tối thiểu hoá — không nhìn ra được ở đó: nó là quan hệ
    giữa hai tuần LIÊN TIẾP CỦA CÙNG MỘT ĐỘI, mà lịch theo tuần thì mỗi đội mỗi
    tuần lại nằm ở một ô khác. Vì vậy có bảng phải: mỗi đội một hàng, các tuần
    trải ngang, và mỗi break là một vạch đậm ở đúng ranh giới hai tuần sinh ra
    nó. Đếm vạch = đọc được hàm mục tiêu.
    """
    n = int(sol["n"])
    nb_weeks = int(sol["nb_weeks"])
    nb_slots = int(sol["nb_games_per_week"])
    teams = [int(t) for t in sol["teams"]]
    games = sol["games"]
    team_weeks = sol["team_weeks"]
    breaks_of = {int(b["team"]): int(b["breaks"]) for b in sol.get("team_breaks", [])}
    total = sol.get("total_breaks")
    if total is None:
        total = sum(1 for tw in team_weeks if tw["is_break"])

    fig = plt.figure(figsize=(12.2, 5.9))
    fig.patch.set_facecolor(SURFACE)
    gs = fig.add_gridspec(1, 2, width_ratios=(1.0, 2.5), wspace=0.16)
    ax_week = _bare_axes(fig.add_subplot(gs[0]))
    ax_team = _bare_axes(fig.add_subplot(gs[1]))
    accent = DIMENSION_COLORS[VIZ_DIMENSION]

    # ---- trái: lưới tuần × trận ---------------------------------------------
    # Mỗi ô là một trận, cắt đôi: NỬA TRÁI là đội nhà, NỬA PHẢI là đội khách.
    # Khe hở 0.06 giữa hai nửa là khe nền, không phải đường viền.
    for g in games:
        row, col = int(g["week"]) - 1, int(g["slot"])
        for fill, team, dx in ((HOME_FILL, int(g["home"]), 0.05),
                               (AWAY_FILL, int(g["away"]), 0.53)):
            ax_week.add_patch(mpatches.Rectangle(
                (col + dx, row + 0.12), 0.42, 0.76,
                facecolor=fill, edgecolor="none", zorder=2))
            ax_week.text(col + dx + 0.21, row + 0.5, str(team),
                         ha="center", va="center", fontsize=9.5,
                         color=_ink_on(fill), zorder=3)

    ax_week.set_xlim(0, nb_slots)
    ax_week.set_ylim(nb_weeks, 0)
    ax_week.set_xticks([c + 0.5 for c in range(nb_slots)],
                       [f"trận {c + 1}" for c in range(nb_slots)])
    ax_week.set_yticks([r + 0.5 for r in range(nb_weeks)],
                       [f"tuần {r + 1}" for r in range(nb_weeks)])
    ax_week.tick_params(length=0, colors=INK_MUTED, labelsize=8.5)
    ax_week.set_title("Lưới tuần × trận — ai gặp ai, trên sân của ai",
                      loc="left", fontsize=9.5, color=INK_SECONDARY, pad=8)

    # ---- phải: lịch riêng từng đội, nơi break lộ ra --------------------------
    row_of = {t: i for i, t in enumerate(teams)}
    for tw in team_weeks:
        r, c = row_of[int(tw["team"])], int(tw["week"]) - 1
        at_home = bool(tw["at_home"])
        fill = HOME_FILL if at_home else AWAY_FILL
        ax_team.add_patch(mpatches.Rectangle(
            (c + 0.04, r + 0.12), 0.92, 0.76,
            facecolor=fill, edgecolor="none", zorder=2))
        ax_team.text(c + 0.5, r + 0.5,
                     f"{'N' if at_home else 'K'}{tw['opponent']}",
                     ha="center", va="center", fontsize=9,
                     color=_ink_on(fill), zorder=3)
        if tw["is_break"]:
            # Vạch đậm ĐẶT ĐÚNG RANH GIỚI hai tuần liên tiếp cùng sân — break là
            # quan hệ giữa hai ô, nên dấu của nó phải nằm giữa hai ô đó chứ không
            # nằm trong một ô.
            ax_team.plot([c, c], [r + 0.06, r + 0.94], color=INK, linewidth=3.0,
                         solid_capstyle="butt", zorder=4)

    # Cột đếm break của từng đội, nằm ngoài lưới. Tổng cột này = hàm mục tiêu.
    for t in teams:
        ax_team.text(nb_weeks + 0.55, row_of[t] + 0.5, str(breaks_of.get(t, "")),
                     ha="center", va="center", fontsize=9.5, color=INK)
    ax_team.text(nb_weeks + 0.55, 1.01, "break",
                 transform=ax_team.get_xaxis_transform(),
                 ha="center", va="bottom", fontsize=8.5, color=INK_SECONDARY)
    ax_team.text(nb_weeks + 0.55, -0.02, f"tổng {total}",
                 transform=ax_team.get_xaxis_transform(),
                 ha="center", va="bottom", fontsize=9, color=accent)

    ax_team.set_xlim(0, nb_weeks + 1.1)
    ax_team.set_ylim(n, 0)
    ax_team.set_xticks([c + 0.5 for c in range(nb_weeks)],
                       [str(c + 1) for c in range(nb_weeks)])
    ax_team.set_yticks([r + 0.5 for r in range(n)], [f"đội {t}" for t in teams])
    ax_team.tick_params(length=0, colors=INK_MUTED, labelsize=9)
    ax_team.set_xlabel("tuần", fontsize=9, color=INK_SECONDARY)
    ax_team.set_title("Lịch riêng từng đội — mỗi vạch đậm là một break",
                      loc="left", fontsize=9.5, color=INK_SECONDARY, pad=8)

    top = _title(
        fig,
        f"Bài 3.1 — Lịch thi đấu vòng tròn hai lượt: tổng số break = {total} (tối ưu)",
        f"{n} đội × {nb_weeks} tuần, biến thể A (sports.mod — có sân nhà/khách) · "
        f"{_provenance(rec)}. Break = hai tuần liên tiếp cùng sân; ba bản giải "
        "biến thể A (`opl`, `ortools` và bản phụ trợ `docplexcp_portA`) cùng ra "
        f"{total}. Chiều `docplexcp` ở bảng trên giải BIẾN THỂ B (lịch NFL, không "
        "có sân nhà/khách) nên không có gì để vẽ ở đây.",
    )
    # Bố cục đặt tay, cùng lý do như bài 2.1 (xem `_draw_jobshop`).
    fig.subplots_adjust(left=0.055, right=0.985, top=top - 0.03, bottom=0.155)
    fig.legend(
        handles=[
            mpatches.Patch(facecolor=HOME_FILL,
                           label="N = đá sân nhà (nửa trái mỗi trận)"),
            mpatches.Patch(facecolor=AWAY_FILL,
                           label="K = đá sân khách (nửa phải mỗi trận)"),
            mlines.Line2D([], [], color=INK, linewidth=3.0,
                          label="break — hai tuần liên tiếp cùng sân"),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=3,
        frameon=False, fontsize=9, labelcolor=INK_SECONDARY, handlelength=1.4,
    )
    return fig


# --------------------------------------------------------------------------- #
# Bài 3.2 — thời khoá biểu
# --------------------------------------------------------------------------- #

def _draw_timetable(sol: dict, rec):
    """Ba lưới (ngày × tiết), mỗi lớp một lưới.

    Ô KHÔNG tô màu theo môn: bài này có 8 môn, nhiều hơn bảng 6 màu đã kiểm định,
    mà sinh thêm hai màu nữa thì cặp kề rơi khỏi ngưỡng phân biệt dưới mù màu.
    Môn vì thế được nhận diện bằng CHỮ; màu chỉ tách ba trạng thái của một ô, và
    dành riêng một màu nhấn cho ô kết thúc muộn nhất — chính là makespan.
    """
    day_duration = int(sol["day_duration"])
    nb_days = int(sol["nb_days"])
    classes = list(sol["classes"])
    sessions = sol["sessions"]
    makespan = int(sol.get("makespan")
                   or max(s["start"] + s["duration"] for s in sessions))
    accent = DIMENSION_COLORS[VIZ_DIMENSION]

    busy_of = {}
    for b in sol.get("class_busy", []):
        busy_of.setdefault(b["class"], set()).add(int(b["time"]))

    fig, axes = plt.subplots(len(classes), 1, figsize=(11.4, 2.55 * len(classes) + 1.5))
    fig.patch.set_facecolor(SURFACE)
    axes = list(axes) if len(classes) > 1 else [axes]

    for ax, cls in zip(axes, classes):
        _bare_axes(ax)

        for t in range(nb_days * day_duration):
            d, s = divmod(t, day_duration)
            busy = t in busy_of.get(cls, ())
            ax.add_patch(mpatches.Rectangle(
                (d + 0.04, s + 0.06), 0.92, 0.88,
                facecolor=CELL_DARK if busy else CELL_EMPTY,
                edgecolor="none", zorder=1))
            if busy:
                ax.text(d + 0.5, s + 0.5, "lớp bận", ha="center", va="center",
                        fontsize=6.5, color=INK_SECONDARY, zorder=2)

        for ses in sessions:
            if ses["class"] != cls:
                continue
            d, s = divmod(int(ses["start"]), day_duration)
            dur = int(ses["duration"])
            last = int(ses["start"]) + dur == makespan
            fill = accent if last else CELL_BOOKED
            ax.add_patch(mpatches.Rectangle(
                (d + 0.04, s + 0.06), 0.92, dur - 0.12,
                facecolor=fill, edgecolor="none", zorder=2))
            cy = s + dur / 2
            # Hai dòng chữ neo quanh tâm ô (va="bottom"/"top"): khoảng cách giữa
            # chúng khi đó do CỠ CHỮ quyết định, không do chiều cao ô — nên ô một
            # tiết và ô hai tiết dùng chung một công thức mà không dòng nào chồng.
            ax.text(d + 0.5, cy - 0.04, ses["discipline"], ha="center", va="bottom",
                    fontsize=7.5, color=_ink_on(fill), zorder=3)
            ax.text(d + 0.5, cy + 0.06, f"{ses['teacher']} · {ses['room']}",
                    ha="center", va="top", fontsize=6,
                    color=_ink_on(fill) if last else INK_SECONDARY, zorder=3)

        # Ranh giới sáng / chiều — ràng buộc "một buổi học không vắt qua trưa"
        # chỉ đọc được khi thấy vạch này.
        ax.axhline(day_duration / 2, color=AXIS, linewidth=1, zorder=4)

        ax.set_xlim(0, nb_days)
        ax.set_ylim(day_duration, 0)
        ax.set_xticks([d + 0.5 for d in range(nb_days)],
                      [f"ngày {d + 1}" for d in range(nb_days)])
        ax.set_yticks([s + 0.5 for s in range(day_duration)],
                      [f"tiết {s + 1}" for s in range(day_duration)])
        ax.tick_params(length=0, colors=INK_MUTED, labelsize=8.5)
        ax.set_title(f"Lớp {cls}", loc="left", fontsize=10.5, color=INK, pad=6)

    end_day, end_slot = divmod(makespan - 1, day_duration)
    top = _title(
        fig,
        f"Bài 3.2 — Thời khoá biểu: makespan = {makespan} tiết "
        f"(buổi cuối cùng học hết tiết {end_slot + 1} ngày {end_day + 1})",
        f"{len(classes)} lớp × {nb_days} ngày × {day_duration} tiết, "
        f"{len(sessions)} buổi học · {_provenance(rec)}. Cả ba chiều cùng ra "
        "makespan này (xem kiểm chứng chéo ở trên). Vạch ngang giữa mỗi lưới là "
        "ranh giới sáng/chiều.",
    )
    # Bố cục đặt tay, cùng lý do như bài 2.1 (xem `_draw_jobshop`).
    fig.subplots_adjust(left=0.052, right=0.99, top=top, bottom=0.075, hspace=0.42)
    fig.legend(
        handles=[
            mpatches.Patch(facecolor=CELL_BOOKED,
                           label="buổi học đã xếp (môn · giáo viên · phòng)"),
            mpatches.Patch(facecolor=accent,
                           label=f"buổi kết thúc muộn nhất = makespan ({makespan})"),
            mpatches.Patch(facecolor=CELL_DARK, label="lớp bận, không được xếp (RB8)"),
            mpatches.Patch(facecolor=CELL_EMPTY, edgecolor=AXIS, linewidth=0.8,
                           label="tiết trống"),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4,
        frameon=False, fontsize=9, labelcolor=INK_SECONDARY, handlelength=1.4,
    )
    return fig


# --------------------------------------------------------------------------- #
# Cửa vào
# --------------------------------------------------------------------------- #

#: Tiền tố tên bài -> hàm vẽ. Tra theo tiền tố ("2.1") chứ không theo tên đầy đủ
#: để đổi hậu tố thư mục không làm mất hình.
_DRAWERS = {
    "1.1": _draw_graph_coloring,
    "1.2": _draw_nqueens,
    "2.1": _draw_jobshop,
    "2.2": _draw_employee,
    "3.1": _draw_sports,
    "3.2": _draw_timetable,
}


def _viz_record(problem: str):
    """Bản ghi của chiều dựng hình trong kết quả ĐÃ CHẠY của `problem`.

    Bản phụ trợ (`companion`) dùng chung tên chiều nhưng giải biến thể khác, nên
    lọc thêm theo nhãn: chỉ lấy đúng bản ghi của chiều chính.
    """
    for rec in nbutil.runs(problem):
        if rec.dimension == VIZ_DIMENSION and (rec.label or rec.dimension) == VIZ_DIMENSION:
            return rec
    return None


def show_solution(problem: str):
    """Vẽ nghiệm của một bài, lấy từ kết quả chạy đã có trong phiên.

    Không bao giờ ném exception: thiếu chiều, thiếu nghiệm hay thiếu dòng
    `SOLUTION` đều chỉ in một dòng nói rõ thiếu gì rồi trả về `None`.
    """
    key = problem.split("_")[0]
    draw = _DRAWERS.get(key)
    if draw is None:
        print(f"ℹ️  Chưa có hình cho bài {problem} — "
              f"nbviz.py mới vẽ được: {', '.join(sorted(_DRAWERS))}.")
        return None

    rec = _viz_record(problem)
    if rec is None:
        print(f"ℹ️  Không vẽ được nghiệm bài {problem}: phiên này không có bản ghi "
              f"nào của chiều `{VIZ_DIMENSION}`\n"
              f"    (bị `{nbutil.DIMENSIONS_ENV}` lọc bỏ, hoặc manifest.json không "
              "khai chiều đó). Đây không phải lỗi mô hình.")
        return None
    if not rec.ok:
        print(f"ℹ️  Không vẽ được nghiệm bài {problem}: chiều `{VIZ_DIMENSION}` "
              f"kết thúc với status = {rec.status}, chưa có nghiệm để vẽ.")
        return None
    if not rec.solution:
        print(f"ℹ️  Không vẽ được nghiệm bài {problem}: chiều `{VIZ_DIMENSION}` "
              "chạy xong nhưng không in dòng `SOLUTION`\n"
              f"    (xem giao kèo ở đầu tools/runner.py). Số liệu ở bảng trên "
              "vẫn đầy đủ.")
        return None

    try:
        fig = draw(rec.solution, rec)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"ℹ️  Không vẽ được nghiệm bài {problem}: dòng `SOLUTION` thiếu hoặc "
              f"sai kiểu dữ liệu ({exc.__class__.__name__}: {exc}).")
        return None
    return _emit(fig)


#: Số dòng tối đa in ra cho một bảng nghiệm. Bảng dài nhất hiện nay là `sessions`
#: của bài 3.2 với 106 dòng, nên ngưỡng phải nằm TRÊN con số đó: bảng này là tập
#: nghiệm, cắt bớt là in ra một nghiệm không đầy đủ. Ngưỡng chỉ còn là chốt chặn
#: cho bộ dữ liệu lớn hơn hẳn, và khi chạm thì nói rõ đã cắt bao nhiêu dòng.
_MAX_SOLUTION_ROWS = 150


def _fmt_cell(v) -> str:
    if isinstance(v, bool):
        return "✓" if v else "·"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt_cell(x) for x in v)
    return str(v)


def _rows_table(name: str, rows: list[dict]) -> str:
    """Bảng markdown cho một danh sách bản ghi (task, ca trực, phiên học...)."""
    cols: list[str] = []
    for row in rows:
        for k in row:
            if k not in cols:
                cols.append(k)
    head = f"| {' | '.join(cols)} |\n|{'|'.join(['---'] * len(cols))}|"
    body = "\n".join(
        "| " + " | ".join(_fmt_cell(row.get(c, "")) for c in cols) + " |"
        for row in rows[:_MAX_SOLUTION_ROWS]
    )
    more = (f"\n\n*(còn {len(rows) - _MAX_SOLUTION_ROWS} dòng nữa, đã cắt bớt)*"
            if len(rows) > _MAX_SOLUTION_ROWS else "")
    return f"**`{name}`** — {len(rows)} dòng\n\n{head}\n{body}{more}"


def _render_solution(sol: dict) -> str:
    """Dựng markdown cho một cấu trúc `SOLUTION` bất kỳ.

    CỐ Ý viết tổng quát thay vì một hàm cho mỗi bài: đây là NGHIỆM THÔ, đúng
    những khoá mà model đã in ra. Bài nào cần cách trình bày riêng thì đã có
    hình vẽ ở `_DRAWERS` lo phần đó.
    """
    scalars: list[tuple[str, str]] = []
    blocks: list[str] = []
    for key, value in sol.items():
        if key == "problem":       # trùng với tiêu đề ngay phía trên
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            blocks.append(_rows_table(key, value))
        elif isinstance(value, dict):
            blocks.append(_rows_table(key, [{"khoá": k, "giá trị": _fmt_cell(v)}
                                            for k, v in value.items()]))
        elif isinstance(value, list):
            scalars.append((key, "`" + "`, `".join(_fmt_cell(v) for v in value) + "`"))
        else:
            scalars.append((key, f"`{_fmt_cell(value)}`"))

    parts = []
    if scalars:
        parts.append("| Khoá | Giá trị |\n|---|---|\n" + "\n".join(
            f"| `{k}` | {v} |" for k, v in scalars))
    parts.extend(blocks)
    return "\n\n".join(parts)


def show_solution_data(problem: str):
    """In TẬP NGHIỆM của một bài dưới dạng bảng — phần chữ đi kèm hình vẽ.

    Hình cho thấy nghiệm *trông* thế nào; bảng này cho thấy nghiệm *là* gì, đúng
    từng giá trị biến mà model in ra ở dòng `SOLUTION`. Cùng một bản ghi với
    `show_solution()` nên hai thứ luôn nói về cùng một nghiệm.

    Cùng chính sách với `show_solution()`: thiếu gì thì in một dòng nói rõ thiếu
    gì rồi trả về `None`, không bao giờ ném exception.
    """
    rec = _viz_record(problem)
    if rec is None:
        print(f"ℹ️  Không in được tập nghiệm bài {problem}: phiên này không có bản "
              f"ghi nào của chiều `{VIZ_DIMENSION}`\n"
              f"    (bị `{nbutil.DIMENSIONS_ENV}` lọc bỏ, hoặc manifest.json không "
              "khai chiều đó). Đây không phải lỗi mô hình.")
        return None
    if not rec.ok:
        print(f"ℹ️  Không in được tập nghiệm bài {problem}: chiều `{VIZ_DIMENSION}` "
              f"kết thúc với status = {rec.status}.")
        return None
    if not rec.solution:
        print(f"ℹ️  Không in được tập nghiệm bài {problem}: chiều `{VIZ_DIMENSION}` "
              "chạy xong nhưng không in dòng `SOLUTION`\n"
              f"    (xem giao kèo ở đầu tools/runner.py).")
        return None

    obj = "" if rec.objective is None else f" · objective = **{_fmt_cell(rec.objective)}**"
    header = (f"**Tập nghiệm — {problem}, chiều `{VIZ_DIMENSION}` "
              f"({nbutil.ENGINE[VIZ_DIMENSION]})** · status = `{rec.status}`{obj}")
    try:
        body = _render_solution(rec.solution)
    except (AttributeError, TypeError, ValueError) as exc:
        print(f"ℹ️  Không in được tập nghiệm bài {problem}: dòng `SOLUTION` sai kiểu "
              f"dữ liệu ({exc.__class__.__name__}: {exc}).")
        return None
    return nbutil._md(f"{header}\n\n{body}")


__all__ = ["show_solution", "show_solution_data", "DIMENSION_COLORS", "SERIES",
           "VIZ_DIMENSION"]
