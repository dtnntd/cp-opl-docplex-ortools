# Chạy báo cáo này trên Google Colab

Colab là máy Linux x86-64 không có IBM ILOG CPLEX Optimization Studio và không có
WSL interop. Hai chiều `opl` và `docplexcp` đều dựa vào binary của IBM, nên câu hỏi
"đẩy notebook lên Colab thì chạy được tới đâu" quy về đúng một câu: **có cách nào
lấy engine CP Optimizer trên Linux mà không cài CPLEX Studio không?**

Câu trả lời, sau khi kiểm chứng bằng một venv sạch: **không.**

## Kết luận ngắn

| Thành phần báo cáo | Trên Colab |
|---|---|
| Văn xuôi, phân loại ràng buộc, mô hình toán, code hiển thị (`show_notes`, `show_code`, `show_dimension_code`, `show_source_matrix`) | **100%** — chỉ đọc file trong repo |
| Ô số liệu chạy thật (6 bài × 3 chiều) | **6/18 = 33%** — chỉ cột `ortools` |
| Bản phụ trợ `companion` bài 3.1 (`docplexcp_portA`) | 0/1 |
| Benchmark bài 3.2 (`make bench`, 3 chiều × 3 cấu hình) | 1/3 chiều |
| **Bảng trục NGÔN NGỮ** (OPL vs DOcplex.cp) | **0** — cần cả hai engine IBM |
| **Bảng trục ENGINE** (CP Optimizer vs CP-SAT) | **0** — cần chiều `docplexcp` |

Nói cho gọn: **Colab dựng lại được toàn bộ phần trình bày và đúng một phần ba số
liệu, nhưng không dựng lại được bất kỳ phép so sánh nào.** Cả hai trục so sánh —
tức lý do tồn tại của báo cáo, xem `README.md` §"Vì sao ba chiều" — đều đi qua
engine CP Optimizer. Mất engine đó là mất cả hai trục, còn lại một cột số liệu
OR-Tools đứng một mình không so với gì.

Trừ khi tự cài CPLEX Studio bản Linux vào Colab. Đường đó còn sống, xem §"Ba đường
vòng còn lại" bên dưới.

## Chiều nào sống, chiều nào chết

| Chiều | Colab | Lý do |
|---|---|---|
| `ortools` | ✅ **được** | `pip install ortools` mang theo luôn engine CP-SAT dưới dạng thư viện native trong chính wheel. Không cần gì ngoài pip. |
| `docplexcp` | ❌ **không** | `pip install docplex` chỉ là lớp mô hình hoá bằng Python. Không gói PyPI nào của IBM ship binary `cpoptimizer` hay `lib_cpo_solver_*.so` cho Linux — đã kiểm bằng cách liệt kê từng file trong wheel, xem §dưới. |
| `opl` | ❌ **không** | `oplrun` chỉ đi kèm CPLEX Studio, không có bản pip nào. Gói `doopl` trên PyPI (giao diện Python cho OPL) dừng ở phiên bản 12.10.0.26 năm 2019, chỉ có wheel tới `cp37`, và wheel Linux nặng 294 KB — nghĩa là **không** chứa engine (wheel Windows cùng phiên bản nặng 25 MB). Colab chạy Python ≥ 3.11 nên gói này còn không cài được. |

## Bằng chứng: không có engine CP Optimizer nào lấy được qua pip

Kiểm trong venv sạch, Python 3.11, Linux x86-64, cài `ortools docplex cplex`:

**1. Wheel `cplex` 22.2.0.1 (bản Community trên PyPI) không chứa CP Optimizer.**
Toàn bộ file nhị phân trong gói 31 MB đó là hai file, và cả hai là engine *math
programming*:

```
cplex/_internal/libcplex2220.so       ← thư viện CPLEX Callable Library (LP/MIP)
cplex/_internal/py311_cplex2220.so    ← binding Python
```

`find site-packages -iname '*cpoptimizer*'` trả về **rỗng**. Không có file thực thi
nào (`find -type f -executable` ngoài `.so`/`.py`: rỗng). Mô tả gói trên PyPI cũng
nói đúng phạm vi của nó: *"A Python interface to the CPLEX Callable Library"* — CP
Optimizer là engine khác, không nằm trong Callable Library.

**2. `docplex` 2.32.264 tự nói ra là nó thiếu gì.** Cấu hình mặc định sau khi cài:

```
context.solver.agent    = local
context.solver.local.execfile = cpoptimizer          ← tên trần, phải có sẵn trong PATH
context.solver.lib.libfile    = lib_cpo_solver_*.so  ← không có file nào khớp
```

Gọi `solve()` trên một model 8 biến `all_diff` cho ra:

```
# Solver executable file is not found !
# Please check that:
#  - you have installed IBM ILOG CPLEX Optimization Studio on your computer,
...
CpoException: Executable file 'cpoptimizer' does not exists
```

**3. Có một gói tên `docplex_cpo_solver` *thật sự* chứa thư viện engine — nhưng nó
không nằm trên PyPI.** `docplex/cp/config.py` (dòng 431–438) có sẵn móc để dùng nó:

```python
# Check if library has been installed with workers specific package
try:
    from docplex_cpo_solver import get_library_path
    lfile = get_library_path()
    if lfile:
        context.solver.lib.libfile = lfile
        context.solver.agent = 'lib'
except:
    pass
```

Đã thử `https://pypi.org/pypi/docplex-cpo-solver/json` và `docplex_cpo_solver` →
**404** cả hai. Gói đó chỉ được cài sẵn trong runtime worker của IBM Watson Studio
(cùng họ với `docplex_wml`, cũng 404 trên PyPI). Không lấy được từ ngoài.

**4. Không có gói thay thế nào.** `cpoptimizer`, `cp-optimizer`, `ibm-cpoptimizer`,
`docplex-cp`, `cplex-cp`, `ibm-cplex`, `cplex-community` — **404** toàn bộ trên PyPI.
`conda-forge` cũng không có gói `cplex` (404).

## Ô bootstrap dán vào Colab

Dán vào ô đầu tiên của notebook, chạy một lần:

```python
# --- Bootstrap Colab -------------------------------------------------------
import os, pathlib, subprocess, sys

REPO = "https://github.com/dtnntd/cp-opl-docplex-ortools.git"
DIR  = pathlib.Path("/content/cp")

if not DIR.exists():
    subprocess.run(["git", "clone", "--depth", "1", REPO, str(DIR)], check=True)

# 9.14 là bản đã sinh ra số liệu trong results/runs.json. KHÔNG dùng "ortools"
# trần — xem mục "Bẫy riêng của Colab" trong COLAB.md.
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "ortools==9.14.6206"], check=True)

# Notebook dùng đường dẫn TƯƠNG ĐỐI ("../tools", "../results/bench.csv") nên
# thư mục làm việc phải là notebooks/, trong khi Colab mặc định đứng ở /content.
os.chdir(DIR / "notebooks")
sys.path.insert(0, str(DIR / "tools"))

# Bỏ hai chiều không có engine trên Colab (cần patch ở mục "Đề xuất kỹ thuật").
os.environ["CP_DIMENSIONS"] = "ortools"

print("cwd =", os.getcwd())
subprocess.run([sys.executable, "../tools/check_env.py"])
```

`pandas`, `matplotlib`, `jinja2` và `IPython` đã có sẵn trong Colab nên không cần
cài — phần còn lại của `requirements.txt` chỉ phục vụ việc *xuất* HTML
(`jupyter`, `nbconvert`, `nbformat`), việc mà Colab không làm.

Không cài `docplex` cũng được: `nbutil.py` và `runner.py` không import nó, chỉ các
file trong `models/*/docplexcp/` mới import — và chúng sẽ không được gọi tới.

## Notebook hỏng như thế nào khi thiếu hai engine IBM

Tin tốt trước: **không có chỗ nào ném exception.** Đã chạy thử với
`CPLEX_STUDIO_DIR=/nonexistent CPOPTIMIZER_EXEC=/nonexistent/cpoptimizer` để giả
lập Colab, `run_table()` và `cross_check()` đều trả về bình thường. Lý do:

* `tools/oplrun.sh` kết thúc bằng `exit 127` khi không dò ra `oplrun`, chứ không
  phải bằng một file không tồn tại. `subprocess.run` trong `runner.py:182` vì thế
  chỉ nhận `returncode = 127`, không ném `FileNotFoundError`.
* Chiều `docplexcp` chạy model như một tiến trình con; `_resolve()` trong
  `tools/cpo_env.py` (dòng 137 và 151) ném `RuntimeError` **trong tiến trình con
  đó**, nên nó chỉ hoá thành exit code khác 0 ở tiến trình cha.
* `runner.py:224` — `rec.ok = code == 0 and _is_success(rec.status)` — biến cả hai
  trường hợp thành `ok=False`, `status=None`. Đúng một dòng FAIL, không hơn.

`make html` (tức `nbconvert --execute`) do đó **không** dừng giữa chừng vì hai
chiều IBM. Nó chạy hết và xuất ra một báo cáo trông vẫn "đầy đủ".

Đó chính là vấn đề. Hỏng theo kiểu im lặng nguy hiểm hơn hỏng theo kiểu ném lỗi.
Bốn chỗ cụ thể:

**(a) `nbutil.py:346–348` — dán nhãn engine thắng cho một chiều chưa hề chạy.**

```python
"engine nhanh hơn": (
    "CP-SAT" if (sat.solve_time_s or 0) < (cpo.solve_time_s or 0)
    else "CP Optimizer"),
```

`cpo.solve_time_s` là `None` khi chiều `docplexcp` không chạy được. `None or 0`
cho ra `0`, nên phép so thành `1.89 < 0` → `False` → cột ghi **"CP Optimizer"**.
Đã chạy thử và xác nhận: bảng trục engine tuyên bố CP Optimizer nhanh hơn ở cả hai
bài thử, trong khi CP Optimizer không chạy dòng nào. Đây là lỗi tiềm ẩn **trên mọi
máy**, không riêng Colab: chỉ cần một chiều FAIL là con số này thành sai.

**(b) `nbutil.py:282–283` — đổ lỗi nhầm cho mô hình.**

```
`opl` = None · `docplexcp` = None · `ortools` = 55 → ❌ **LỆCH — có lỗi trong mô hình**
```

Không có lỗi nào trong mô hình cả. Chỉ là thiếu engine. Thông điệp này gửi người
đọc đi sửa đúng thứ không hỏng.

**(c) `nbutil.py:264–267` — "cả ba" khi chỉ có một.** Với bài CSP thuần (1.1, 1.2)
câu chốt là *"✅ cả ba đều tìm được nghiệm khả thi"*, in nguyên văn ngay cả khi
nhóm chỉ còn một bản ghi. Con số "ba" được viết cứng trong chuỗi.

**(d) `notebooks/99_comparison.ipynb`, ô code cuối — chỗ DUY NHẤT ném exception
thật, và nó ném vì lý do khác:**

```python
b = pd.read_csv("../results/bench.csv")
```

`.gitignore` loại `results/*.csv`, nên **bản clone mới không có file này**.
`FileNotFoundError` → `nbconvert --execute` dừng ngay tại đó. Mà sinh lại nó cần
`make bench`, tức `tools/bench_timetable.py`, mà script này khai cứng cả ba chiều
trong `DIMENSIONS` (dòng 40–54) và **không đọc biến môi trường nào** — trên Colab
nó sẽ ghi ra một CSV mà hai phần ba số hàng là FAIL.

## Đề xuất kỹ thuật: biến môi trường `CP_DIMENSIONS`

Ý tưởng: cho phép **bỏ hẳn** chiều không có engine thay vì để nó chạy rồi FAIL.
Đây không phải chuyện thẩm mỹ — nó sửa được cả bốn chỗ trên bằng một chỗ, vì
`nbutil.py` **đã** xử lý đúng trường hợp bản ghi *vắng mặt*:

* `cross_check()` gặp nhóm chỉ có một phần tử → `nbutil.py:275` in
  *"⚠️ chỉ có một chiều, **không đối chiếu được**"* — đã là câu đúng, không cần sửa.
* `axis_tables()` có hai điều kiện canh cửa `if opl and cpo` / `if cpo and sat`
  (`nbutil.py:333`, `nbutil.py:339`) → không có bản ghi thì không sinh hàng, hai
  bảng trục ra **rỗng**, đúng sự thật. Đã kiểm: `frame([])` render ra bảng rỗng
  bình thường, không ném lỗi.

Nói cách khác, code hiện tại chỉ nói dối khi bản ghi **có mặt nhưng hỏng**. Vắng
mặt thì nó nói thật. Vậy chỉ cần đừng tạo bản ghi đó.

> **Chưa sửa file nào.** Bốn patch dưới đây để chủ dự án quyết. Patch 1 và 2 là
> phần lõi; patch 3 và 4 là phần dọn cho sạch.

### Patch 1 — `tools/runner.py`: đọc `CP_DIMENSIONS`

```diff
--- a/tools/runner.py
+++ b/tools/runner.py
@@ -30,6 +30,7 @@
 import argparse
 import json
+import os
 import pathlib
 import re
 import subprocess
@@ -55,6 +56,36 @@ LANGUAGE = {
 }
 
 _RESULT_RE = re.compile(r"^RESULT\s+(\{.*\})\s*$", re.MULTILINE)
+
+
+def enabled_dimensions() -> frozenset[str]:
+    """Các chiều được phép chạy trong phiên này.
+
+    Đặt biến môi trường `CP_DIMENSIONS` (ngăn bằng dấu phẩy) để bỏ chiều không có
+    engine trên máy đang chạy — ví dụ trên Google Colab, nơi không có CPLEX Studio
+    nên hai chiều dùng engine CP Optimizer đều vô nghĩa:
+
+        CP_DIMENSIONS=ortools
+
+    Không đặt biến này thì cả ba chiều đều chạy, y như trước.
+
+    Bỏ HẲN chiều khác với để nó chạy rồi FAIL: bản ghi FAIL vẫn lọt vào bảng với
+    `solve_time_s = None`, và `nbutil.axis_tables()` sẽ dựng cả một hàng so sánh
+    trên con số không tồn tại. Vắng mặt thì mọi hàm hạ nguồn tự bỏ qua đúng chỗ.
+    """
+    raw = os.environ.get("CP_DIMENSIONS", "").strip()
+    if not raw:
+        return frozenset(ENGINE)
+    names = frozenset(n.strip() for n in raw.split(",") if n.strip())
+    unknown = names - frozenset(ENGINE)
+    if unknown:
+        raise ValueError(
+            f"CP_DIMENSIONS có chiều không hợp lệ: {', '.join(sorted(unknown))} "
+            f"(chọn trong: {', '.join(sorted(ENGINE))})"
+        )
+    return names
+
+
+def skipped_dimensions() -> frozenset[str]:
+    """Các chiều bị `CP_DIMENSIONS` loại ra — dùng để in cảnh báo."""
+    return frozenset(ENGINE) - enabled_dimensions()
 
 #: Các giá trị `status` được tính là chạy thành công, so khớp không phân biệt hoa thường.
@@ -243,9 +274,10 @@ def run_suite(problem_dir, timeout: int = 600) -> list[RunRecord]:
     """Chạy mọi chiều khai báo trong manifest.json của một bài."""
     manifest = load_manifest(problem_dir)
+    enabled = enabled_dimensions()
     records: list[RunRecord] = []
     for dim, spec in manifest["dimensions"].items():
-        if spec.get("skip"):
+        if spec.get("skip") or dim not in enabled:
             continue
         records.append(
@@ -273,12 +305,13 @@ def run_companions(problem_dir, timeout: int = 600) -> list[RunRecord]:
     """
     manifest = load_manifest(problem_dir)
+    enabled = enabled_dimensions()
     records: list[RunRecord] = []
     for name, spec in manifest.get("companion", {}).items():
         if spec.get("skip"):
             continue
         # Tên bản phụ trợ có dạng "<chiều>_<hậu tố>", ví dụ "docplexcp_portA".
         dim = next((d for d in ENGINE if name.startswith(d)), None)
-        if dim is None:
+        if dim is None or dim not in enabled:
             continue
```

Thêm một dòng vào `_main()` để chạy CLI cũng nói ra chuyện đang lọc:

```diff
@@ -307,6 +340,10 @@ def _main() -> int:
     a = ap.parse_args()
 
+    if skipped_dimensions():
+        print(f"[CP_DIMENSIONS] bỏ qua chiều: "
+              f"{', '.join(sorted(skipped_dimensions()))}", file=sys.stderr)
+
     if a.all:
```

### Patch 2 — `tools/nbutil.py`: in cảnh báo, và đừng đoán engine thắng từ `None`

```diff
--- a/tools/nbutil.py
+++ b/tools/nbutil.py
@@ -27,7 +27,7 @@
 from runner import (ENGINE, LANGUAGE, ROOT, load_manifest, run_companions,
-                    run_suite)  # noqa: E402
+                    run_suite, skipped_dimensions)  # noqa: E402
 
 MODELS = ROOT / "models"
@@ -126,6 +126,9 @@
 _RUNS: dict[str, list] = {}
 
+#: Cảnh báo CP_DIMENSIONS chỉ in một lần cho cả notebook, không lặp mỗi bài.
+_WARNED_SKIP = False
+
 _SOURCE_MARK = {"official": "✅", "new": "✍️", "official+extended": "✅+✍️"}
@@ -186,6 +189,17 @@ def runs(problem: str, timeout: int = 900, refresh: bool = False) -> list:
     """
+    global _WARNED_SKIP
+    missing = skipped_dimensions()
+    if missing and not _WARNED_SKIP:
+        _WARNED_SKIP = True
+        print(
+            "⚠️  CP_DIMENSIONS đang lọc: KHÔNG chạy chiều "
+            + ", ".join(sorted(missing))
+            + ".\n    Mọi bảng dưới đây chỉ có số liệu của chiều còn lại; "
+              "hai bảng trục so sánh sẽ rỗng.\n"
+              "    Đây KHÔNG phải lỗi mô hình — máy này thiếu engine tương ứng "
+              "(xem COLAB.md)."
+        )
     if refresh or problem not in _RUNS:
```

```diff
@@ -300,6 +314,18 @@ def _ratio(a, b):
     return round(a / b, 2)
 
 
+def _faster(cpo_s, sat_s):
+    """Engine nào giải nhanh hơn — `None` khi thiếu số liệu.
+
+    KHÔNG được coi `None` là 0. Chiều không chạy được có `solve_time_s = None`,
+    và `(sat or 0) < (cpo or 0)` khi đó ra `False`, tức cột này dán nhãn
+    "CP Optimizer thắng" cho một chiều còn chưa hề khởi động. Thiếu số liệu thì
+    phải để trống, không được đoán.
+    """
+    if cpo_s is None or sat_s is None:
+        return None
+    return "CP-SAT" if sat_s < cpo_s else "CP Optimizer"
+
+
 def axis_tables(timeout: int = 900):
@@ -343,9 +369,7 @@ def axis_tables(timeout: int = 900):
                     "CP-SAT ít nhánh hơn": _ratio(cpo.branches, sat.branches),
-                    "engine nhanh hơn": (
-                        "CP-SAT" if (sat.solve_time_s or 0) < (cpo.solve_time_s or 0)
-                        else "CP Optimizer"),
+                    "engine nhanh hơn": _faster(cpo.solve_time_s, sat.solve_time_s),
                 })
```

### Patch 3 — `tools/nbutil.py`: bỏ con số "ba" viết cứng trong `cross_check()`

```diff
@@ -261,11 +...,11 @@ def cross_check(problem: str, timeout: int = 900):
             out.append(
                 f"{label}CSP thuần, không có hàm mục tiêu\n\n{detail} → "
-                + ("✅ cả ba đều tìm được nghiệm khả thi\n" if ran
+                + (f"✅ cả {len(group)} chiều đã chạy đều tìm được nghiệm khả thi\n" if ran
                    else "❌ **có chiều không ra nghiệm**\n")
                 + "\n> Không có giá trị mục tiêu để đối chiếu, nên phép kiểm ở đây chỉ "
-                  "xác nhận **cả ba đều tìm được nghiệm**. Tính hợp lệ của từng nghiệm "
+                  "xác nhận **mọi chiều đã chạy đều tìm được nghiệm**. Tính hợp lệ của từng nghiệm "
                   "do chính model tự kiểm lại theo dữ liệu gốc rồi báo qua `status`; "
```

Câu *"❌ LỆCH — có lỗi trong mô hình"* (`nbutil.py:282–283`) thì **không cần sửa**
sau Patch 1: khi chiều bị lọc, nhóm chỉ còn một bản ghi và nhánh `len(group) < 2`
ở dòng 274 bắt trước, in ra *"⚠️ chỉ có một chiều, không đối chiếu được"*.

### Patch 4 — `notebooks/99_comparison.ipynb`: đừng chết vì thiếu `bench.csv`

Ô code cuối, thay bằng:

```python
import pathlib
import pandas as pd

p = pathlib.Path("../results/bench.csv")
if not p.exists():
    print("Chưa có ../results/bench.csv — chạy `make bench` để sinh (cần đủ ba engine).")
else:
    b = pd.read_csv(p)
    display((b[b.ok].groupby(["config", "dimension", "engine", "encoding"], sort=False)
               [["objective", "solve_time_s", "branches", "fails"]].median().reset_index()))
```

`tools/bench_timetable.py` cũng nên lọc theo `enabled_dimensions()` trong vòng lặp
`for dim, spec in DIMENSIONS.items()` (dòng 77 và 118), nhưng benchmark một chiều
thì không còn là benchmark, nên trên Colab cứ để `make bench` đứng ngoài.

### Sau khi vá thì Colab ra cái gì

`CP_DIMENSIONS=ortools` sẽ cho:

* một dòng cảnh báo ở đầu, nói rõ đang thiếu chiều nào và vì sao;
* `run_table()` ra bảng một hàng, các cột đầy đủ số liệu thật;
* `cross_check()` ra *"⚠️ chỉ có một chiều, không đối chiếu được"* — trung thực;
* `axis_tables()` ra **hai bảng rỗng** — cũng trung thực, và nhìn phát biết ngay
  báo cáo dựng trên Colab không có phần so sánh.

Không có dòng ❌ giả nào, không có nhãn "CP Optimizer nhanh hơn" bịa ra.

## Bẫy riêng của Colab: `pip install ortools` mới nhất trả **sai** bài 3.1

Đây là phát hiện ngoài dự kiến, và nó là lý do ô bootstrap ghim phiên bản.

| Phiên bản | `models/3.1_sports/ortools/sports_sat.py` |
|---|---|
| `ortools==9.14.6206` (bản đã sinh `results/runs.json`) | `OPTIMAL`, objective **12** — khớp chiều OPL |
| `ortools==9.15.6755` (bản `pip install ortools` lấy về hôm nay) | **`INFEASIBLE`** trong 0.03 s |

Đã truy tới cùng:

1. Chặn lại lời gọi `CpSolver.solve()` ở cả hai phiên bản và dump `model.proto` ra
   text. Hai file **giống hệt nhau từng byte** (14 566 dòng, chỉ khác ký tự xuống
   dòng cuối file). Vậy không phải do lớp Python `cp_model` sinh model khác đi.
2. Chạy lại cùng model đó trên 9.15 với từng bộ tham số:

   | Tham số | Kết quả trên 9.15 |
   |---|---|
   | mặc định | `INFEASIBLE` |
   | `num_workers=1` | `INFEASIBLE` |
   | `num_workers=8` | `INFEASIBLE` |
   | **`cp_model_presolve=False`** | **`OPTIMAL`, obj 12** |
   | `num_workers=1, cp_model_presolve=False` | `OPTIMAL`, obj 12 |

Tắt presolve là hết. Đây là **lỗi tính đúng đắn (soundness) trong presolve của
CP-SAT 9.15.6755**: nó cắt mất nghiệm rồi tuyên bố bài vô nghiệm. Bài 3.1 dùng
`add_allowed_assignments` + `add_all_different` + `add_inverse` + `add_map_domain`
cùng lúc, tổ hợp đủ hiếm để lọt lưới hồi quy của Google.

Năm bài còn lại chạy đúng trên 9.15 (objective khớp `results/runs.json`: 55, 13,
47, và hai bài CSP đều `OPTIMAL`). Nhưng một ô sai trong bảng so sánh là đủ hỏng
báo cáo, nên: **ghim `ortools==9.14.6206`.**

Tiện thể, 9.15 còn đổi API theo cách phá tương thích: `cp_model.cp_model_pb2`
không còn được re-export, và `model.proto` giờ là đối tượng C++ (`copy_from` thay
cho `CopyFrom`). Code trong `models/` không đụng tới hai thứ này nên không ảnh
hưởng, nhưng nó cho thấy 9.15 không phải bản nâng cấp vá lỗi thuần tuý.

> Ghim phiên bản cũng đáng cân nhắc cho `requirements.txt` chứ không riêng Colab.
> Dòng hiện tại là `ortools>=9.14`, tức `make setup` trên máy sạch hôm nay sẽ kéo
> về đúng 9.15 và bài 3.1 sẽ FAIL. Chủ dự án quyết.

## Ba đường vòng còn lại cho chiều `docplexcp`

**1. IBM Watson Machine Learning / DOcplexcloud — chết một nửa.**
Dịch vụ *Decision Optimization on Cloud* (DOcplexcloud) **đã ngừng từ tháng 9/2020**.
Bằng chứng trực tiếp trong chính gói đã cài: `docplex` 2.32.264 **không còn một
dòng nào** nhắc tới `docloud` — không trong `docplex/cp/`, cũng không trong
`docplex/mp/`. Thư mục `docplex/cp/solver/` chỉ còn `solver_local.py`,
`solver_lib.py`, `solver_simulator.py` và `environment_client.py`. Agent giải qua
mạng đã bị gỡ khỏi thư viện, không phải chỉ ngừng phục vụ.

Bản thay thế là *DO on Watson Machine Learning*, vẫn sống, nhưng nó **không phải
là một agent của `docplex`**: nó bắt đóng gói model thành file zip, đẩy lên WML,
tạo deployment rồi tạo job. Kiến trúc của kho này là "mỗi model là một script độc
lập in ra một dòng `RESULT {json}`" (xem `README.md` §Hai quy ước) — ghép vào WML
là viết lại toàn bộ `tools/runner.py`, không phải đổi một biến môi trường. Ngoài
ra cần tài khoản IBM Cloud có phần Decision Optimization, tức không còn là "mở
Colab lên là chạy".

**2. IBM Academic Initiative — còn sống, nhưng không giải quyết được gì thêm.**
Sinh viên/giảng viên lấy được bản CPLEX Studio **đầy đủ** (không có trần
2^1000). Nhưng thứ nhận được vẫn là **một bộ cài**, không phải một gói pip — nên
nó rơi về đúng đường số 3 dưới đây, chỉ khác là bỏ được giới hạn Community.

**3. Cài CPLEX Studio bản Linux vào Colab bằng tay — đường khả thi nhất, và kho
này đã dọn sẵn chỗ cho nó.**

Điểm mấu chốt: hạ tầng trong `tools/` **đã có sẵn nhánh Linux**, chỉ thiếu file.

* `tools/oplrun.sh` dò `opl/bin/x86-64_linux/oplrun` **trước** bản `.exe` khi
  `uname -s` là `Linux`, và dò các gốc `/opt/ibm/ILOG`, `/opt/IBM/ILOG`,
  `$HOME/ibm/ILOG`, `$HOME/IBM/ILOG`.
* `tools/cpo_env.py` có `_arch_subdirs()` trả về
  `cpoptimizer/bin/x86-64_linux/cpoptimizer` khi `sys.platform == "linux"`, và
  `_base_dirs()` dò `/opt/ibm/ILOG`, `/opt/IBM/ILOG`, `$HOME/ibm/ILOG` với glob
  bắt mọi số hiệu phiên bản. Cả hai biến `CPOPTIMIZER_EXEC` và `CPLEX_STUDIO_DIR`
  đều được tôn trọng.

> Ghi chú: `tools/cpo_env.py` và `tools/oplrun.sh` vừa được viết lại cho đa nền
> tảng **trong lúc tôi khảo sát** (cây làm việc đang có thay đổi chưa commit so
> với `b229525`). Số dòng trích ở trên lấy theo bản trong cây làm việc, không
> phải bản đã commit. `tools/nbutil.py`, `tools/runner.py` và các notebook thì
> **không** bị đụng tới, nên mọi số dòng trích của ba thứ đó khớp cả hai bản.

Nghĩa là nếu bộ cài Linux nằm đúng chỗ đó thì **cả ba chiều sống lại trên Colab mà
không phải sửa một dòng code nào.** Cách làm: tải bộ cài `.bin` cho Linux từ trang
IBM (cần đăng nhập IBMid, nên không `wget` thẳng trong ô Colab được — phải để sẵn
trên Google Drive rồi `drive.mount`), chạy cài im lặng vào `/opt/ibm/ILOG/`, rồi
`make check`. Phải cài lại mỗi lần Colab cấp máy mới, và bản Community vẫn giữ
nguyên trần 2^1000 (tức bài 3.1 với n ≥ 8 vẫn bị từ chối, đúng như
`models/3.1_sports/manifest.json` §`community_edition_limit` đã ghi).

Lưu ý: người dùng đang có bộ cài **Windows** 22.2, và bộ cài đó không dùng cho
Linux được — phải tải riêng bản `linux_x86_64`. Cùng một tài khoản, khác file.

---

## Những gì tôi đã kiểm chứng thật

Venv sạch trong thư mục scratch, Python 3.11.2, Linux x86-64, không đụng vào
Python hệ thống và không đụng vào `requirements.txt`.

1. **`pip install ortools` là đủ cho chiều OR-Tools.** Đã chạy **cả 6** model
   `models/*/ortools/*.py` bằng interpreter của venv với đúng tham số trong
   `manifest.json`. Cả 6 in ra dòng `RESULT`, không thiếu phụ thuộc nào.
2. **Wheel `cplex` 22.2.0.1 không chứa CP Optimizer.** Đã liệt kê từng file trong
   gói; chỉ có `libcplex2220.so` và `py311_cplex2220.so`. `find -iname
   '*cpoptimizer*'` rỗng, `find -type f -executable` (trừ `.so`/`.py`) rỗng.
3. **`docplex` 2.32.264 không giải được gì trên Linux sạch.** Đã gọi `solve()`
   thật và nhận `CpoException: Executable file 'cpoptimizer' does not exists`.
   Đã in cấu hình đã resolve: `agent=local`, `execfile=cpoptimizer`,
   `libfile=lib_cpo_solver_*.so`, `ctypes.util.find_library('cpo_solver') → None`.
4. **Không gói PyPI nào lấp được chỗ đó.** `docplex-cpo-solver`,
   `docplex_cpo_solver`, `docplex-wml`, `cpoptimizer`, `cp-optimizer`,
   `ibm-cpoptimizer`, `docplex-cp`, `cplex-cp`, `cplexcp`, `ibm-cplex`,
   `cplex-community`, `cpo-solver` → HTTP **404** trên PyPI. `conda-forge/cplex`
   → 404.
5. **`doopl` tồn tại nhưng không dùng được.** Phiên bản cuối 12.10.0.26; wheel cao
   nhất là `cp37`; wheel `manylinux1_x86_64` nặng 294 KB so với 25 MB của wheel
   `win_amd64` — chênh lệch đó chính là engine, và bản Linux không có nó.
6. **`docloud` đã bị gỡ khỏi `docplex`.** `grep -rl docloud` trên cả
   `docplex/cp/` và `docplex/mp/` → không kết quả nào.
7. **Notebook không ném exception vì thiếu engine IBM.** Đã chạy `runner.run()`,
   `nbutil.run_table()`, `nbutil.cross_check()` với `CPLEX_STUDIO_DIR` và
   `CPOPTIMIZER_EXEC` trỏ vào đường dẫn không tồn tại. Kết quả: `ok=False,
   status=None`, không exception. Đã đọc nguyên văn output của `cross_check()`
   cho cả bài CSP và bài tối ưu, và tái lập được nhãn sai
   *"engine nhanh hơn = CP Optimizer"* ở `nbutil.py:346–348`.
8. **`results/bench.csv` bị `.gitignore` loại.** `git ls-files results/` chỉ trả
   về hai file `.png`. Ô cuối của `99_comparison.ipynb` đọc file này bằng
   `pd.read_csv` không có canh cửa.
9. **Lỗi hồi quy `ortools` 9.15.6755 ở bài 3.1.** Đã đối chiếu 9.14 vs 9.15 trên
   cùng một máy; đã dump và diff `model.proto` (giống hệt nhau); đã khoanh nguyên
   nhân vào presolve bằng cách chạy lại với `cp_model_presolve=False`. Năm bài còn
   lại khớp `results/runs.json` trên cả hai phiên bản.
10. **`frame([])` không ném lỗi** với pandas 3.0.5 + jinja2 — nên hai bảng trục
    rỗng sau khi vá là an toàn.

## Những gì chỉ là suy luận

Tách riêng, không trộn vào phần trên.

* **Colab có `pandas`/`matplotlib`/`jinja2`/`IPython` sẵn.** Đúng theo hiểu biết
  chung về ảnh Colab, nhưng tôi không có Colab để chạy thử. Nếu ô bootstrap báo
  thiếu, thêm vào lệnh `pip install`.
* **Thư mục làm việc mặc định của Colab là `/content`.** Ô bootstrap `os.chdir`
  dựa trên giả định này. Nếu Colab đã đổi hành vi thì `os.chdir` vẫn vô hại.
* **Phiên bản Python của Colab ≥ 3.11**, đủ để loại `doopl` (`cp37`). Kết luận về
  `doopl` không phụ thuộc vào con số này — wheel Linux của nó không chứa engine
  dù chạy trên Python nào.
* **Bộ cài CPLEX Studio Community bản Linux cài im lặng được vào Colab.** Tôi
  không tải được file cài (cần đăng nhập IBMid) nên **chưa chạy thử**. Điều tôi
  *đã* xác nhận là phía kho này đã sẵn sàng: `oplrun.sh` ưu tiên nhánh
  `x86-64_linux` và dò `/opt/ibm/ILOG`, `cpo_env.py:36` đã có đúng đường dẫn
  Linux. Việc bộ cài có chạy trót lọt trong sandbox Colab hay không là phần chưa
  kiểm.
* **Trần 2^1000 của Community Edition vẫn áp dụng cho bản Linux.** Suy ra từ chỗ
  giới hạn này gắn với giấy phép chứ không với nền tảng; đo trực tiếp thì cần bản
  Linux đã cài.
* **Bảng "6/18 ô = 33%".** Đếm theo số ô số liệu trong các bảng `run_table()`. Nếu
  đếm theo cách khác (số hình, số đoạn văn) thì tỉ lệ khác — nhưng con số quan
  trọng hơn là **0/2 bảng trục so sánh**, và con số đó không phụ thuộc cách đếm.
* **Lỗi presolve 9.15 là lỗi của Google chứ không phải của model.** Bằng chứng gián
  tiếp nhưng mạnh: `cp_model_presolve=False` cho ra đúng objective 12 mà chiều OPL
  độc lập cũng cho ra, và model proto không đổi giữa hai phiên bản. Tôi chưa rút
  gọn về một model tối thiểu để báo cáo ngược cho upstream.
