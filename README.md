# Báo cáo khảo sát CP — OPL vs DOcplex.cp vs OR-Tools

So sánh cách triển khai Constraint Programming trên ba chiều, qua 6 bài toán.

📄 **Đọc bản đã dựng: https://dtnntd.github.io/cp-opl-docplex-ortools/**

Đặc tả nội dung nằm ở [`CP_report_brief.md`](CP_report_brief.md); kế hoạch thi công
và phân phối công việc nằm ở [`PLAN.md`](PLAN.md).

## Vì sao ba chiều

| Chiều | Ngôn ngữ mô hình | Engine giải |
|---|---|---|
| `opl` | OPL (`.mod`) | CP Optimizer (IBM) |
| `docplexcp` | Python — `docplex.cp` | CP Optimizer (IBM) |
| `ortools` | Python — `ortools.sat` | CP-SAT (Google) |

OPL và DOcplex.cp **chung engine** ⇒ so hai chiều này cô lập được khác biệt do
**ngôn ngữ**. DOcplex.cp và OR-Tools **chung ngôn ngữ** ⇒ so hai chiều này cô lập
được khác biệt do **engine**. So thẳng OPL với OR-Tools không tách được hai loại
khác biệt đó vì chúng khác nhau cả hai yếu tố cùng lúc.

Báo cáo chỉ đụng tới nhánh CP. `docplex.mp` (Math Programming → engine CPLEX) là
paradigm khác và **không** được dùng ở bất kỳ đâu.

## Cài đặt

```bash
make setup     # thư viện Python
make check     # xác nhận cả ba engine gọi được
```

`make check` phải xanh cả ba dòng trước khi chạy tiếp.

### Yêu cầu ngoài pip

- **IBM ILOG CPLEX Optimization Studio** — cung cấp `oplrun` (chiều OPL) và
  `cpoptimizer` (engine cho chiều DOcplex.cp). `pip install docplex` **không** kèm
  solver; docplex chỉ là lớp mô hình hoá bằng Python.
- Máy này dùng bản **Community Edition 22.2 cài trên Windows**, gọi từ WSL qua
  interop. `tools/oplrun.sh` lo việc dịch đường dẫn Linux → Windows;
  `tools/cpo_env.py` lo việc trỏ docplex.cp sang `cpoptimizer.exe`.
- Cài ở đường dẫn khác thì đặt biến môi trường `CPLEX_STUDIO_DIR` hoặc
  `CPOPTIMIZER_EXEC`.

> **Giới hạn Community Edition:** CP Optimizer chỉ nhận bài có không gian tìm kiếm
> tới 2^1000. Với mã hoá nhị phân, con số đó bằng đúng số biến bool. Các mô hình
> trong dự án vì thế ưu tiên biến nguyên miền nhỏ. Xem `PLAN.md` §Ràng buộc.

## Chạy

```bash
make run P=models/2.1_jobshop   # ba chiều của một bài
make run-all                    # cả 6 bài × 3 chiều -> results/
make bench                      # đo hiệu năng bài 3.2
make html                       # chạy notebook và xuất report/html/
make pages                      # đẩy report/html/ lên nhánh gh-pages
```

`make pages` ghi đè nhánh `gh-pages` bằng `report/html/` hiện tại. Nhánh đó rời
khỏi `main` và chỉ chứa HTML đã dựng, nên `main` không bao giờ lẫn file build.

## Bố cục

```
data/          dữ liệu dùng CHUNG cho cả ba chiều của mỗi bài
models/<bài>/  opl/ · docplexcp/ · ortools/ · manifest.json · NOTES.md
notebooks/     5 notebook: intro + 3 phần + tổng hợp
report/        script build và HTML xuất ra
results/       số liệu chạy được (json/csv)
tools/         oplrun.sh · cpo_env.py · runner.py · check_env.py
vendor/docplex ví dụ CP chính thức của IBM (sparse clone, chỉ examples/cp)
```

### Hai quy ước khiến mọi thứ khớp nhau

**1. Mỗi bài một `manifest.json`** — khai báo cho từng chiều: file model, tham số,
và nguồn gốc (`official` = lấy mẫu chính thức, `new` = viết mới). Runner và
notebook đọc chung file này, nên bảng ✅/✍️ trong báo cáo luôn khớp code thật.

**2. Mọi model in ra một dòng `RESULT {json}`** ở cuối:

```
RESULT {"status": "Feasible", "objective": 55, "solve_time_s": 0.31, "branches": 440, "fails": 198}
```

Nhờ vậy `tools/runner.py` thu số liệu đồng nhất, thay vì phải đọc ba định dạng log
khác nhau của hai engine.

> Lưu ý khi đọc số liệu: `fails` của CP Optimizer và `conflicts` của CP-SAT đếm
> hai thứ khác nhau, **không so trực tiếp với nhau được**. CP-SAT lại chạy đa
> luồng nên số liệu đổi giữa các lần chạy — phần benchmark cố định số worker và
> seed để tái lập được.
