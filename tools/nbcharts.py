"""Biểu đồ cho báo cáo — ba hình cho ba luận điểm, vẽ bằng matplotlib.

Báo cáo này so sánh trên hai trục, và cả hai trục đều là phép so **tỉ lệ** chứ
không phải phép so hiệu: số nhánh trải từ hàng chục tới hàng triệu, thời gian giải
trải ba bậc độ lớn. Vì vậy mọi hình ở đây dùng **trục log** cho hai đại lượng đó,
và nói rõ điều đó ngay trên hình — trục log không tự khai báo, người đọc không để ý
thì đọc sai độ lớn.

Ba hàm công khai::

    bench_chart()            # bài 3.2: 3 chiều × 4 cấu hình, thời gian và số nhánh
    axis_charts(lang, eng)   # hai trục so sánh, dữ liệu từ nbutil.axis_tables()
    community_limit_chart()  # trần 2^1000 của CPLEX Community

Kèm `bench_table()` — bảng trung vị của `results/bench.csv`, chịu được trường hợp
file chưa tồn tại (nó do `make bench` sinh ra, không có trong kho).

Dùng trong notebook::

    import sys; sys.path.insert(0, "../tools")
    from nbcharts import *

    lang, eng = axis_tables()
    axis_charts(lang, eng)      # KHÔNG chạy lại solver — dùng lại bảng đã có

Hai điều cấm được cài thẳng vào code chứ không chỉ ghi trong tài liệu:

* **Không vẽ `fails` của CP Optimizer cạnh `conflicts` của CP-SAT.** Hai cột đó
  cùng tên trong CSV nhưng đếm hai thứ khác nhau — nhánh chết so với mệnh đề học
  được. Đặt cạnh nhau trên một trục là mời người đọc so hai thứ không so được, nên
  `bench_chart()` cố ý chỉ vẽ thời gian và số nhánh, và ghi lý do lên hình.
* **Không coi ô thiếu số liệu là 0.** `nbutil.axis_tables()` trả `None` cho chiều
  không chạy được trên máy đo. `None` vẽ thành cột dài 0 là bịa ra một kết luận
  ("chiều đó duyệt 0 nhánh"), nên hàng thiếu số liệu bị **bỏ qua và ghi chú**.
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from runner import ROOT  # noqa: E402

BENCH_CSV = ROOT / "results" / "bench.csv"

# --------------------------------------------------------------------------- #
# Bảng màu — dùng chung cho TOÀN báo cáo
#
# Ba chiều giữ đúng một màu ở mọi hình, mọi notebook: màu đi theo *chiều*, không đi
# theo thứ hạng trong hình. Người đọc học "OPL màu xanh" ở hình đầu thì đến hình
# cuối vẫn đúng.
#
# Bộ ba màu hiện dùng ĐÃ QUA kiểm định của skill `dataviz` trên nền sáng (#ffffff
# của file này và #fcfcfb của `nbviz.py`), cả `--pairs adjacent` lẫn `--pairs all`:
# dải sáng PASS · sàn chroma PASS · tách cặp ΔE 9.7 ở protan/deutan và 14.5 ở tritan
# (ngưỡng 8) · thị lực thường ΔE 18.6 (sàn 15) · tương phản nền ≥ 3:1. Bộ cũ
# (#0b5cad/#6a3d9a/#c1440e) TRƯỢT: cặp `opl` ↔ `docplexcp` chỉ ΔE 3.4 dưới mắt
# deutan và 12.4 với mắt thường — người mù màu đỏ-lục không tách nổi đúng hai chiều
# tạo nên trục NGÔN NGỮ, phép so trung tâm của báo cáo.
#
# **Kênh nhận dạng thứ hai vẫn giữ nguyên** dù màu đã đạt chuẩn: hình dạng điểm
# khác nhau (`o`/`s`/`^`), nhãn tên chiều ngay cạnh cột, giá trị in thẳng lên đầu
# mỗi cột. Hai lý do: báo cáo học thuật hay được in ĐEN TRẮNG, và lúc đó màu — dù
# tách tốt đến đâu — không còn kênh nào; và các hình của `nbviz.py` cũng dựa vào
# chữ chứ không dựa vào màu, nên bỏ chữ ở đây là làm hai nửa báo cáo đọc khác nhau.
# Màu tốt hơn là thêm một lớp an toàn, không phải cái cớ để bỏ lớp đang có.
# --------------------------------------------------------------------------- #

#: Màu của ba chiều — hằng số dùng chung, giữ khớp với `nbviz.DIMENSION_COLORS`.
#: Đổi ở đây thì đổi luôn bên đó, và chạy lại validator chứ đừng ước lượng bằng mắt.
DIMENSION_COLOR = {
    "opl": "#0072b2",
    "docplexcp": "#c47ca8",
    "ortools": "#b85000",
}

#: Tên ngắn để ghi cạnh cột/điểm.
DIMENSION_SHORT = {
    "opl": "OPL",
    "docplexcp": "DOcplex.cp",
    "ortools": "OR-Tools",
}

#: Tên đầy đủ cho chú giải — nhắc luôn engine, vì đó mới là biến số của phép so.
DIMENSION_LABEL = {
    "opl": "OPL → CP Optimizer",
    "docplexcp": "DOcplex.cp → CP Optimizer",
    "ortools": "OR-Tools → CP-SAT",
}

#: Kênh nhận dạng thứ hai, không phụ thuộc màu.
DIMENSION_MARKER = {"opl": "o", "docplexcp": "s", "ortools": "^"}

#: Màu trạng thái — chỉ dùng cho hình trần giấy phép, KHÔNG bao giờ dùng cho chiều.
STATUS_OK = "#0a7d5f"        # dưới trần, engine chạy
STATUS_BLOCKED = "#b3261e"   # vượt trần, FATAL[ENGINE_001]
STATUS_UNTESTED = "#6f6f6a"  # cách mã hoá bị loại bỏ, chưa từng chạy

INK = "#1a1a1a"
INK_MUTED = "#5a5a56"
GRID = "#e2e2dd"
BAND = "#f5f5f2"
SURFACE = "#ffffff"

_BAR_H = 0.62

__all__ = [
    "bench_chart", "bench_table", "axis_charts", "community_limit_chart",
    "DIMENSION_COLOR", "DIMENSION_LABEL", "DIMENSION_SHORT", "BENCH_CSV",
    "COMMUNITY_LOG2_CEILING",
]


# --------------------------------------------------------------------------- #
# Nền chung
# --------------------------------------------------------------------------- #

def _plt():
    """`pyplot` với vài mặc định của báo cáo.

    Không đặt `font.family`: font mặc định của matplotlib (DejaVu Sans) có đủ dấu
    tiếng Việt, đổi sang font khác là rước rủi ro thiếu chữ.
    """
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_MUTED,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 11,
        "legend.fontsize": 9,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 110,
    })
    return plt


def _tidy(ax, xgrid: bool = True):
    """Bỏ khung, để lại lưới dọc mảnh và nét liền — lưới phải lùi ra sau dữ liệu."""
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=0.8, linestyle="-")
    ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _num(v):
    """Giá trị số dùng được, hoặc `None`.

    Bắt cả `None` lẫn `NaN`: `nbutil.frame()` dựng DataFrame, và một cột số có ô
    `None` bị pandas đổi thành `NaN`. Cả hai đều nghĩa là CHƯA ĐO ĐƯỢC, và không
    cái nào được phép rơi vào một phép tính rồi hiện ra như số 0.
    """
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _rows(table) -> list[dict]:
    """Danh sách dict từ DataFrame (hoặc từ chính list dict khi thiếu pandas)."""
    if hasattr(table, "to_dict"):
        return table.to_dict("records")
    return list(table)


def _wrap(text: str, width: int = 96) -> str:
    """Xuống dòng cho ghi chú dưới hình — matplotlib không tự ngắt dòng.

    Hai ghi chú đặt cạnh nhau ở đáy hình sẽ chồng chữ lên nhau nếu để chạy dài.
    """
    import textwrap

    return "\n".join(textwrap.wrap(text, width=width))


def _int_text(v) -> str:
    """Số nguyên có dấu cách hàng nghìn, kiểu `216 066` — như PLAN.md."""
    return f"{v:,.0f}".replace(",", " ")


def _sec_text(v) -> str:
    return f"{v:.3g} s"


def _log_limits(values, pad_lo: float = 2.2, pad_hi: float = 3.4):
    """Biên trục log, chừa chỗ cho nhãn ở đầu cột/điểm.

    Trên trục log, cột ngắn nhất mà biên dưới đặt sát giá trị nhỏ nhất thì biến mất
    hẳn — nên biên dưới lùi thêm một quãng, tính bằng *tỉ lệ* chứ không bằng hiệu.
    """
    lo, hi = min(values), max(values)
    return lo / pad_lo, hi * pad_hi


def _finish(fig):
    """Trả hình về cho notebook, đúng MỘT lần.

    Backend inline tự vẽ mọi figure còn mở ở cuối ô, và giá trị trả về của ô cũng
    được vẽ — để nguyên thì mỗi hình hiện hai lần. Đóng figure khỏi sổ quản lý của
    pyplot rồi trả về đối tượng: `savefig` vẫn chạy trên figure đã đóng, nên hình
    chỉ hiện qua đúng đường trả về.
    """
    _plt().close(fig)
    return fig


# --------------------------------------------------------------------------- #
# 1. Benchmark bài 3.2
# --------------------------------------------------------------------------- #

#: Thứ tự cấu hình mong muốn; cấu hình lạ trong CSV vẫn được vẽ, xếp sau.
_CONFIG_ORDER = ["small", "small+avail", "large", "large+avail"]
_DIM_ORDER = ["opl", "docplexcp", "ortools"]

_MISSING_BENCH = """\
Chưa có {path} — bỏ qua phần benchmark.

File này KHÔNG nằm trong kho: nó là số liệu đo trên máy đang chạy, do `make bench`
sinh ra (4 cấu hình × 3 chiều × 5 lần chạy, khoảng 7 phút):

    make bench
    # tương đương: python3 tools/bench_timetable.py --csv results/bench.csv

Chạy xong thì chạy lại ô này. Mọi ô khác của notebook không phụ thuộc file này."""


def _bench_frame(path=None):
    """DataFrame của `results/bench.csv`, hoặc `None` kèm hướng dẫn khi thiếu file.

    Thiếu file là chuyện bình thường trên một bản clone mới, không phải lỗi: ném
    exception ở đây làm hỏng cả `nbconvert --execute`, tức là một máy chưa chạy
    benchmark thì không dựng nổi báo cáo.
    """
    p = pathlib.Path(path) if path else BENCH_CSV
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        try:
            shown = p.relative_to(ROOT)
        except ValueError:
            shown = p
        print(_MISSING_BENCH.format(path=shown))
        return None
    import pandas as pd

    return pd.read_csv(p)


def _bench_medians(path=None):
    """Trung vị mỗi ô (cấu hình × chiều), theo thứ tự đọc được của báo cáo."""
    b = _bench_frame(path)
    if b is None:
        return None
    b = b[b.ok]
    seen = list(dict.fromkeys(b["config"]))
    configs = [c for c in _CONFIG_ORDER if c in seen] + \
              [c for c in seen if c not in _CONFIG_ORDER]
    dims = [d for d in _DIM_ORDER if d in set(b["dimension"])] + \
           [d for d in dict.fromkeys(b["dimension"]) if d not in _DIM_ORDER]

    out = []
    for cfg in configs:
        for dim in dims:
            cell = b[(b["config"] == cfg) & (b["dimension"] == dim)]
            if cell.empty:
                continue
            out.append({
                "config": cfg,
                "dimension": dim,
                "engine": cell["engine"].iloc[0],
                "encoding": cell["encoding"].iloc[0],
                "reps": int(len(cell)),
                "objective": _num(cell["objective"].median()),
                "solve_time_s": _num(cell["solve_time_s"].median()),
                "branches": _num(cell["branches"].median()),
                "fails": _num(cell["fails"].median()),
            })
    return out


def bench_table(path=None):
    """Bảng trung vị của benchmark bài 3.2 — thay cho `pd.read_csv` trần.

    Trả `None` (sau khi in hướng dẫn) nếu chưa có `results/bench.csv`.
    """
    rows = _bench_medians(path)
    if rows is None:
        return None
    from nbutil import frame

    return frame([{
        "cấu hình": r["config"],
        "chiều": DIMENSION_SHORT.get(r["dimension"], r["dimension"]),
        "engine": r["engine"],
        "mã hoá": r["encoding"],
        "lần chạy": r["reps"],
        "mục tiêu": r["objective"],
        "thời gian giải (s)": r["solve_time_s"],
        "nhánh": r["branches"],
        "fails/conflicts": r["fails"],
    } for r in rows])


_BENCH_FOOTNOTE = (
    "Trục hoành thang log: khoảng cách bằng nhau nghĩa là TỈ LỆ bằng nhau, nên độ dài cột "
    "không tỉ lệ với giá trị — đọc theo con số ở đầu cột. "
    "Thời gian giải trải ba bậc độ lớn ({lo} … {hi}).\n"
    "Cột `fails` (CP Optimizer) và `conflicts` (CP-SAT) CỐ Ý không vẽ: hai đại lượng đếm hai "
    "thứ khác nhau — nhánh chết so với mệnh đề học được — chỉ so được trong cùng một engine."
)


def bench_chart(path=None, figsize=(11.6, 7.4)):
    """Bài 3.2: ba chiều trên bốn cấu hình dữ liệu, thời gian và số nhánh.

    Mỗi ô là **trung vị 5 lần chạy** (PLAN.md §2.4 — CP-SAT không tất định giữa các
    lần chạy nên một lần đo không dùng được).
    """
    rows = _bench_medians(path)
    if rows is None:
        return None
    plt = _plt()

    configs = list(dict.fromkeys(r["config"] for r in rows))

    # Vị trí hàng: mỗi cấu hình một khối, giữa hai khối chừa một quãng trống.
    ypos, blocks = {}, {}
    y = 0.0
    for cfg in configs:
        block = [r for r in rows if r["config"] == cfg]
        y0 = y
        for r in block:
            ypos[(cfg, r["dimension"])] = y
            y += 1.0
        blocks[cfg] = (y0, y - 1.0)
        y += 0.9

    fig, axes = plt.subplots(1, 2, figsize=figsize, sharey=True)
    panels = [
        (axes[0], "solve_time_s", "Thời gian giải — trung vị 5 lần chạy",
         "giây (thang log)", _sec_text),
        (axes[1], "branches", "Số nhánh duyệt — trung vị 5 lần chạy",
         "số nhánh (thang log)", _int_text),
    ]

    for ax, key, title, xlabel, fmt in panels:
        vals = [r[key] for r in rows if r[key]]
        lo, hi = _log_limits(vals, pad_lo=1.9, pad_hi=6.0 if key == "branches" else 5.0)
        ax.set_xscale("log")
        ax.set_xlim(lo, hi)

        for i, cfg in enumerate(configs):
            y0, y1 = blocks[cfg]
            if i % 2 == 0:
                ax.axhspan(y0 - 0.7, y1 + 0.7, color=BAND, zorder=0, lw=0)

        for r in rows:
            v = r[key]
            if not v:
                continue
            yy = ypos[(r["config"], r["dimension"])]
            ax.barh(yy, v - lo, left=lo, height=_BAR_H, zorder=3,
                    color=DIMENSION_COLOR.get(r["dimension"], INK_MUTED))
            ax.text(v * 1.10, yy, fmt(v), va="center", ha="left",
                    fontsize=8.5, color=INK_MUTED, zorder=4)

        ax.set_title(title, loc="left", pad=10)
        ax.set_xlabel(xlabel)
        _tidy(ax)

    ax0 = axes[0]
    # Biên đảo chiều (đáy > đỉnh) để hàng đầu tiên nằm trên cùng — đọc từ trên
    # xuống theo đúng thứ tự cấu hình. KHÔNG gọi thêm `invert_yaxis()`: gọi cả hai
    # là lật hai lần, tức không lật.
    ax0.set_ylim(y - 0.9 - 0.5, -0.8)
    ax0.set_yticks([ypos[(r["config"], r["dimension"])] for r in rows])
    ax0.set_yticklabels([DIMENSION_SHORT.get(r["dimension"], r["dimension"])
                         for r in rows])

    # Tên cấu hình thành một cột riêng bên trái cột nhãn chiều — căn phải cả hai
    # cột thì hai cột không bao giờ chồng lên nhau dù tên dài ngắn khác nhau.
    for cfg, (y0, y1) in blocks.items():
        ax0.text(-0.33, (y0 + y1) / 2, cfg, transform=ax0.get_yaxis_transform(),
                 ha="right", va="center", fontsize=10.5, fontweight="bold", color=INK)

    handles = [plt.Line2D([], [], marker="s", linestyle="none", markersize=9,
                          color=DIMENSION_COLOR[d], label=DIMENSION_LABEL[d])
               for d in _DIM_ORDER if any(r["dimension"] == d for r in rows)]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.245, 0.885),
               ncol=3, handletextpad=0.5, columnspacing=2.0)

    fig.suptitle("Bài 3.2 — thời khoá biểu: ba chiều trên bốn cấu hình dữ liệu",
                 x=0.015, y=0.985, ha="left", fontsize=13, fontweight="bold")

    times = [r["solve_time_s"] for r in rows if r["solve_time_s"]]
    fig.text(0.015, 0.005,
             _BENCH_FOOTNOTE.format(lo=_sec_text(min(times)), hi=_sec_text(max(times))),
             fontsize=8, color=INK_MUTED, va="bottom", ha="left", linespacing=1.5)

    fig.subplots_adjust(left=0.245, right=0.985, top=0.855, bottom=0.145, wspace=0.30)
    return _finish(fig)


# --------------------------------------------------------------------------- #
# 2. Hai trục so sánh
# --------------------------------------------------------------------------- #

#: Đặc tả một trục: hai cột số nhánh trong bảng của `nbutil.axis_tables()`, chiều
#: tương ứng, và HƯỚNG của tỉ lệ — mỗi bảng đã có sẵn một cột tỉ lệ với hướng riêng
#: (`tỉ lệ nhánh` = DOcplex.cp/OPL; `CP-SAT ít nhánh hơn` = CPO/CP-SAT), hình phải
#: ghi đúng hướng đó, không thì con số trên hình mâu thuẫn với con số trong bảng.
_LANG_SPEC = {
    "pairs": [("OPL nhánh", "opl"), ("DOcplex.cp nhánh", "docplexcp")],
    "ratio": "b/a",
    "ratio_of": "DOcplex.cp / OPL",
}
_ENG_SPEC = {
    "pairs": [("CPO nhánh", "docplexcp"), ("CP-SAT nhánh", "ortools")],
    "ratio": "a/b",
    "ratio_of": "CP Optimizer / CP-SAT — CP-SAT ít nhánh hơn bấy nhiêu lần",
}


def _ratio_text(r: float) -> str:
    """Tỉ lệ đọc được ở mọi bậc độ lớn.

    Một định dạng cứng `%.2f` biến tỉ lệ 0.0015 thành `×0.00` — đúng chỗ mà phép so
    đang mạnh nhất thì hình lại không nói được gì.
    """
    if r >= 100:
        return f"×{r:,.0f}".replace(",", " ")
    if r >= 10:
        return f"×{r:.1f}"
    return f"×{r:.2f}"


def _short_title(name: str, width: int = 26) -> str:
    """Tên bài rút gọn cho nhãn trục — bỏ phần trong ngoặc, cắt cho vừa."""
    head = str(name).split("(")[0].strip(" -–—")
    return head if len(head) <= width else head[: width - 1].rstrip() + "…"


def _pct_gap(a: float, b: float) -> float:
    """Chênh lệch theo phần trăm, luôn tính bên lớn so với bên nhỏ."""
    lo, hi = sorted((a, b))
    return (hi / lo - 1.0) * 100.0


def _dumbbell_panel(ax, rows, spec, title, plt):
    """Một trục so sánh: mỗi bài một đoạn nối hai chấm.

    Trên thang log, **độ dài đoạn nối chính là tỉ lệ** giữa hai chiều — đó là điều
    duy nhất phép so này muốn nói, nên hình mã hoá nó thành một đại lượng nhìn thấy
    được chứ không bắt người đọc chia hai con số.
    """
    (key_a, dim_a), (key_b, dim_b) = spec["pairs"]
    n = len(rows)
    missing = []

    for i, r in enumerate(rows):
        a, b = _num(r.get(key_a)), _num(r.get(key_b))
        pair = [(a, dim_a, key_a), (b, dim_b, key_b)]
        have = [(v, d) for v, d, _ in pair if v]

        # Hai chấm lệch nhau một chút theo chiều dọc. Không lệch thì ở những bài
        # hai chiều gần bằng nhau — đúng những bài quan trọng nhất của trục ngôn
        # ngữ — chấm sau đè kín chấm trước, và hình mất hẳn một chiều.
        ya, yb = i - 0.15, i + 0.15
        if len(have) == 2:
            ax.plot([a, b], [ya, yb], color="#cfcfc9", lw=2.2, zorder=2,
                    solid_capstyle="round")
        for v, d, yy in ((a, dim_a, ya), (b, dim_b, yb)):
            if not v:
                continue
            ax.plot(v, yy, marker=DIMENSION_MARKER[d], markersize=9.5,
                    color=DIMENSION_COLOR[d], markeredgecolor=SURFACE,
                    markeredgewidth=2.0, linestyle="none", zorder=6)

        if len(have) == 2:
            note = _ratio_text(b / a if spec["ratio"] == "b/a" else a / b)
            if _pct_gap(a, b) < 1.0:
                note += "  (≈ trùng)"
            ax.text(max(a, b) * 1.45, i, note, va="center", ha="left",
                    fontsize=8.5, color=INK_MUTED, zorder=4)
        else:
            gone = [k for v, _, k in pair if not v]
            missing.append(f"{r.get('bài')} ({', '.join(gone)})")

    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{r.get('bài')}  {_short_title(r.get('tên', ''))}"
                        for r in rows])
    ax.set_ylim(n - 0.4, -0.6)   # đảo chiều bằng chính biên, xem `bench_chart`
    ax.set_xscale("log")
    ax.set_xlabel("số nhánh duyệt (thang log)")
    ax.set_title(title, loc="left", pad=30)
    _tidy(ax)

    handles = [plt.Line2D([], [], marker=DIMENSION_MARKER[d], linestyle="none",
                          markersize=9, color=DIMENSION_COLOR[d],
                          label=DIMENSION_LABEL[d]) for _, d in spec["pairs"]]
    # Chú giải nằm TRÊN vùng vẽ: đặt trong vùng vẽ thì nó che mất hàng cuối, mà
    # hàng cuối (bài 3.2) lại đúng là hàng báo cáo dẫn ra nhiều nhất.
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, 1.005),
              ncol=2, handletextpad=0.4, columnspacing=1.6)
    return missing


def _lang_note(rows) -> str:
    """Câu chốt của trục ngôn ngữ, TÍNH TỪ SỐ LIỆU chứ không gõ tay."""
    gaps = []
    for r in rows:
        a, b = _num(r.get("OPL nhánh")), _num(r.get("DOcplex.cp nhánh"))
        if a and b:
            gaps.append((_pct_gap(a, b), r.get("bài")))
    if not gaps:
        return "Chưa đủ số liệu để rút kết luận cho trục này."
    gaps.sort()
    (lo_pct, lo_p), (hi_pct, hi_p) = gaps[0], gaps[-1]
    return _wrap(
        f"Con số bên phải: tỉ lệ nhánh {_LANG_SPEC['ratio_of']}. Đoạn nối dài = chênh "
        f"lệch lớn. Bài {lo_p} hai chấm gần trùng (chênh {lo_pct:.2g} %): mọi khái niệm ánh "
        f"xạ một–một giữa hai ngôn ngữ. Bài {hi_p} đoạn nối dài nhất (chênh {hi_pct:.0f} %): "
        f"allDifferent của OPL không nhận mảng biểu thức nên ép thêm biến phụ. "
        f"⇒ NGÔN NGỮ CHỈ ẢNH HƯỞNG HIỆU NĂNG KHI NÓ ÉP VIẾT MỘT MÔ HÌNH TOÁN KHÁC ĐI; "
        f"khác biệt thuần cú pháp dừng ở mức dễ đọc."
    )


def _eng_note(rows) -> str:
    """Câu chốt của trục engine, tính từ số liệu."""
    fewer, total, best = 0, 0, (1.0, None)
    faster_cpo = []
    for r in rows:
        c, s = _num(r.get("CPO nhánh")), _num(r.get("CP-SAT nhánh"))
        tc, ts = _num(r.get("CPO (s)")), _num(r.get("CP-SAT (s)"))
        if c and s:
            total += 1
            if s < c:
                fewer += 1
            if c / s > best[0]:
                best = (c / s, r.get("bài"))
        if tc and ts and tc < ts:
            faster_cpo.append(str(r.get("bài")))
    if not total:
        return "Chưa đủ số liệu để rút kết luận cho trục này."
    slower = (f"Nhưng ÍT NHÁNH KHÔNG ĐỒNG NGHĨA NHANH HƠN: bài {', '.join(faster_cpo)} "
              f"CP Optimizer vẫn về trước — mỗi nhánh của CP-SAT đắt hơn nhiều."
              if faster_cpo else
              "Ở bộ dữ liệu này CP-SAT về trước ở mọi bài.")
    return _wrap(
        f"Con số bên phải: tỉ lệ nhánh {_ENG_SPEC['ratio_of']}. CP-SAT duyệt ít nhánh hơn ở "
        f"{fewer}/{total} bài (bài {best[1]} ít hơn {best[0]:.0f}×) nhờ học mệnh đề xung đột: "
        f"mỗi lần thất bại cắt được cả một vùng lớn. {slower} "
        f"⇒ Không bên nào thắng toàn diện — mỗi engine thắng ở lớp bài mà cấu trúc dữ liệu "
        f"lõi của nó phục vụ."
    )


def axis_charts(lang=None, eng=None, figsize=(13.4, 6.8)):
    """Hai trục so sánh, cạnh nhau — trục NGÔN NGỮ và trục ENGINE.

    Truyền thẳng hai bảng của `nbutil.axis_tables()` vào để **không chạy lại
    solver**; bỏ trống thì hàm tự gọi `axis_tables()`, và lời gọi đó cũng dùng lại
    bộ nhớ đệm `nbutil._RUNS` chứ không chạy lại engine.
    """
    if lang is None or eng is None:
        from nbutil import axis_tables

        lang, eng = axis_tables()
    lang_rows, eng_rows = _rows(lang), _rows(eng)
    plt = _plt()

    fig, axes = plt.subplots(1, 2, figsize=figsize, sharex=True)

    missing = _dumbbell_panel(
        axes[0], lang_rows, _LANG_SPEC,
        "Trục NGÔN NGỮ — cùng engine CP Optimizer, khác ngôn ngữ mô hình hoá", plt)
    missing += _dumbbell_panel(
        axes[1], eng_rows, _ENG_SPEC,
        "Trục ENGINE — cùng Python, khác engine", plt)

    values = [v for rows, spec in ((lang_rows, _LANG_SPEC), (eng_rows, _ENG_SPEC))
              for r in rows for k, _ in spec["pairs"] if (v := _num(r.get(k)))]
    if values:
        lo, hi = _log_limits(values, pad_lo=2.6, pad_hi=9.0)
        axes[0].set_xlim(lo, hi)

    # Hàng thiếu số liệu: nói ra ngay trên hình, và nói rõ nó KHÁC với "bằng 0".
    for ax, rows, spec in ((axes[0], lang_rows, _LANG_SPEC),
                           (axes[1], eng_rows, _ENG_SPEC)):
        for i, r in enumerate(rows):
            if sum(1 for k, _ in spec["pairs"] if _num(r.get(k))) < 2:
                # Đặt ở mép phải — đúng chỗ tỉ lệ vẫn hiện với hàng đủ số liệu, nên
                # đọc thành "hàng này không có tỉ lệ vì thiếu số đo". Chấm của chiều
                # còn lại (nếu có) vẫn nằm trên cùng, không bị hộp che.
                ax.text(0.985, i, "chưa có số liệu — chiều tương ứng không chạy được",
                        transform=ax.get_yaxis_transform(), ha="right", va="center",
                        fontsize=8.5, style="italic", color=STATUS_BLOCKED, zorder=5,
                        bbox=dict(boxstyle="round,pad=0.35", facecolor=SURFACE,
                                  edgecolor=STATUS_BLOCKED, linewidth=0.8))

    fig.suptitle("Hai trục so sánh của báo cáo — số nhánh duyệt trên cùng một bài",
                 x=0.008, y=0.985, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.008, 0.947,
             "Thang log: khoảng cách bằng nhau = tỉ lệ bằng nhau, nên ĐỘ DÀI ĐOẠN NỐI "
             "chính là tỉ lệ số nhánh giữa hai chiều.",
             fontsize=8.5, color=INK_MUTED, ha="left", va="top")

    fig.text(0.008, 0.02, _lang_note(lang_rows), fontsize=8, color=INK_MUTED,
             va="bottom", ha="left", linespacing=1.55)
    fig.text(0.515, 0.02, _eng_note(eng_rows), fontsize=8, color=INK_MUTED,
             va="bottom", ha="left", linespacing=1.55)
    if missing:
        fig.text(0.008, 0.155,
                 _wrap("Thiếu số liệu ở: " + "; ".join(missing)
                       + " — ô trống nghĩa là CHƯA ĐO ĐƯỢC, không phải bằng 0, và không "
                         "phải lỗi mô hình (xem COLAB.md).", 130),
                 fontsize=8, color=STATUS_BLOCKED, va="bottom", ha="left")

    fig.subplots_adjust(left=0.192, right=0.978, top=0.815, bottom=0.30, wspace=0.58)
    return _finish(fig)


# --------------------------------------------------------------------------- #
# 3. Trần Community Edition
# --------------------------------------------------------------------------- #

#: Trần của CPLEX Studio Community: không gian tìm kiếm tối đa 2^1000 (PLAN.md §2.1).
COMMUNITY_LOG2_CEILING = 1000

#: Các điểm đo/ước tính về log₂ không gian tìm kiếm.
#:
#: `measured=True` là số ĐO ĐƯỢC (engine tự báo, hoặc tính thẳng từ miền biến của
#: mô hình đã chạy); `measured=False` là ƯỚC TÍNH. Hai loại không được vẽ giống
#: nhau — trộn chúng là biến một phỏng đoán thành một phép đo.
#: `accepted` nói engine Community có nhận bài hay không, và đó luôn là quan sát
#: thật, kể cả khi kích thước bài chỉ ước tính được.
_COMMUNITY_POINTS = [
    {"label": "1.2 N-Queens, N = 8", "log2": 24.0, "measured": True,
     "accepted": True, "source": "PLAN.md §2.1"},
    {"label": "3.1 Sports, n = 6", "log2": 510.6, "measured": True,
     "accepted": True, "source": "models/3.1_sports/manifest.json"},
    {"label": "3.2 Timetable, large + khả dụng", "log2": 780.3, "measured": True,
     "accepted": True, "source": "PLAN.md §2.1/§2.5"},
    {"label": "3.2 Timetable, large", "log2": 786.4, "measured": True,
     "accepted": True, "source": "PLAN.md §2.1/§2.5"},
    {"label": "3.1 Sports, n = 8", "log2": 1092.0, "measured": False,
     "accepted": False, "source": "models/3.1_sports/manifest.json"},
    {"label": "1.2 N-Queens, N = 200", "log2": 1529.0, "measured": False,
     "accepted": False, "source": "PLAN.md §2.1"},
    {"label": "3.2 mã hoá nhị phân (brief §4)", "log2": 2800.0, "measured": False,
     "accepted": None, "source": "PLAN.md §2.1"},
]


def _community_points() -> list[dict]:
    """Điểm đo, ưu tiên số trong `manifest.json` khi có — để hình không lệch kho."""
    import json

    pts = [dict(p) for p in _COMMUNITY_POINTS]
    path = ROOT / "models" / "3.1_sports" / "manifest.json"
    if path.exists():
        lim = json.loads(path.read_text(encoding="utf-8")).get(
            "community_edition_limit") or {}
        by_label = {p["label"]: p for p in pts}
        for label, key in (("3.1 Sports, n = 6", "measured_log2_search_space_n6"),
                           ("3.1 Sports, n = 8", "estimated_log2_search_space_n8")):
            v = _num(lim.get(key))
            if v and label in by_label:
                by_label[label]["log2"] = v
    return sorted(pts, key=lambda p: p["log2"])


def community_limit_chart(figsize=(11.2, 5.4)):
    """Trần 2^1000 của CPLEX Community so với không gian tìm kiếm từng bài.

    Trục hoành để **tuyến tính**: đại lượng vẽ đã là $\\log_2$ của không gian tìm
    kiếm, tức bản thân nó đã là một thang log. Vẽ log của log thì mốc 1000 — thứ
    duy nhất hình này muốn nói — hết đọc được.
    """
    pts = _community_points()
    plt = _plt()
    fig, ax = plt.subplots(figsize=figsize)

    for i, p in enumerate(pts):
        color = (STATUS_UNTESTED if p["accepted"] is None
                 else STATUS_OK if p["accepted"] else STATUS_BLOCKED)
        ax.barh(i, p["log2"], height=_BAR_H, zorder=3,
                color=color if p["measured"] else SURFACE,
                edgecolor=color, linewidth=1.4,
                hatch=None if p["measured"] else "///")
        # Nhãn nói cả ba điều một lúc: giá trị, đo được hay ước tính, và engine có
        # nhận bài hay không. Nhờ vậy hình không cần chú giải riêng, và không có
        # thông tin nào chỉ tồn tại dưới dạng màu.
        size = (f"{p['log2']:.1f}" if p["measured"]
                else f"≈{p['log2']:.0f} (ước tính)")
        state = ("chưa từng chạy" if p["accepted"] is None
                 else "engine chạy" if p["accepted"] else "engine TỪ CHỐI")
        # Nền trắng sau nhãn: vạch trần 2^1000 cắt ngang đúng chỗ nhãn của hai bài
        # 3.2 (780.3 và 786.4), không có nền thì nét đứt chạy xuyên qua chữ.
        ax.text(p["log2"] + 45, i, f"{size} · {state}", va="center", ha="left",
                fontsize=8.5, color=INK_MUTED, zorder=4,
                bbox=dict(boxstyle="square,pad=0.18", facecolor=SURFACE,
                          edgecolor="none"))

    ax.axvline(COMMUNITY_LOG2_CEILING, color=STATUS_BLOCKED, lw=1.6,
               linestyle=(0, (5, 3)), zorder=2)
    ax.text(COMMUNITY_LOG2_CEILING - 30, -0.85,
            f"trần Community: $2^{{{COMMUNITY_LOG2_CEILING}}}$", ha="right",
            va="center", fontsize=9, color=STATUS_BLOCKED, fontweight="bold")

    ax.set_yticks(range(len(pts)))
    ax.set_yticklabels([p["label"] for p in pts])
    ax.set_ylim(-1.3, len(pts) - 0.3)
    ax.invert_yaxis()
    ax.set_xlim(0, max(p["log2"] for p in pts) * 1.46)
    ax.set_xlabel("$\\log_2$ không gian tìm kiếm (thang tuyến tính)")
    ax.set_title("Trần giấy phép của CPLEX Studio Community — đo được ở đâu",
                 loc="left", pad=22, fontsize=13, fontweight="bold")
    _tidy(ax)

    # Không có chú giải: mỗi cột đã tự khai giá trị, loại số và trạng thái ngay
    # bên cạnh nó. Một chú giải ba dòng ở hình bảy cột chỉ có chỗ đặt là đè lên
    # chính dữ liệu.
    fig.text(0.008, 0.005, _wrap(
        "Cột đặc = số ĐO ĐƯỢC, cột gạch chéo = số ƯỚC TÍNH — hai loại không đọc như nhau; "
        "riêng trạng thái chạy/từ chối thì luôn là quan sát thật. "
        "Hai điều hình này cho thấy: (1) thêm ràng buộc làm không gian tìm kiếm GIẢM "
        "(786.4 → 780.3 ở bài 3.2, dù số ràng buộc gần gấp đôi) — trần tính theo không gian "
        "tìm kiếm chứ không theo số ràng buộc; (2) trần là giới hạn GIẤY PHÉP chứ không phải "
        "giới hạn năng lực engine — CP-SAT giải xong cả những bài mà CP Optimizer Community "
        "từ chối nhận.", 148),
        fontsize=8, color=INK_MUTED, va="bottom", ha="left", linespacing=1.5)

    fig.subplots_adjust(left=0.245, right=0.99, top=0.875, bottom=0.245)
    return _finish(fig)
