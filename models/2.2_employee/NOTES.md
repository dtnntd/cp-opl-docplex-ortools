# Bài 2.2 — Xếp ca nhân sự có nguyện vọng (Employee / Shift Scheduling with shift requests)

---

## (a) Phát biểu bài toán

Một đơn vị vận hành liên tục — bệnh viện, trung tâm trực, nhà máy ba ca — cần lập
lịch trực cho một kỳ. Kỳ gồm **7 ngày**, mỗi ngày chia thành **3 ca** (Morning,
Evening, Night). Đơn vị có **5 nhân viên**.

Yêu cầu vận hành:

- **Không được bỏ trống ca.** Mỗi ca của mỗi ngày phải có **đúng một** người trực.
  Không thiếu (bỏ trống thì dịch vụ đứt), cũng không thừa (thừa thì trả lương vô ích).
- **Không ai trực hai ca trong cùng một ngày.** Mỗi người nhận **tối đa một** ca mỗi ngày.
- **Chia việc công bằng.** Toàn kỳ có $7\times 3=21$ suất trực chia cho 5 người, tức
  4,2 suất/người — không chia chẵn được. Vậy mỗi người phải nhận trong khoảng
  $\lfloor 21/5\rfloor=4$ đến $\lceil 21/5\rceil=5$ suất. Không ai được rảnh cả
  tuần trong khi người khác trực gấp đôi.

Ngoài ba yêu cầu cứng đó, mỗi nhân viên nộp **nguyện vọng** (shift request): danh
sách những ca cụ thể mà họ *muốn* được xếp — vì tiện đi lại, vì lịch học, vì thích
ca đêm. Nguyện vọng là **mong muốn, không phải ràng buộc**: không đáp ứng được thì
lịch vẫn hợp lệ. Trong bộ dữ liệu này mỗi người nộp 4 nguyện vọng, tổng cộng 20.

> **Mục tiêu: xếp một lịch hợp lệ đáp ứng được NHIỀU nguyện vọng nhất.**

Đây là bài toán **rostering** kinh điển, và cũng là dạng bài mà brief §1 xếp vào ô
"tổ hợp/boolean nặng": toàn bộ quyết định là 105 câu hỏi có/không độc lập nhau, ràng
buộc đều là ràng buộc **đếm** trên các biến 0/1, không có thời lượng, không có trục
thời gian liên tục, không có tài nguyên tích luỹ. Không một biến interval nào xuất
hiện — khác hẳn bài 2.1 (job-shop) và bài 3.2 (timetable).

---

## (b) Mô hình toán học — DÙNG CHUNG cho cả ba chiều

> Cả ba chiều `opl`, `docplexcp`, `ortools` cài đặt **đúng mô hình dưới đây**, trên
> **đúng một file dữ liệu** `data/employee/employee.dat`. Không chiều nào thêm hay
> bớt một ràng buộc nào. Nhờ vậy mọi chênh lệch số liệu ở mục (d) chỉ có thể đến từ
> ngôn ngữ mô hình hoá hoặc từ engine, không đến từ mô hình.

### Tập hợp

| Ký hiệu | Ý nghĩa | Bộ dữ liệu này |
|---|---|---|
| $\mathcal{E}$ | tập nhân viên | $\{E_1,\dots,E_5\}$, $N=\lvert\mathcal{E}\rvert=5$ |
| $\mathcal{D}$ | tập ngày trong kỳ | $\{\text{Mon},\dots,\text{Sun}\}$, $\lvert\mathcal{D}\rvert=7$ |
| $\mathcal{S}$ | tập ca trong một ngày | $\{\text{Morning},\text{Evening},\text{Night}\}$, $\lvert\mathcal{S}\rvert=3$ |
| $\mathcal{R}\subseteq\mathcal{E}\times\mathcal{D}\times\mathcal{S}$ | tập **nguyện vọng**: $(e,d,s)\in\mathcal{R}$ nghĩa là nhân viên $e$ muốn làm ca $s$ ngày $d$ | $\lvert\mathcal{R}\rvert=20$ |

Gọi **suất trực** là một cặp $(d,s)\in\mathcal{D}\times\mathcal{S}$ — một ca cụ thể
của một ngày cụ thể. Tổng số suất trong kỳ:

$$\Sigma \;=\; \lvert\mathcal{D}\rvert\cdot\lvert\mathcal{S}\rvert \;=\; 7\cdot 3 \;=\; 21$$

### Tham số

| Ký hiệu | Định nghĩa | Bộ dữ liệu này |
|---|---|---|
| $r_{e,d,s}$ | chỉ báo nguyện vọng: $r_{e,d,s}=\mathbb{1}\bigl[(e,d,s)\in\mathcal{R}\bigr]$ | ma trận $5\times7\times3$, 20 ô bằng 1 |
| $L_{\min}$ | tải tối thiểu mỗi người $=\bigl\lfloor \Sigma/N \bigr\rfloor$ | $\lfloor 21/5\rfloor = 4$ |
| $L_{\max}$ | tải tối đa mỗi người $=\bigl\lceil \Sigma/N \bigr\rceil$ | $\lceil 21/5\rceil = 5$ |

Bản gốc của Google lưu $r$ ở dạng **dày** — mảng lồng ba tầng gồm 105 số 0/1. File
`.dat` dùng chung ở đây lưu ở dạng **thưa** — liệt kê 20 bộ ba thuộc $\mathcal{R}$.
Hai cách đồng nhất về toán học ($r_{e,d,s}=1 \iff (e,d,s)\in\mathcal{R}$); bản thưa
đọc được bằng mắt và hợp với cách OPL mô tả quan hệ bằng tuple set. Đã đối chiếu
từng ô trong 105 ô để chắc chắn không sai lệch.

### Biến quyết định

| Biến | Miền | Số lượng | Ý nghĩa |
|---|---|---|---|
| $x_{e,d,s}$ | $\{0,1\}$ | $N\cdot\lvert\mathcal{D}\rvert\cdot\lvert\mathcal{S}\rvert = 5\cdot7\cdot3 = \mathbf{105}$ | $x_{e,d,s}=1 \iff$ nhân viên $e$ trực ca $s$ trong ngày $d$ |

Đây là **toàn bộ** biến quyết định của mô hình — không có biến phụ, không có biến
interval, không có biến nguyên. Không gian tìm kiếm là $2^{105}$, thoải mái dưới
trần $2^{1000}$ của CPLEX Studio Community Edition (log CP Optimizer xác nhận:
*"Maximization problem — 105 variables, 70 constraints"*).

Đặt **tải** của nhân viên $e$ — số suất trực người đó nhận trong cả kỳ:

$$\ell_e \;=\; \sum_{d\in\mathcal{D}}\ \sum_{s\in\mathcal{S}} x_{e,d,s}$$

### Ràng buộc

**(C1) Mỗi suất trực do đúng một người đảm nhiệm.** Không bỏ trống, không xếp thừa.

$$\sum_{e\in\mathcal{E}} x_{e,d,s} \;=\; 1
\qquad \forall\, d\in\mathcal{D},\ \forall\, s\in\mathcal{S}
\tag{C1}$$

$\lvert\mathcal{D}\rvert\cdot\lvert\mathcal{S}\rvert = 21$ ràng buộc.

**(C2) Mỗi người trực tối đa một ca mỗi ngày.**

$$\sum_{s\in\mathcal{S}} x_{e,d,s} \;\le\; 1
\qquad \forall\, e\in\mathcal{E},\ \forall\, d\in\mathcal{D}
\tag{C2}$$

$N\cdot\lvert\mathcal{D}\rvert = 35$ ràng buộc. Chú ý (C2) là **bất đẳng thức**, không
phải đẳng thức: có ngày một người không trực ca nào, và điều đó bắt buộc phải xảy ra
vì $\lvert\mathcal{D}\rvert=7 > L_{\max}=5$.

**(C3)–(C4) Cân bằng tải.**

$$\ell_e \;\ge\; L_{\min} \qquad \forall\, e\in\mathcal{E} \tag{C3}$$

$$\ell_e \;\le\; L_{\max} \qquad \forall\, e\in\mathcal{E} \tag{C4}$$

$2N = 10$ ràng buộc.

### Hàm mục tiêu

$$\boxed{\ \max\ \; Z \;=\; \sum_{e\in\mathcal{E}}\sum_{d\in\mathcal{D}}\sum_{s\in\mathcal{S}}
r_{e,d,s}\, x_{e,d,s}
\;\;=\;\; \sum_{(e,d,s)\in\mathcal{R}} x_{e,d,s} \ }$$

Hai vế bằng nhau vì $r_{e,d,s}=0$ triệt tiêu mọi hạng tử ngoài $\mathcal{R}$. Vế
trái là cách viết của bản Google (quét cả lưới 105 ô); vế phải chạy thẳng trên tuple
set thưa (20 hạng tử). Chiều `opl` và `docplexcp` dùng vế phải, chiều `ortools` giữ
nguyên vế trái của bản chính thức.

### Ba hệ quả rút ra được từ mô hình

Ba tính chất dưới đây suy trực tiếp từ (C1)–(C4), không cần solver. Chúng vừa giải
thích lời giải, vừa là công cụ kiểm chứng độc lập ở mục (d).

**① Tổng tải luôn cố định, và số người phải làm thêm ca là xác định trước.**
Cộng (C1) trên mọi suất:

$$\sum_{e\in\mathcal{E}} \ell_e \;=\; \sum_{d,s}\ \sum_{e} x_{e,d,s} \;=\; \Sigma \;=\; 21$$

Kết hợp với (C3)–(C4): nếu gọi $k$ là số nhân viên nhận $L_{\max}$ suất thì
$k\,L_{\max} + (N-k)L_{\min} = \Sigma$, suy ra

$$k \;=\; \Sigma - N\!\cdot\!L_{\min} \;=\; \Sigma \bmod N \;=\; 21 \bmod 5 \;=\; 1$$

Nghĩa là **đúng một** người nhận 5 suất, bốn người còn lại nhận 4 suất — biết trước
mà không cần giải. Cả ba chiều đều in ra đúng như vậy; đây là phép thử đầu tiên xem
bản cài đặt có trung thực không.

**② Ràng buộc cân bằng luôn khả thi.** Vì $N L_{\min}\le \Sigma\le N L_{\max}$ theo
đúng định nghĩa sàn/trần, (C3)–(C4) không bao giờ mâu thuẫn với (C1). Bài luôn có
nghiệm khả thi, nên mọi chiều bắt buộc phải trả về `Optimal`, không bao giờ
`Infeasible`.

**③ Chặn trên chặt của hàm mục tiêu — và ở bộ dữ liệu này nó CHÍNH LÀ tối ưu.**
Theo (C1), mỗi suất $(d,s)$ chỉ có một người trực, nên **mỗi suất đáp ứng được nhiều
nhất một nguyện vọng**, bất kể có bao nhiêu người cùng xin suất đó. Vậy

$$Z \;\le\; \Bigl\lvert\ \bigl\{\,(d,s)\;:\;\exists e,\ (e,d,s)\in\mathcal{R}\,\bigr\}\ \Bigr\rvert$$

Đếm trên bộ dữ liệu này: 20 nguyện vọng chỉ rơi vào **13 suất khác nhau** — 6 suất bị
tranh chấp, trong đó `<Sat, Evening>` có tới 3 người cùng xin (E1, E3, E5), còn
`<Mon,Night>`, `<Sun,Night>`, `<Wed,Evening>`, `<Thu,Evening>`, `<Fri,Morning>` mỗi
suất 2 người. Do đó

$$Z^\star \;\le\; 13$$

Cả ba chiều đều đạt $Z^\star = 13$ ⇒ **chặn trên khít, và 13 là tối ưu — chứng minh
được bằng tay, độc lập hoàn toàn với mọi solver.** Bảy nguyện vọng bị bỏ không phải
vì mô hình xếp kém, mà vì bảy người đó xin trùng suất với người khác; không lịch nào
đáp ứng nổi. (Chặn trên từ phía nhân viên — $\sum_e \min(\lvert\mathcal{R}_e\rvert,
L_{\max}, \#\text{ngày }e\text{ xin})$ — cho 20, tức là rất lỏng; chặn từ phía suất
mới là chặn có ích.)

---

## (c) Nguồn từng chiều

| Chiều | Ngôn ngữ | Engine | Nguồn | File |
|---|---|---|---|---|
| `ortools` | Python (`ortools.sat`) | CP-SAT | ✅ **LẤY MẪU CHÍNH THỨC** — [developers.google.com/optimization/scheduling/employee_scheduling](https://developers.google.com/optimization/scheduling/employee_scheduling), phần *"Scheduling with shift requests"* (`schedule_requests_sat.py`, Apache 2.0) | `ortools/employee_sat.py` |
| `opl` | OPL | CP Optimizer | ✍️ **VIẾT MỚI** — IBM không có bản CP nào cho bài này | `opl/employee.mod` |
| `docplexcp` | Python (`docplex.cp`) | CP Optimizer | ✍️ **VIẾT MỚI** — IBM không có bản CP nào cho bài này | `docplexcp/employee_cp.py` |

Phần dựng mô hình của chiều `ortools` giữ **nguyên văn** bản Google — cùng biến, cùng
lời gọi API, cùng thứ tự ràng buộc, cùng hàm mục tiêu, giữ cả comment tiếng Anh gốc.
Chỉ ba thứ được thêm, tất cả nằm ngoài khối mô hình: đọc dữ liệu từ `.dat` dùng chung
thay vì mảng viết cứng, cố định `num_search_workers=1` + `random_seed=0`, và in dòng
`RESULT`.

Dữ liệu `data/employee/employee.dat` là bản chép **đúng từng ô** bảng
`shift_requests` của Google (5 nhân viên × 7 ngày × 3 ca, 20 nguyện vọng), chỉ đổi từ
dạng dày sang dạng thưa. Đã kiểm chứng bằng cách bung ngược file `.dat` thành mảng
$5\times7\times3$ rồi so bằng `==` với mảng gốc chép từ trang Google: **khớp tuyệt đối**.

### Chứng minh: IBM KHÔNG có bản CP nào cho bài xếp ca nhân sự

Đây là một **khoảng trống của hệ IBM**, và là một kết luận của báo cáo. Có tồn tại
ví dụ `nurses` mang tên rất giống bài này ở cả hai sản phẩm của IBM, nhưng **cả hai
đều là MILP, chạy trên engine CPLEX qua `docplex.mp` / context CPLEX của OPL — khác
paradigm hoàn toàn**. Dưới đây là bằng chứng đã tự kiểm chứng trên máy.

#### Bằng chứng 1 — bộ ví dụ OPL của CPLEX Studio 22.2

Thư mục `/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222/opl/examples/opl/`:

| Đại lượng | Giá trị |
|---|---|
| Tổng số file `.mod` | **184** |
| Số file `.mod` có `using CP;` (tức là chạy trên CP Optimizer) | **76** |
| Trong 76 file CP đó, số file về xếp ca nhân sự / nurse / roster / staff | **0** |

Có duy nhất một ví dụ mang tên `nurses/` — và nó **không** nằm trong 76 file CP:

```
$ grep -c "^using" nurses/nurses.mod
0                       # KHÔNG có dòng `using CP;` ⇒ rơi vào context CPLEX
```

Chính IBM ghi rõ paradigm trong file dự án `nurses/.oplproject`:

```xml
<description>Nurses Scheduling model, MIP</description>
```

Và `nurses.mod` khai **biến liên tục** — thứ mà CP Optimizer không có khái niệm:

```opl
dvar float+ NurseWorkTime[Nurses];          // dòng 83
dvar float+ NurseAvgHours;                  // dòng 84
dvar float+ NurseMoreThanAvgHours[Nurses];  // dòng 85
dvar float+ NurseLessThanAvgHours[Nurses];  // dòng 86
dvar float+ Fairness;                       // dòng 87
```

#### Bằng chứng 2 — chạy thật, hai lần

Không dừng ở việc đọc code. Chạy `nurses.mod` nguyên bản bằng `oplrun`, engine tự khai báo mình:

```
*** FATAL[ENGINE_002]: Exception from IBM ILOG CPLEX: CPLEX Error 1016:
    Community Edition. Problem size limits exceeded.
```

Ngoại lệ đến từ **CPLEX**, không phải CP Optimizer. Và **mã lỗi tự phân biệt hai
engine** — đây là phép thử đối chứng: lấy đúng `employee.mod` của dự án (có
`using CP;`) rồi phóng dữ liệu lên 20 nhân viên × 30 ngày × 3 ca = 1 800 biến bool,
vượt trần $2^{1000}$:

```
*** FATAL[ENGINE_001]: Exception from IBM ILOG Concert: Problem size limit exceeded.
```

| File | Trần bị chạm | Mã lỗi | Engine tự khai |
|---|---|---|---|
| `employee.mod` của dự án (`using CP;`), 1 800 biến | $2^{1000}$ | `FATAL[ENGINE_001]` | **CP Optimizer** (Concert) |
| `nurses.mod` của IBM (không `using`), bộ gốc | 1 000 biến / 1 000 ràng buộc | `FATAL[ENGINE_002]` | **CPLEX** |

Hai mã lỗi khác nhau, hai loại trần khác nhau ⇒ hai engine khác nhau, xác nhận bằng
thực nghiệm chứ không chỉ bằng đọc code.

Rồi thử **ép** nó sang CP bằng cách chèn `using CP;` vào dòng đầu:

```
*** ERROR at 84:1-35 nurses_forceCP.mod:
    Decision variables of type dvar float+ not supported by this algorithm.
    ... (lặp lại ở dòng 85, 86, 87, 88)
### OPL exception: Impossible to load model.
```

⇒ `nurses.mod` **không chỉ tình cờ chạy trên CPLEX — nó KHÔNG THỂ chạy trên CP
Optimizer.** Mô hình được thiết kế quanh biến liên tục và mục tiêu tuyến tính, tức là
quanh quy hoạch tuyến tính, chứ không quanh lan truyền ràng buộc. Đây không phải "cùng
một bài viết bằng cú pháp khác", mà là **một paradigm khác**.

#### Bằng chứng 3 — kho ví dụ chính thức của DOcplex

Kho `IBMDecisionOptimization/docplex` (commit `ccb884b9`, 2026-07-02), tra toàn bộ cây
git chứ không chỉ phần đã sparse-checkout:

```
$ git ls-tree -r HEAD --name-only | grep -iE "nurse|roster|shift|employee"
docs/mp/nurses.html                              docs/mp/nurses_multiobj.html
docs/mp/nurses_pandas.html                       docs/mp/nurses_scheduling.html
docs/mp/_images/nurses_*.png            (5 file)
examples/mp/jupyter/nurses_data.xls
examples/mp/jupyter/nurses_pandas.ipynb          examples/mp/jupyter/nurses_scheduling.ipynb
examples/mp/jupyter/nurses_pandas-multi_objective.ipynb
examples/mp/modeling/nurses.py                   examples/mp/modeling/nurses_multiobj.py
```

**Toàn bộ 15 kết quả đều nằm dưới `mp/`.** Lọc riêng nhánh CP:

```
$ git ls-tree -r HEAD --name-only | grep '^examples/cp/' | grep -iE "nurse|roster|shift|employee"
(không có kết quả)
```

`examples/cp/` có **107 file** — job-shop, house building, steel mill, sports
scheduling, truck fleet, sudoku, golomb ruler… — và **không một file nào** về xếp ca
nhân sự. Còn `examples/mp/modeling/nurses.py` mở đầu bằng:

```python
from docplex.mp.model import Model      # dòng 9 — Math Programming, KHÔNG phải docplex.cp
```

#### Kết luận của mục (c)

**IBM cung cấp bài xếp ca nhân sự ở CẢ HAI sản phẩm, nhưng CHỈ dưới dạng MILP** —
`nurses.mod` (OPL → engine CPLEX) và `examples/mp/modeling/nurses.py`
(`docplex.mp` → engine CPLEX). Bản CP thì không tồn tại ở đâu cả, dù CP Optimizer có
tới 76 ví dụ OPL và 107 ví dụ Python.

Điều đó khiến bài 2.2 **đối xứng ngược với bài 3.2** trong báo cáo, và hai bài cộng
lại vẽ đúng bản đồ thế mạnh của hai hệ sinh thái:

| | IBM có sẵn bản CP? | Google có sẵn bản CP? |
|---|---|---|
| **3.2 Timetable** (interval, min makespan) | ✅ `timetabling.mod` — bản OPL đầy đủ, giàu ràng buộc | ❌ không có |
| **2.2 Employee** (boolean, max nguyện vọng) | ❌ chỉ có MILP | ✅ có, là ví dụ hướng dẫn tiêu biểu |

IBM đầu tư ví dụ CP vào lớp bài **lập lịch có thời lượng** — nơi biến interval và
`no_overlap` phát huy; còn lớp bài **phân công boolean thuần** thì IBM mặc định đưa
sang MILP. Google đi hướng ngược lại: CP-SAT lấy chính bài rostering boolean làm ví
dụ hướng dẫn đầu bảng. Sự phân công đó không ngẫu nhiên — nó phản chiếu đúng cấu
trúc dữ liệu lõi của hai engine, và mục (d) đo được điều đó bằng số.

**Hệ quả cho `docplex.mp`:** ràng buộc "tuyệt đối không dùng `docplex.mp`" của dự án
khiến bài này **bắt buộc** phải viết mới hai chiều IBM. Không có đường tắt nào, và
đó chính là điều đáng nói.

---

## (d) Quan sát so sánh

### Kiểm chứng chéo — điều kiện tiên quyết

Ba chiều dựng độc lập, ba ngôn ngữ, hai engine, cùng một file dữ liệu:

| Chiều | Engine | Objective | Kết luận optimality |
|---|---|---|---|
| `opl` | CP Optimizer | **13** / 20 | `Optimal` (best bound = 13, gap 0.00%) |
| `docplexcp` | CP Optimizer | **13** / 20 | `Optimal` |
| `ortools` | CP-SAT | **13** / 20 | `OPTIMAL` |
| *chặn trên tính bằng tay* — mục (b)③ | — | **≤ 13** | khít |

Bốn nguồn độc lập cùng ra 13, trong đó nguồn thứ tư **không dùng solver nào**. Đây là
mức kiểm chứng chặt hơn hẳn bài 3.2 (chỉ đối chiếu solver với solver).

Ba chiều trả về **ba lịch khác nhau** — riêng ngày thứ Hai đã đủ phân biệt cả ba:

| Ca thứ Hai | `opl` | `docplexcp` | `ortools` |
|---|---|---|---|
| Morning | E2 | E2 | **E5** |
| Evening | E3 | E3 | E3 |
| Night | E4 | **E1** | E4 |

(người nhận 5 suất cũng lệch: E3, E3, E4). Đó là bình thường và đúng kỳ vọng: bài
có rất nhiều nghiệm tối ưu vì các nhân viên đối xứng với nhau ở mọi suất không ai xin.
Thứ phải trùng là **giá trị mục tiêu**, không phải lời giải cụ thể — và nó trùng.

Cả ba đều in đúng: một người 5 suất, bốn người 4 suất — khớp hệ quả ① ở mục (b).

### Số liệu — tất cả đều tái lập được

Cả ba chiều cố định **1 worker + seed 0** (PLAN.md §2.4). Chạy lại 3 lần: `branches`
và `fails` giống hệt từng con số, chỉ `solve_time_s` dao động ở hàng phần nghìn giây.

| Chiều | Ngôn ngữ | Engine | Obj | Thời gian giải | Nhánh | Fails / Conflicts |
|---|---|---|---|---|---|---|
| `opl` | OPL | CP Optimizer | 13 | 0,015 s | 1 133 | 354 |
| `docplexcp` | Python `docplex.cp` | CP Optimizer | 13 | 0,013 s | 1 325 | 418 |
| `ortools` | Python `ortools.sat` | CP-SAT | 13 | **0,0055 s** | **254** | **0** |

Quy mô: **105 biến bool**, không gian tìm kiếm $2^{105}$ — thoải mái dưới trần
$2^{1000}$ của Community Edition. Mô hình có $21+35+10=66$ ràng buộc theo (C1)–(C4);
log CP Optimizer báo `105 variables, 70 constraints` — chênh 4 là do bước trích xuất
của OPL, không phải do mô hình thêm ràng buộc nào.

> Nhắc lại quy ước của README: cột cuối là `fails` với CP Optimizer và `conflicts`
> với CP-SAT — **hai đại lượng đếm hai thứ khác nhau**, chỉ so được trong cùng một
> engine. Cột `branches` thì so được vì cả hai đều đếm điểm rẽ nhánh.

---

### Trục NGÔN NGỮ — OPL vs DOcplex.cp, cùng engine CP Optimizer

Cùng engine, cùng mô hình toán, cùng dữ liệu, cùng 1 worker và cùng seed. Mà:

| | OPL | DOcplex.cp | chênh |
|---|---|---|---|
| Nhánh | 1 133 | 1 325 | **+17 %** |
| Fails | 354 | 418 | +18 % |

**Nguyên nhân đã truy ra và kiểm chứng bằng thí nghiệm: thứ tự biến được nạp xuống
engine.**

OPL khai báo cả 105 biến trong **một dòng**, và thứ tự là thứ tự khai báo:

```opl
dvar boolean x[Employees][Days][Shifts];      // (e, d, s)
```

Python không có kiểu "mảng đánh chỉ số bằng tập hợp", nên `docplex.cp` phải dựng dict:

```python
x = {(e, dd, s): mdl.binary_var(name=f"x_{e}_{dd}_{s}") for e in employees for dd in days for s in shifts}
```

Dict được tạo theo thứ tự $(e,d,s)$ — nhưng **`docplex.cp` không nạp biến theo thứ tự
tạo**. Nó chỉ đẩy một biến xuống engine khi biến đó **xuất hiện lần đầu trong một ràng
buộc**. Ràng buộc đầu tiên là (C1), duyệt theo $(d,s)$ rồi mới tới $e$ — nên file `.cpo`
sinh ra bắt đầu bằng:

```
x_E1_Mon_Morning = intVar(0, 1);
x_E2_Mon_Morning = intVar(0, 1);      // <- thứ tự (d, s, e), KHÁC bản OPL
x_E3_Mon_Morning = intVar(0, 1);
```

Thứ tự biến là đầu vào của heuristic chọn biến mặc định của CP Optimizer, nên nó đổi
cây tìm kiếm. **Thí nghiệm xác nhận** — chỉ hoán vị thứ tự *post* ba nhóm ràng buộc
trong bản `docplex.cp`, không đổi một ký tự nào của mô hình toán:

| Thứ tự post ràng buộc | Thứ tự biến vào engine | Nhánh | Fails |
|---|---|---|---|
| C1 → C2 → C3 (bản đang dùng) | $(d,s,e)$ | 1 325 | 418 |
| C2 → C1 → C3 | $(e,d,s)$ — **trùng OPL** | **1 118** | 343 |
| C3 → C1 → C2 | $(e,d,s)$ — **trùng OPL** | **1 118** | 343 |
| *(chiều OPL để đối chiếu)* | $(e,d,s)$ | *1 133* | *354* |

Hễ ép `docplex.cp` nạp biến theo đúng thứ tự $(e,d,s)$ của OPL, con số tụt từ 1 325 về
1 118 — sát ngay bản OPL (1 133). Chênh lệch 17 % biến mất.

> **Kết luận trục ngôn ngữ.** Ở bài này hai ngôn ngữ diễn đạt được mô hình toán *y hệt
> nhau* — không như bài 1.2 nơi `allDifferent` của OPL từ chối mảng biểu thức và ép
> phải thêm biến phụ. Nhưng chúng vẫn không đưa **cùng một bài toán** xuống engine: OPL
> cố định thứ tự biến bằng câu lệnh khai báo, `docplex.cp` để thứ tự đó **rơi ra như
> tác dụng phụ của thứ tự viết ràng buộc**. Một lựa chọn mà lập trình viên Python không
> hề biết mình đang thực hiện lại đáng giá 17 % số nhánh. Đây là dạng khác biệt ngôn
> ngữ **tinh vi hơn** trường hợp N-Queens: ở đó ngôn ngữ chặn ta viết một thứ; ở đây
> ngôn ngữ vẫn cho viết đúng, chỉ âm thầm đổi thứ tự.

**Một cái bẫy nữa của OPL, đã đo được.** Khối `execute` của OPL **không đọc được
`dexpr`**. Muốn in giá trị mục tiêu vào dòng `RESULT`, phản xạ tự nhiên là vật chất hoá
mục tiêu thành một `dvar` phụ rồi `maximize` biến đó:

```opl
dvar int met in 0..card(ShiftRequests);
maximize met;
subject to { met == sum(<e,d,s> in ShiftRequests) x[e][d][s];  ... }
```

Chạy được, ra đúng 13 — nhưng **đắt hơn**:

| Bản OPL | Nhánh | Fails |
|---|---|---|
| `maximize` thẳng tổng thưa, đọc kết quả bằng `cp.getObjValue()` | **1 133** | **354** |
| thêm `dvar met` + ràng buộc `met == …` (tổng thưa) | 1 586 | 586 |
| thêm `dvar met` + ràng buộc `met == …` (tổng dày 105 ô) | 1 583 | 572 |

**+40 % số nhánh** cho một biến phụ tồn tại thuần tuý vì hạn chế của tầng scripting.
Hai dòng cuối gần như trùng nhau ⇒ thủ phạm là **biến phụ**, không phải cách viết tổng.
Bản giao nộp dùng `cp.getObjValue()` nên không phải trả giá này. Cùng một họ hiện tượng
với bài 1.2 (440 nhánh với biến phụ so với 255 khi không cần), và cùng một bài học:
**trong OPL, mọi thứ phải nhìn thấy từ `execute` đều có nguy cơ trở thành biến quyết
định, và biến quyết định thì không bao giờ miễn phí.**

---

### Trục ENGINE — DOcplex.cp vs OR-Tools, cùng ngôn ngữ Python

Cùng ngôn ngữ, cùng mô hình toán, cùng dữ liệu, cùng 1 worker và cùng seed:

| | DOcplex.cp / CP Optimizer | OR-Tools / CP-SAT | tỉ lệ |
|---|---|---|---|
| Thời gian giải | 0,013 s | **0,0055 s** | **2,4× nhanh hơn** |
| Nhánh | 1 325 | **254** | **5,2× ít hơn** |
| Fails / Conflicts | 418 | **0** | — |

**Con số đáng nói nhất là số 0.** CP-SAT chứng minh tối ưu mà **không quay lui lần
nào**: presolve + lan truyền mệnh đề đủ để đóng bài. 254 nhánh còn lại là các bước gán
không hề vấp. Trong khi đó CP Optimizer vấp 418 lần trên đúng bài đó.

Vì sao? Vì bài này là **bài boolean thuần**, và hai engine có hai bộ ràng buộc lõi khác nhau.

**CP-SAT có, CP Optimizer không có.** Hai ràng buộc trong (C1), (C2) chính là hai
nguyên hàm boolean của SAT:

```python
model.add_exactly_one(shifts[(n, d, s)] for n in all_nurses)   # (C1)
model.add_at_most_one(shifts[(n, d, s)] for s in all_shifts)   # (C2)
```

CP-SAT nạp thẳng chúng thành **mệnh đề CNF** và giao cho bộ máy CDCL của chính nó —
lan truyền đơn vị, học mệnh đề xung đột, nhảy lùi không thời gian. Đây là sân nhà.

`docplex.cp` **không có API tương đương ở tầng boolean**. Danh mục ràng buộc toàn cục
của CP Optimizer — `all_diff`, `count`, `pack`, `sequence`, `no_overlap`, `alternative`,
`forbid_extent` — hướng tới biến **miền rời rạc** và biến **interval**. Ràng buộc "đúng
một trong các biến bool này bằng 1" phải viết thành **tổng số học**:

```python
mdl.add(mdl.sum(x[e, dd, s] for e in employees) == 1)          # (C1)
mdl.add(mdl.sum(x[e, dd, s] for s in shifts) <= 1)             # (C2)
```

Engine nhận về một ràng buộc **số học tuyến tính trên biến $\{0,1\}$**, và lan truyền nó
bằng suy luận khoảng trên tổng chứ không bằng suy luận mệnh đề. Đúng đắn như nhau,
nhưng yếu hơn hẳn: nó không sinh ra được **lời giải thích cho xung đột**, nên không học
được gì từ 418 lần thất bại — mỗi lần vấp là phải quay lui thời gian, không tích luỹ.

**Đối chiếu ngược với bài 3.2 mới thấy hết ý nghĩa.** Ở đó, chính CP Optimizer là bên
có primitive mà CP-SAT thiếu — `alternative` để chọn tài nguyên, `forbid_extent` để khai
báo lịch bận không tốn một biến quyết định nào; CP-SAT phải bung tay thành literal hiện
diện và phép tuyển, và trên bộ `large` nó thua 0,67 s so với 2,52 s. Ở bài 2.2 thì
ngược hẳn chiều.

| | Bài 3.2 (interval, min makespan) | Bài 2.2 (boolean, max nguyện vọng) |
|---|---|---|
| Primitive quyết định | `alternative`, `forbid_extent`, `no_overlap` | `add_exactly_one`, `add_at_most_one` |
| Bên có sẵn primitive | **CP Optimizer** | **CP-SAT** |
| Bên phải dựng tay | CP-SAT (literal hiện diện, phép tuyển) | CP Optimizer (tổng số học) |
| Bên thắng, bộ lớn nhất | CP Optimizer (0,67 s vs 2,52 s) | **CP-SAT (0,0055 s vs 0,013 s; 0 xung đột)** |

> **Kết luận trục engine.** Số liệu **xác nhận** nhận định của brief §1: bài tổ hợp /
> boolean nặng là sở trường của CP-SAT, và ở đây nó thắng ở cả ba cột — nhanh hơn 2,4×,
> ít nhánh hơn 5,2×, và không quay lui lần nào. Nhưng kết luận đúng **không phải**
> "CP-SAT mạnh hơn CP Optimizer". Đặt bài 2.2 cạnh bài 3.2 thì thấy rõ: mỗi engine
> thắng đúng ở lớp bài mà **cấu trúc dữ liệu lõi của nó phục vụ** — CDCL trên mệnh đề
> với CP-SAT, thuật toán lan truyền trên interval với CP Optimizer. Và điều đó khớp
> chính xác với thứ tìm được ở mục (c): IBM không thèm phát hành ví dụ CP cho bài xếp
> ca boolean, còn Google lại lấy chính nó làm bài hướng dẫn đầu bảng. **Chỗ trống trong
> kho ví dụ và chỗ yếu trong số liệu benchmark chỉ về cùng một hướng.**

**Cảnh báo về quy mô.** Bộ dữ liệu này rất nhỏ (105 biến, cả ba chiều xong dưới 20 ms),
nên tỉ lệ 2,4× đo trên thang phần nghìn giây, đủ để nêu xu hướng nhưng không nên ngoại
suy. Điểm vững chắc và không phụ thuộc quy mô là **0 conflicts** so với **418 fails**:
đó là khác biệt về *cách chứng minh tối ưu*, không phải về tốc độ đồng hồ. Bài duy nhất
có benchmark định lượng đầy đủ trong báo cáo vẫn là 3.2 (PLAN.md §1).

---

## Chạy

```bash
make run P=models/2.2_employee                 # cả ba chiều
python3 tools/runner.py --suite models/2.2_employee

# từng chiều
tools/oplrun.sh models/2.2_employee/opl/employee.mod data/employee/employee.dat
python3 models/2.2_employee/docplexcp/employee_cp.py data/employee/employee.dat
python3 models/2.2_employee/ortools/employee_sat.py  data/employee/employee.dat
```

Kết quả mong đợi ở cả ba chiều: `status` tối ưu, `objective = 13`.
