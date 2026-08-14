"""Tiện ích cho notebook — giữ cho notebook mỏng và không lặp lại nội dung.

Nguyên tắc: notebook **không nhúng lại** code model hay mô hình toán. Nó đọc thẳng
từ `models/<bài>/` rồi hiển thị. Nhờ vậy code in trong báo cáo luôn đúng là code
vừa chạy ra kết quả ngay bên dưới, và mô hình toán trong báo cáo luôn đúng là mô
hình đã được kiểm chứng — không có đường nào để hai thứ lệch nhau.

Dùng trong notebook:

    import sys; sys.path.insert(0, "../tools")
    from nbutil import *

    show_notes("3.2_timetable", "Mô hình toán")     # mô hình toán, LaTeX
    show_code("models/3.2_timetable/opl/timetabling_avail.mod")
    df = run_table("3.2_timetable")                  # chạy 3 chiều -> DataFrame
    show_source_matrix()                             # bảng ✅/✍️ toàn báo cáo
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from runner import (DIMENSIONS_ENV, ENGINE, LANGUAGE, ROOT, load_manifest,
                    run_companions, run_suite, skipped_dimensions)  # noqa: E402

MODELS = ROOT / "models"

_LANG_BY_SUFFIX = {".mod": "opl", ".py": "python", ".dat": "text", ".json": "json"}


def _md(text: str):
    """Trả về đối tượng Markdown của IPython nếu có, ngược lại trả chuỗi."""
    try:
        from IPython.display import Markdown

        return Markdown(text)
    except ImportError:
        return text


def problems() -> list[str]:
    """Danh sách tên bài, theo thứ tự 1.1, 1.2, 2.1, ... (có manifest.json)."""
    return sorted(p.parent.name for p in MODELS.glob("*/manifest.json"))


def manifest(problem: str) -> dict:
    return load_manifest(MODELS / problem)


# --------------------------------------------------------------------------- #
# Hiển thị nội dung có sẵn trong repo
# --------------------------------------------------------------------------- #

#: Tiền tố đánh mục kiểu "(a) ", "(b) " ở đầu tiêu đề — bỏ đi khi so khớp.
_SECTION_MARKER = re.compile(r"^\([a-z]\)\s*", re.IGNORECASE)


def _normalise_title(title: str) -> str:
    return _SECTION_MARKER.sub("", title.lstrip("# ").strip()).lower()


def notes_section(problem: str, heading: str) -> str:
    """Lấy nguyên văn một mục cấp 2 của NOTES.md.

    So khớp có bỏ qua tiền tố đánh mục "(a) "/"(b) " và không phân biệt hoa
    thường, nên `notes_section(p, "Mô hình toán")` khớp được cả
    "## (b) Mô hình toán học — DÙNG CHUNG cho cả ba chiều".
    """
    path = MODELS / problem / "NOTES.md"
    if not path.exists():
        return f"*(chưa có `{path.relative_to(ROOT)}`)*"
    blocks = re.split(r"\n(?=## )", path.read_text(encoding="utf-8"))
    key = _normalise_title(heading)
    for block in blocks:
        if _normalise_title(block.split("\n", 1)[0]).startswith(key):
            return block.strip()
    available = [b.split("\n", 1)[0].lstrip("# ").strip() for b in blocks[1:]]
    return f"*(không tìm thấy mục “{heading}”. Có: {', '.join(available)})*"


def show_notes(problem: str, heading: str):
    """Hiển thị một mục của NOTES.md — dùng cho phát biểu bài toán và mô hình toán."""
    return _md(notes_section(problem, heading))


def show_code(path: str | pathlib.Path, first: int | None = None,
              last: int | None = None, title: str | None = None):
    """Hiển thị mã nguồn từ file, tô màu theo phần mở rộng.

    `first`/`last` cắt theo số dòng (đếm từ 1) khi chỉ muốn trích một đoạn.
    """
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = ROOT / p
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    lo = (first - 1) if first else 0
    hi = last if last else len(lines)
    body = "\n".join(lines[lo:hi])
    lang = _LANG_BY_SUFFIX.get(p.suffix, "")
    header = title or f"`{p.relative_to(ROOT)}`"
    span = f" (dòng {first}–{last})" if first else ""
    return _md(f"**{header}**{span}\n\n```{lang}\n{body}\n```")


def show_dimension_code(problem: str, dimension: str, **kw):
    """Hiển thị model của một chiều, lấy đường dẫn từ manifest.json."""
    spec = manifest(problem)["dimensions"][dimension]
    mark = {"official": "✅ mẫu chính thức", "new": "✍️ viết mới",
            "official+extended": "✅+✍️ mẫu chính thức, có mở rộng"}
    title = (f"{LANGUAGE[dimension]} → engine {ENGINE[dimension]} "
             f"· {mark.get(spec.get('source'), spec.get('source', ''))}")
    return show_code(spec["model"], title=title, **kw)


# --------------------------------------------------------------------------- #
# Chạy và lập bảng
# --------------------------------------------------------------------------- #

#: Kết quả chạy đã có, theo tên bài. Một notebook thường vừa lập bảng vừa kiểm
#: chứng chéo cho cùng một bài — không cache thì solver chạy hai lần cho cùng một
#: thứ, và tệ hơn là hai lần đó có thể ra số khác nhau (CP-SAT đa luồng).
_RUNS: dict[str, list] = {}

#: Cảnh báo `CP_DIMENSIONS` chỉ in một lần cho cả notebook, không lặp lại mỗi bài.
_WARNED_SKIP = False

_SOURCE_MARK = {"official": "✅", "new": "✍️", "official+extended": "✅+✍️"}


# --------------------------------------------------------------------------- #
# Phân biệt "chiều không chạy được" với "chiều cho kết quả khác"
#
# Đây là ranh giới quan trọng nhất của cả file. Một bản ghi FAIL có thể đến từ hai
# nguyên nhân hoàn toàn khác nhau, và chẩn đoán nhầm thì báo cáo gửi người đọc đi
# sửa đúng thứ không hỏng:
#
#   * `status is None`  -> tiến trình con không in nổi một dòng RESULT nào. Máy này
#     thiếu engine, hoặc lệnh chạy hỏng. KHÔNG nói lên điều gì về mô hình.
#   * `status` có giá trị nhưng không nằm trong danh sách thành công (`Infeasible`,
#     `Invalid`, `Timeout`, ...) -> engine đã chạy và trả lời; câu trả lời mới là
#     thứ đáng nghi.
#
# Không bao giờ được dùng `x or 0` để lấp một trong hai trường hợp trên: `None or 0`
# biến "chưa đo được" thành "đo được và bằng 0", tức là bịa ra một kết luận.
# --------------------------------------------------------------------------- #

#: Số đếm bằng chữ, cho câu văn kiểu "cả ba đều tìm được nghiệm".
_COUNT_WORD = {2: "hai", 3: "ba", 4: "bốn", 5: "năm", 6: "sáu"}


def _did_not_run(rec) -> bool:
    """Chiều không chạy được: không có `status`, tức không có dòng RESULT nào."""
    return not rec.ok and rec.status is None


def _no_solution(rec) -> bool:
    """Chiều chạy được nhưng không cho nghiệm hợp lệ — đây mới là tín hiệu về mô hình."""
    return not rec.ok and rec.status is not None


def _names(labels) -> str:
    return ", ".join(f"`{d}`" for d in labels)


def _subject(n: int) -> tuple[str, str]:
    """Chủ ngữ và động từ cho câu chốt của bài CSP, theo SỐ CHIỀU THẬT SỰ có mặt.

    Con số "ba" từng được viết cứng trong chuỗi, nên nhóm chỉ còn một bản ghi vẫn
    in ra "cả ba đều tìm được nghiệm".
    """
    if n == 1:
        return "chiều duy nhất", "tìm được"
    return f"cả {_COUNT_WORD.get(n, str(n))}", "đều tìm được"


def _blocked_note(dead: list[str], bad: list[str]) -> str:
    """Câu từ chối kết luận, nói rõ chiều nào hỏng và hỏng theo kiểu gì."""
    parts = []
    if dead:
        parts.append(f"chiều {_names(dead)} **không chạy được** "
                     "(thiếu engine hoặc lỗi khi khởi chạy)")
    if bad:
        parts.append(f"chiều {_names(bad)} chạy được nhưng **không cho nghiệm hợp lệ**")
    mark = "⚠️" if dead else "❌"
    note = f"{mark} **KHÔNG ĐỐI CHIẾU ĐƯỢC** — " + "; ".join(parts)
    if dead:
        note += (". Thiếu engine KHÔNG phải lỗi mô hình; số liệu của chiều đó chưa "
                 "tồn tại nên không có gì để so — xem `COLAB.md`")
    return note


def _warn_broken(recs) -> None:
    """In cảnh báo khi có bản ghi hỏng, để ô trống trong bảng không bị hiểu nhầm."""
    dead = [r.label or r.dimension for r in recs if _did_not_run(r)]
    bad = [r.label or r.dimension for r in recs if _no_solution(r)]
    if dead:
        print(f"⚠️  Chiều {', '.join(dead)} KHÔNG chạy được trên máy này "
              "(thiếu engine hoặc lỗi khi khởi chạy).\n"
              "    Các ô trống bên dưới là vì chưa có số liệu, không phải vì "
              "kết quả bằng 0 — và không phải lỗi mô hình.")
    if bad:
        print(f"❌  Chiều {', '.join(bad)} chạy được nhưng không cho nghiệm hợp lệ.")


def _fmt(v):
    """Định dạng một ô cho `frame()`.

    Styler mặc định in float với 6 chữ số thập phân cố định — thời gian giải hoá
    thành `0.021000`, tỉ lệ thành `5.430000`. `%g` cắt số 0 thừa nên `0.023`,
    `0.0017`, `645.91` giữ nguyên bề ngoài như bảng pandas thường.
    """
    return f"{v:g}" if isinstance(v, float) else v


def frame(rows: list[dict]):
    """Bảng từ danh sách dict — DataFrame thường, chỉ khác ở cách HIỂN THỊ.

    Hai chỗ sửa so với `_repr_html_` mặc định của pandas:

    * **Cột số căn phải, cột chữ căn trái.** Mặc định của nbconvert căn PHẢI mọi
      ô, kể cả cột chữ (tên bài, trạng thái) nên mép trái của các cột đó lởm
      chởm. Căn trái tất cả thì hết lởm chởm nhưng lại không dò được độ lớn của
      số: 201 và 141455 bắt đầu ở cùng một cột, phải đếm chữ số mới biết cái nào
      lớn hơn. Chia theo kiểu dữ liệu mới đúng cả hai.
    * **Bỏ cột chỉ số.** RangeIndex 0,1,2,… là hiện vật của pandas, trong báo cáo
      nó chỉ là một cột số vô nghĩa nằm trước cột đầu tiên.

    Vẫn là DataFrame nên mọi thao tác pandas khác giữ nguyên; chỉ `_repr_html_`
    bị đổi, và cũng chỉ đổi khi có `pandas.io.formats.style` (cần jinja2).
    """
    try:
        import pandas as pd
    except ImportError:
        return rows

    class _Aligned(pd.DataFrame):
        @property
        def _constructor(self):
            return _Aligned

        def _repr_html_(self):
            try:
                numeric = list(self.select_dtypes("number").columns)
                styler = self.style.hide(axis="index").format(_fmt, na_rep="—")
                if numeric:
                    styler = styler.set_table_styles(
                        {c: [{"selector": "", "props": [("text-align", "right")]}]
                         for c in numeric},
                        axis=0, overwrite=False)
                return styler.to_html()
            except ImportError:      # thiếu jinja2 -> quay về bảng thường
                return super()._repr_html_()

    return _Aligned(rows)


def runs(problem: str, timeout: int = 900, refresh: bool = False) -> list:
    """Chạy cả ba chiều của một bài (kèm bản phụ trợ nếu có), ghi nhớ kết quả.

    Bản phụ trợ khai ở khoá `companion` của manifest được chạy cùng, vì thiếu nó
    thì có bài không đủ ba điểm đo trên cùng một biến thể — xem PLAN.md §2.7.

    Nếu `CP_DIMENSIONS` đang lọc bớt chiều, in một cảnh báo (đúng một lần cho cả
    notebook): báo cáo thiếu chiều mà không nói gì thì tệ hơn là không chạy.
    """
    global _WARNED_SKIP
    missing = skipped_dimensions()
    if missing and not _WARNED_SKIP:
        _WARNED_SKIP = True
        print(f"⚠️  {DIMENSIONS_ENV} đang lọc: KHÔNG chạy chiều "
              f"{', '.join(sorted(missing))}.\n"
              "    Mọi bảng dưới đây chỉ có số liệu của chiều còn lại, và bảng trục "
              "so sánh nào cần chiều bị bỏ sẽ rỗng.\n"
              "    Đây KHÔNG phải lỗi mô hình — máy này thiếu engine tương ứng "
              "(xem COLAB.md).")
    if refresh or problem not in _RUNS:
        _RUNS[problem] = (run_suite(MODELS / problem, timeout=timeout)
                          + run_companions(MODELS / problem, timeout=timeout))
    return _RUNS[problem]


def run_table(problem: str, timeout: int = 900):
    """Chạy cả ba chiều của một bài, trả về DataFrame (hoặc list dict nếu thiếu pandas)."""
    _warn_broken(runs(problem, timeout=timeout))
    has_variants = len({r.variant for r in runs(problem, timeout=timeout)}) > 1
    rows = []
    for rec in runs(problem, timeout=timeout):
        row = {
            "chiều": rec.label or rec.dimension,
            "ngôn ngữ": rec.language,
            "engine": rec.engine,
            "nguồn": _SOURCE_MARK.get(rec.source, rec.source),
        }
        if has_variants:
            row["biến thể"] = rec.variant
        row |= {
            "trạng thái": rec.status,
            "mục tiêu": rec.objective,
            "thời gian giải (s)": rec.solve_time_s,
            "nhánh": rec.branches,
            "fails/conflicts": rec.fails,
        }
        rows.append(row)
    return frame(rows)


def cross_check(problem: str, timeout: int = 900):
    """Kiểm chứng chéo giữa ba chiều.

    Không có bước này thì mọi so sánh hiệu năng đều vô nghĩa — nhanh hơn mà giải
    sai bài thì không nói lên điều gì.

    Bài tối ưu và bài CSP thuần được kiểm theo hai cách khác nhau, và hàm này nói
    rõ nó đang kiểm cái gì. Với bài CSP, mọi giá trị mục tiêu đều là `None`; nếu
    cứ so `None == None` rồi báo "khớp" thì đó là sự yên tâm giả — phép so không
    xác nhận điều gì cả.
    """
    import collections

    recs = runs(problem, timeout=timeout)
    spec = manifest(problem)

    # Gom theo biến thể bài toán, lấy thẳng từ bản ghi chứ không tra lại theo tên
    # chiều — bản phụ trợ dùng chung tên chiều với mẫu chính thức nhưng giải biến
    # thể khác, tra theo tên chiều sẽ xếp nhầm nhóm.
    #
    # Vài bài có hai mẫu chính thức của IBM trùng tên nhưng là hai bài toán khác
    # nhau (PLAN.md §2.7); đối chiếu objective xuyên biến thể là so hai thứ khác
    # nhau, phải tránh.
    groups: dict[object, list] = collections.defaultdict(list)
    for r in recs:
        groups[r.variant].append(r)

    out = [f"**Kiểm chứng chéo — bài {problem}**\n"]
    if len(groups) > 1:
        warning = spec.get("two_official_variants", {}).get("warning")
        out.append(f"> ⚠️ {warning}\n" if warning else
                   "> ⚠️ Bài này có nhiều biến thể; chỉ đối chiếu trong cùng biến thể.\n")

    all_ok = True
    for variant, group in sorted(groups.items(), key=lambda kv: str(kv[0])):
        label = f"**Biến thể {variant}** — " if variant is not None else ""
        objs = {r.label: r.objective for r in group}
        values = [v for v in objs.values() if v is not None]
        ran = all(r.ok for r in group)
        # Hai loại hỏng, hai chẩn đoán khác nhau — xem ghi chú ở đầu file.
        dead = [r.label for r in group if _did_not_run(r)]
        bad = [r.label for r in group if _no_solution(r)]

        if not values:  # CSP thuần: không có gì để đối chiếu
            detail = " · ".join(f"`{r.label}` → {r.status}" for r in group)
            all_ok &= ran
            subject, verb = _subject(len(group))
            out.append(
                f"{label}CSP thuần, không có hàm mục tiêu\n\n{detail} → "
                + (f"{_blocked_note(dead, bad)}\n" if (dead or bad)
                   else f"✅ {subject} {verb} nghiệm khả thi\n")
                + "\n> Không có giá trị mục tiêu để đối chiếu, nên phép kiểm ở đây chỉ "
                + ("nhằm xác nhận" if (dead or bad) else "xác nhận")
                + f" **{subject} {verb} nghiệm**. Tính hợp lệ của từng nghiệm "
                  "do chính model tự kiểm lại theo dữ liệu gốc rồi báo qua `status`; "
                  "nghiệm sai thành `Invalid` và bị `runner.py` tính là FAIL.\n"
            )
            continue

        detail = " · ".join(f"`{d}` = {v}" for d, v in objs.items())
        if len(group) < 2:
            out.append(f"{label}{detail} → ⚠️ chỉ có một chiều, **không đối chiếu được**\n")
            all_ok &= ran
            continue

        # Có chiều hỏng thì phép so không còn cơ sở: giá trị vắng mặt không phải là
        # một giá trị "khác", nên không được kết luận LỆCH — càng không được quy cho
        # mô hình khi thứ thiếu chỉ là engine.
        if dead or bad:
            all_ok = False
            out.append(f"{label}{detail} → {_blocked_note(dead, bad)}\n")
            continue

        agree = len(set(values)) == 1 and len(values) == len(group)
        all_ok &= agree and ran
        out.append(f"{label}{detail} → "
                   + ("✅ **KHỚP** — các chiều cùng một nghiệm tối ưu\n" if agree and ran
                      else "❌ **LỆCH — có lỗi trong mô hình**\n"))

    if not all_ok:
        out.append("\n**Có mục chưa đạt — xem lại trước khi dùng số liệu so sánh.**")
    return _md("\n".join(out))


def _pick(group: list, dimension: str, prefer_label: str | None = None):
    """Chọn một bản ghi của `dimension` trong nhóm; ưu tiên nhãn chỉ định."""
    hits = [r for r in group if r.dimension == dimension]
    if prefer_label:
        for r in hits:
            if r.label == prefer_label:
                return r
    return hits[0] if hits else None


def _ratio(a, b):
    """Tỉ lệ a/b, trả về None khi không tính được."""
    if a is None or b in (None, 0):
        return None
    return round(a / b, 2)


def _stat(rec, attr):
    """Số liệu của một bản ghi để đưa vào bảng SO SÁNH — `None` nếu chiều đó FAIL.

    Số nhánh của một lần chạy hỏng (timeout, chạm trần giấy phép, không khởi động
    được) không phải một điểm đo: đặt nó cạnh số của lần chạy xong là mời người đọc
    so hai thứ không so được.
    """
    return getattr(rec, attr) if rec.ok else None


#: Ngưỡng chênh lệch tương đối để cột "engine nhanh hơn" dám gọi tên một bên.
#:
#: Cột đó quyết bằng **đúng một** lần chạy mỗi ô, trong khi thời gian đồng hồ dao
#: động theo tải máy (PLAN.md §2.4) — số nhánh thì tất định nên không cột nào khác
#: cần ngưỡng này. Chênh lệch nhỏ nằm gọn trong dải nhiễu: dựng lại báo cáo lúc máy
#: bận là cột lật ngược và mâu thuẫn với văn xuôi.
#:
#: Con số 0.50 **đo mà ra**, không chọn cho tròn. Bài 3.1 (biến thể A) là ô sát ranh
#: giới nhất của báo cáo — đo lặp cho `docplexcp` 2.596–2.825 s và `ortools`
#: 2.946–4.167 s, tức trung vị chỉ chênh ~17 %. Chạy lại đúng phép so đó 6 lần trên
#: một máy rảnh thì chênh lệch **của cùng một cặp** trải từ 16 % tới 39 %: ngưỡng
#: 20 % hay 30 % sẽ khiến chính ô này lúc ghi "≈ ngang nhau" lúc gọi tên engine —
#: đổi một kiểu bất định lấy một kiểu bất định khác. Cùng phép đo ấy ở bài 3.2 cho
#: 64–80 %. Đặt ngưỡng ở 0.50 (bên chậm phải chậm hơn ít nhất **1.5×**) tách sạch
#: hai bài, còn dư biên ở cả hai phía.
#:
#: Chênh lệch tương đối tính theo bên NHANH hơn. Dưới ngưỡng thì ghi "≈ ngang nhau":
#: thà nói "một lần chạy không phân biệt được" còn hơn tuyên bố một điều lật được
#: khi chạy lại. Muốn phân định ở dưới mức này thì phải đo lặp — xem `make bench`.
NEGLIGIBLE_TIME_DIFF = 0.50

#: Nhãn cho ô mà chênh lệch thời gian nằm dưới `NEGLIGIBLE_TIME_DIFF`.
_TOO_CLOSE = "≈ ngang nhau"


def _faster(cpo, sat):
    """Engine nào giải nhanh hơn — KHÔNG đoán khi thiếu số liệu, KHÔNG phân thắng
    bại trên chênh lệch nằm trong nhiễu.

    Công thức cũ `"CP-SAT" if (sat.solve_time_s or 0) < (cpo.solve_time_s or 0)`
    dán nhãn "CP Optimizer" cho một chiều còn chưa khởi động nổi: `None or 0` ra
    `0`, nên `1.89 < 0` là `False` và nhánh `else` thắng. Thiếu số liệu thì phải nói
    là thiếu, không được rơi vào nhánh mặc định.

    Nó cũng gọi tên người thắng ở mọi chênh lệch, dù nhỏ đến đâu — xem
    `NEGLIGIBLE_TIME_DIFF`.
    """
    broken = [r.label for r in (cpo, sat) if not r.ok]
    if broken:
        return f"⚠️ {', '.join(broken)} không chạy được"
    if cpo.solve_time_s is None or sat.solve_time_s is None:
        return None
    lo, hi = sorted((cpo.solve_time_s, sat.solve_time_s))
    # `lo <= 0` thì không có mẫu số để tính tỉ lệ: hai bên cùng 0 là không phân biệt
    # được, còn 0 so với một số dương thì chênh lệch là vô hạn, gọi tên được.
    too_close = (hi <= 0) if lo <= 0 else (hi - lo) / lo < NEGLIGIBLE_TIME_DIFF
    if too_close:
        return _TOO_CLOSE
    return "CP-SAT" if sat.solve_time_s < cpo.solve_time_s else "CP Optimizer"


def axis_tables(timeout: int = 900):
    """Dựng hai bảng trục so sánh, từ số liệu CHẠY THẬT của mọi bài.

    Bảng được sinh ra chứ không gõ tay, nên không thể lệch với code trong kho.
    Mỗi hàng chỉ gộp các bản ghi **cùng biến thể** (PLAN.md §2.7).

    Trả về (bảng trục ngôn ngữ, bảng trục engine).
    """
    import collections

    lang, eng = [], []
    broken: list[str] = []
    for p in problems():
        recs = runs(p, timeout=timeout)
        broken += [f"{p.split('_')[0]} · {r.label or r.dimension}"
                   for r in recs if not r.ok]
        title = manifest(p).get("title", p)
        groups: dict[object, list] = collections.defaultdict(list)
        for r in recs:
            groups[r.variant].append(r)

        for variant, group in sorted(groups.items(), key=lambda kv: str(kv[0])):
            name = f"{p.split('_')[0]}" + (f" ({variant})" if variant else "")
            opl = _pick(group, "opl")
            cpo = _pick(group, "docplexcp")
            sat = _pick(group, "ortools")

            # Trục NGÔN NGỮ: cùng engine CP Optimizer, khác ngôn ngữ mô hình hoá.
            if opl and cpo:
                lang.append({
                    "bài": name, "tên": title,
                    "OPL nhánh": _stat(opl, "branches"),
                    "DOcplex.cp nhánh": _stat(cpo, "branches"),
                    "OPL (s)": _stat(opl, "solve_time_s"),
                    "DOcplex.cp (s)": _stat(cpo, "solve_time_s"),
                    "tỉ lệ nhánh": _ratio(_stat(cpo, "branches"),
                                          _stat(opl, "branches")),
                })
            # Trục ENGINE: cùng Python, khác engine.
            if cpo and sat:
                eng.append({
                    "bài": name, "tên": title,
                    "CPO nhánh": _stat(cpo, "branches"),
                    "CP-SAT nhánh": _stat(sat, "branches"),
                    "CPO (s)": _stat(cpo, "solve_time_s"),
                    "CP-SAT (s)": _stat(sat, "solve_time_s"),
                    "CP-SAT ít nhánh hơn": _ratio(_stat(cpo, "branches"),
                                                  _stat(sat, "branches")),
                    "engine nhanh hơn": _faster(cpo, sat),
                })

    if broken:
        print("⚠️  Hai bảng trục KHÔNG kết luận được ở các ô sau — chiều tương ứng "
              "không chạy được trên máy này\n    (thiếu engine hoặc lỗi): "
              + "; ".join(broken) + ".\n"
              "    Ô trống nghĩa là CHƯA CÓ SỐ LIỆU, không phải bằng 0, và không "
              "phải lỗi mô hình — xem COLAB.md.")
    return frame(lang), frame(eng)


def show_source_matrix():
    """Bảng ✅/✍️ cho toàn báo cáo, sinh thẳng từ các manifest.json.

    Bảng này KHÔNG gõ tay, nên không bao giờ lệch với code thật đang có trong repo.
    """
    mark = {"official": "✅", "new": "✍️", "official+extended": "✅+✍️"}
    head = "| Bài | Tên | OPL | DOcplex.cp | OR-Tools |\n|---|---|---|---|---|\n"
    rows = []
    for name in problems():
        m = manifest(name)
        dims = m.get("dimensions", {})
        cells = [mark.get(dims.get(d, {}).get("source"), "—")
                 for d in ("opl", "docplexcp", "ortools")]
        rows.append(f"| {name.split('_')[0]} | {m.get('title', name)} | " + " | ".join(cells) + " |")
    legend = "\n\n✅ lấy mẫu chính thức · ✍️ viết mới · ✅+✍️ mẫu chính thức có mở rộng · — chưa có"
    return _md(head + "\n".join(rows) + legend)


__all__ = [
    "problems", "manifest", "notes_section", "show_notes", "show_code",
    "show_dimension_code", "runs", "frame", "run_table", "cross_check", "axis_tables",
    "show_source_matrix", "ENGINE", "LANGUAGE", "ROOT",
]
