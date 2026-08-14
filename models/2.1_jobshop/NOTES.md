# Bài 2.1 — Job-shop scheduling (instance ft06)

> **Bài so sánh trọng tâm của báo cáo.** Đây là bài DUY NHẤT trong sáu bài có sẵn
> cả ba bản chính thức cho cùng một mô hình toán: IBM phát hành bản OPL
> (`sched_jobshop.mod`), IBM phát hành bản DOcplex.cp (`job_shop_basic.py`), và
> cách mã hoá interval cho CP-SAT thì Google có tài liệu hướng dẫn riêng. Nhờ vậy
> phép so sánh ở đây là **sạch nhất**: không có chỗ nào để đổ cho "tại người viết
> mô hình khác nhau".

---

## (a) Phát biểu bài toán

Có $n$ **job** (đơn hàng) phải gia công trên $m$ **máy**.

- Mỗi job gồm đúng $m$ **công đoạn** (operation), phải làm **theo đúng thứ tự đã
  định trước** — công đoạn sau chỉ được bắt đầu khi công đoạn trước đã xong. Thứ
  tự này gọi là *thứ tự công nghệ* (technological order) và là dữ liệu vào, không
  phải biến.
- Công đoạn thứ $o$ của job $j$ phải chạy trên đúng **một máy đã chỉ định** trong
  đúng **một khoảng thời gian đã biết**. Trong job-shop cổ điển, mỗi job đi qua
  **mỗi máy đúng một lần**.
- Một máy **chỉ gia công một công đoạn tại một thời điểm**.
- Công đoạn **không được ngắt quãng** (no preemption): đã khởi động thì chạy liền
  một mạch tới khi xong.
- Thời gian **không giới hạn trần**: mọi lịch đều khả thi nếu xếp tuần tự. Bài
  toán vì thế luôn có nghiệm — cái khó nằm ở chỗ **tối ưu**.

**Mục tiêu:** cực tiểu **makespan** — thời điểm công đoạn cuối cùng của toàn bộ
xưởng kết thúc.

Điều phải quyết định chỉ có một thứ: **thứ tự các công đoạn trên từng máy**. Khi
thứ tự đó đã chốt thì thời điểm bắt đầu sớm nhất tính được ngay. Đây là lý do
job-shop được xếp vào lớp **disjunctive scheduling**: mọi ràng buộc khó đều có
dạng "hoặc $A$ trước $B$, hoặc $B$ trước $A$".

### Instance dùng trong bài: `ft06`

`ft06` là instance chuẩn của Fisher & Thompson (1963), $6\times 6$, có mặt trong
mọi bộ benchmark job-shop (OR-Library). **Makespan tối ưu đã biết: 55.** Con số
này biến bài thành một **phép thử đúng/sai tuyệt đối** cho cả ba chiều — chạy ra
55 thì mô hình đúng, ra khác 55 thì mô hình sai, không phải bàn thêm.

| Đại lượng | Giá trị |
|---|---|
| Số job × số máy | $6\times 6$ = 36 công đoạn |
| Tổng thời gian gia công | 197 |
| Tải từng máy $M_0..M_5$ | 40, 26, 26, 22, 40, 43 |
| Tải từng job $J_0..J_5$ | 26, 47, 34, 35, 25, 30 |
| Chặn dưới tầm thường $\max(\max_m L_m,\ \max_j P_j)$ | **47** |
| Tối ưu thật | **55** |
| Số lịch tích cực tối đa $(n!)^m$ | $720^6 \approx 1.39\times10^{17} = 2^{56.95}$ |

Hai điều rút ra từ bảng: (1) chặn dưới tầm thường **cách tối ưu 8 đơn vị**, tức
instance không tầm thường — đây chính là lý do ft06 sống dai trong tài liệu suốt
60 năm; (2) không gian tìm kiếm $2^{57}$ nằm **rất sâu dưới trần $2^{1000}$** của
CPLEX Studio Community Edition, nên bài này không vướng giới hạn giấy phép
(xem `PLAN.md` §2.1).

---

## (b) Mô hình toán học — DÙNG CHUNG cho cả ba chiều

> Mô hình dưới đây mô tả đúng những gì cả ba bản cài đặt làm. Cả ba dùng **cùng
> một cách mã hoá — biến interval** — nên khác với bài 3.2 (nơi ba chiều mã hoá
> ba kiểu), ở bài này biến số duy nhất bị đổi là **ngôn ngữ** rồi **engine**.

### Tập hợp

| Ký hiệu | Ý nghĩa |
|---|---|
| $\mathcal{J}=\{0,\dots,n-1\}$ | tập job |
| $\mathcal{M}=\{0,\dots,m-1\}$ | tập máy |
| $\mathcal{O}=\{0,\dots,m-1\}$ | vị trí công đoạn trong một job (job-shop cổ điển: mỗi job có đúng $m$ công đoạn) |
| $\mathcal{I}=\mathcal{J}\times\mathcal{O}$ | tập **công đoạn**; phần tử $i=(j,o)$ |
| $\mathcal{I}_m=\{\,i\in\mathcal{I}\ :\ \mu_i=m\,\}$ | các công đoạn chạy trên máy $m$ |

### Tham số

| Ký hiệu | Miền | Ý nghĩa |
|---|---|---|
| $\mu_{j,o}$ | $\mathcal{M}$ | máy thực hiện công đoạn thứ $o$ của job $j$ |
| $p_{j,o}$ | $\mathbb{Z}_{>0}$ | thời gian gia công công đoạn đó |
| $H$ | $\mathbb{Z}_{>0}$ | horizon, chặn trên hiển nhiên của makespan |

Ràng buộc trên **dữ liệu vào** (không phải ràng buộc của mô hình): với mỗi
$j\in\mathcal{J}$, ánh xạ $o\mapsto\mu_{j,o}$ là **song ánh** $\mathcal{O}\to\mathcal{M}$
— mỗi job đi qua mỗi máy đúng một lần. Hệ quả: $|\mathcal{I}_m| = n$ với mọi máy $m$.

$$H \;=\; \sum_{j\in\mathcal{J}}\sum_{o\in\mathcal{O}} p_{j,o}
\qquad(\text{xếp tuần tự mọi công đoạn thì chắc chắn xong trước } H)$$

Với ft06: $n=m=6$, $H=197$.

### Biến quyết định

Biến chính của bài này là **biến interval** ($\texttt{intervalVar}$ trong CP
Optimizer, $\texttt{new\_interval\_var}$ trong CP-SAT) — một kiểu biến **không có
trong lập trình tuyến tính** và là đặc sản của CP dành cho lập lịch. Một biến
interval $x_i$ đại diện cho **cả một khoảng thời gian** $[\sigma_i,\eta_i)$ chứ
không phải một con số, và mang sẵn ba đại lượng liên kết:

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $x_{j,o}$ | **interval** | công đoạn $(j,o)$, coi như một khối đặc trên trục thời gian |
| $\sigma_{j,o}=\operatorname{startOf}(x_{j,o})$ | $\{0,\dots,H\}$ | thời điểm bắt đầu |
| $\eta_{j,o}=\operatorname{endOf}(x_{j,o})$ | $\{0,\dots,H\}$ | thời điểm kết thúc (hở phải) |
| $\pi_m$ | **sequence** trên $\mathcal{I}_m$ | thứ tự các công đoạn trên máy $m$ (một hoán vị của $\mathcal{I}_m$) |
| $\omega$ | $\{0,\dots,H\}$ | makespan |

Ba ghi chú về khai báo biến — đều là nét đặc trưng của CP:

1. **Kích thước dán thẳng vào khai báo biến.** Cả ba chiều khai báo
   $x_{j,o}$ với `size` $=p_{j,o}$, nên ràng buộc "công đoạn dài đúng $p$ và
   không ngắt quãng" **đã nằm trong kiểu của biến**, không cần viết ra. Giống hệt
   thủ pháp đã gặp ở bài 3.2 khi thu miền của $\theta_i$ về $\mathcal{T}_{s_i}$.
2. **$\pi_m$ là biến hoán vị, không phải biến số.** OPL khai báo nó tường minh
   (`dvar sequence`); hai chiều Python để engine tự sinh khi gặp `no_overlap`.
   Mô hình toán viết ra ở đây để nói rõ *cái đang được quyết định thực chất là gì*.
3. **Máy KHÔNG phải biến.** $\mu_{j,o}$ là tham số. Đây là điểm phân biệt job-shop
   cổ điển với *flexible* job-shop (nơi máy trở thành biến, và cần
   `alternative`/optional interval như bài 3.2 dùng).

### Ràng buộc

**(C1) Cấu trúc của biến interval** — khai báo `size` đã bao hàm:

$$\eta_{j,o} \;=\; \sigma_{j,o} + p_{j,o}
\qquad \forall (j,o)\in\mathcal{I}$$

**(C2) Thứ tự công nghệ trong từng job** (*precedence* — `endBeforeStart`):

$$\eta_{j,o} \;\le\; \sigma_{j,\,o+1}
\qquad \forall j\in\mathcal{J},\ \forall o\in\{0,\dots,m-2\}
\tag{C2}$$

Đọc là: *công đoạn $o$ phải KẾT THÚC trước khi công đoạn $o+1$ BẮT ĐẦU.* Cả ba
chiều sinh đúng $n(m-1)=30$ ràng buộc loại này cho ft06.

**(C3) Một máy chỉ chạy một công đoạn tại một thời điểm** (*no-overlap*):

$$[\sigma_i,\eta_i)\ \cap\ [\sigma_{i'},\eta_{i'}) \;=\; \varnothing
\qquad \forall m\in\mathcal{M},\ \forall i\ne i' \in \mathcal{I}_m
\tag{C3}$$

Dạng **tuyển** (đây là chỗ sinh ra độ khó của bài toán):

$$\bigl(\eta_i \le \sigma_{i'}\bigr)\ \ \vee\ \ \bigl(\eta_{i'} \le \sigma_i\bigr)
\qquad \forall m,\ \forall i\ne i'\in\mathcal{I}_m
\tag{C3$'$}$$

Với ft06 có $m\cdot\binom{n}{2} = 6\cdot 15 = 90$ cặp tuyển như vậy — tức
$2^{90}$ tổ hợp hướng nếu duyệt mù. Cả ba chiều **không** viết (C3′) ra thành
tuyển: chúng gọi ràng buộc toàn cục `noOverlap` / `no_overlap` / `add_no_overlap`,
để engine tự cài thuật toán lan truyền chuyên dụng (edge-finding, not-first/not-last).
Đây chính là điểm mạnh của CP so với MILP ở lớp bài này.

Dạng tương đương qua biến thứ tự $\pi_m$ — cách OPL nhìn (C3):

$$\pi_m\ \text{là một hoán vị của } \mathcal{I}_m, \qquad
\eta_{\pi_m(k)} \le \sigma_{\pi_m(k+1)}\quad \forall k
\tag{C3$''$}$$

**(C4) Định nghĩa makespan.** Nhờ (C2), công đoạn cuối của mỗi job cũng là công
đoạn kết thúc muộn nhất của job đó, nên chỉ cần lấy max trên $m-1$:

$$\omega \;=\; \max_{j\in\mathcal{J}}\ \eta_{j,\,m-1}
\tag{C4}$$

**(C5) Miền:**

$$\sigma_{j,o}\ \ge\ 0 \qquad \forall (j,o)\in\mathcal{I}
\tag{C5}$$

### Hàm mục tiêu

$$\boxed{\ \min\ \omega\ }$$

### Chặn dưới hợp lệ (không cài đặt, dùng để kiểm chứng)

$$\omega \ \ge\ \max\Bigl(\ \max_{m\in\mathcal{M}} \sum_{i\in\mathcal{I}_m} p_i,\ \
\max_{j\in\mathcal{J}} \sum_{o\in\mathcal{O}} p_{j,o}\ \Bigr)$$

Vế đầu: máy $m$ phải chạy hết tải của nó mà không chồng lấn (C3). Vế sau: job $j$
phải chạy hết chuỗi công đoạn của nó một cách tuần tự (C2). Với ft06 chặn này
bằng **47**, còn tối ưu là **55** — cho thấy phần khó thật sự nằm ở **tương tác**
giữa (C2) và (C3), thứ mà không chặn dưới đơn lẻ nào bắt được.

### Bảng đối chiếu: mô hình toán ↔ ba chiều cài đặt

| | OPL | DOcplex.cp | OR-Tools |
|---|---|---|---|
| $x_{j,o}$ | `dvar interval itvs[j][o] size Ops[j][o].pt` | `interval_var(size=DURATION[j][m])` | `new_interval_var(s, d, e, name)` |
| $\pi_m$ | `dvar sequence mchs[m] in all(...)` | *(ngầm, do `no_overlap` sinh)* | *(ngầm, do `add_no_overlap` sinh)* |
| (C2) | `endBeforeStart(itvs[j][o], itvs[j][o+1])` | `end_before_start(op[j][s-1], op[j][s])` | `model.add(start[j,o] >= end[j,o-1])` |
| (C3) | `noOverlap(mchs[m])` | `no_overlap(mops)` | `add_no_overlap([...])` |
| (C4)+mục tiêu | `minimize max(j in Jobs) endOf(itvs[j][nbMchs-1])` | `minimize(max(end_of(...)))` | `add_max_equality(mk, [...])` + `minimize(mk)` |
| (C5)/horizon | ngầm (miền mặc định của interval) | ngầm | **tường minh**: `new_int_var(0, H-d, ...)` |

---

## (c) Nguồn từng chiều

| Chiều | Nguồn | Trạng thái | Đường dẫn |
|---|---|---|---|
| `opl` | IBM CPLEX Studio 22.2, `opl/examples/opl/sched_jobshop/sched_jobshop.mod` — *Licensed Materials, Copyright IBM Corporation 1998, 2026* | ✅ **lấy mẫu chính thức** | [`opl/sched_jobshop.mod`](opl/sched_jobshop.mod) |
| `docplexcp` | IBM `docplex` examples, `examples/cp/visu/job_shop_basic.py` — *Apache License 2.0, (c) Copyright IBM Corp. 2015, 2022* | ✅ **lấy mẫu chính thức** | [`docplexcp/jobshop_cp.py`](docplexcp/jobshop_cp.py) · gốc ở [`vendor/docplex/examples/cp/visu/job_shop_basic.py`](../../vendor/docplex/examples/cp/visu/job_shop_basic.py) |
| `ortools` | ✍️ **viết mới**, theo đúng cách mã hoá của tài liệu Google [Job Shop Problem](https://developers.google.com/optimization/scheduling/job_shop) | ✍️ viết mới | [`ortools/jobshop_sat.py`](ortools/jobshop_sat.py) |

### Hai chiều lấy mẫu: đã đổi những gì

Phần **dựng mô hình** của cả hai bản chính thức được giữ **nguyên văn** — biến,
ràng buộc, hàm mục tiêu không đụng tới một ký tự. Chỉ bổ sung phần vỏ:

| Chiều | Thêm | Vì sao |
|---|---|---|
| `opl` | khối `execute EMIT_RESULT` ở cuối | giao kèo `RESULT {json}` của `tools/runner.py` |
| `opl` | đổi file dữ liệu → `data/jobshop/ft06.dat` | dữ liệu dùng chung, xem dưới |
| `docplexcp` | `import cpo_env` | trỏ docplex.cp sang `cpoptimizer.exe` cục bộ |
| `docplexcp` | đọc `.dat` dùng chung thay cho `jobshop_ft06.data` | dữ liệu dùng chung |
| `docplexcp` | Gantt bằng matplotlib thay cho `docplex.cp.utils_visu` | `utils_visu` cần môi trường đồ hoạ tương tác, không chạy được khi gọi qua runner |
| `docplexcp` | gọi `builtins.max` / `builtins.round` ở phần đọc kết quả | xem bẫy ngôn ngữ ở mục (d) |
| `ortools` | — | viết mới hoàn toàn |

Vì sao chiều OR-Tools phải viết mới dù Google có tài liệu: bản hướng dẫn của
Google **nhúng cứng** một instance $3\times3$ ngay trong mã nguồn và không có
đường đọc file. Nó không dùng lại được cho instance dùng chung. Cách mã hoá
(`new_interval_var` + `add_no_overlap` + `add_max_equality`) thì giữ đúng như tài
liệu khuyến nghị.

### Dữ liệu dùng chung — phần quan trọng nhất của bài này

Hai bản mẫu chính thức **đi kèm hai instance KHÁC NHAU**, và ở hai định dạng khác
nhau. Đã kiểm chứng bằng cách chạy thật:

| Nguồn | Định dạng | Kích thước | Công đoạn đầu của job 0 | Makespan tối ưu |
|---|---|---|---|---|
| `sched_jobshop.dat` (IBM OPL) | cú pháp `.dat` của OPL: `Ops = [[<mch,pt>, ...], ...]` | 6×6 | `<5,4>` — máy 5, dài 4 | **45** |
| `jobshop_ft06.data` (IBM docplex) | OR-Library: dòng đầu `n m`, mỗi dòng sau là các cặp `mch pt` | 6×6 | `2 1` — máy 2, dài 1 | **55** |

⇒ Hai instance 6×6 **khác hẳn nhau**. Nếu để nguyên thì chiều OPL giải một bài,
chiều DOcplex.cp giải bài khác, và mọi so sánh trong bài đều vô nghĩa.

**Quyết định: cả ba chiều chạy `ft06`.** Lý do:

1. `ft06` là instance **có tên trong tài liệu**, tối ưu 55 được công bố độc lập ⇒
   có mốc đúng/sai từ bên ngoài, không phải tự ta khẳng định với chính mình.
   Instance mặc định của IBM không có tên, không có mốc đối chiếu nào.
2. Nó là instance mà **bản DOcplex.cp chính thức đang dùng sẵn** ⇒ giữ được tối
   đa tính "nguyên bản" cho một trong hai chiều lấy mẫu.
3. Nó nằm trong bộ ft06/ft10/ft20 ⇒ muốn phóng to bài sau này chỉ cần đổi file.

**Cài đặt.** Có đúng **một** file dữ liệu: [`data/jobshop/ft06.dat`](../../data/jobshop/ft06.dat),
viết bằng cú pháp `.dat` của OPL (để chiều OPL đọc được nguyên trạng, không phải
sửa dòng khai báo nào của bản IBM), sinh tự động từ `jobshop_ft06.data` nên không
có khả năng sai lệch khi chép tay. Hai chiều Python đọc lại **chính file đó** qua
[`jobshop_data.py`](jobshop_data.py). Không tồn tại bản dữ liệu thứ hai để mà lệch.

> `tools/opl_dat.py` — trình đọc `.dat` dùng chung của dự án — hiện chỉ hỗ trợ tập
> hợp `{ ... }`, chưa hỗ trợ **mảng lồng** `[[<a,b>, ...], ...]` mà bài này cần.
> `jobshop_data.py` bù đúng phần đó, phạm vi gói trong bài 2.1. Xem phần tổng kết
> để biết đề xuất gộp lên `tools/`.

---

## (d) Quan sát so sánh

Tất cả số liệu dưới đây đo trên cùng instance `ft06`, cùng máy, cùng lời giải tối
ưu **55**. Lệnh tái lập: `make run P=models/2.1_jobshop`.

### Kiểm chứng chéo — điều kiện cần trước mọi so sánh

| Chiều | Ngôn ngữ | Engine | Makespan | Trạng thái |
|---|---|---|---|---|
| `opl` | OPL | CP Optimizer | **55** | Optimal (đã chứng minh) |
| `docplexcp` | Python `docplex.cp` | CP Optimizer | **55** | Optimal (đã chứng minh) |
| `ortools` | Python `ortools.sat` | CP-SAT | **55** | OPTIMAL |

Cả ba khớp đúng giá trị tối ưu đã công bố của ft06. Thêm một chi tiết đáng chú ý:
hai chiều CP Optimizer trả về **cùng một lịch, từng con số trùng khít**:

```
5  6 16 30 42 49        <- OPL và DOcplex.cp cho ma trận start giống hệt nhau
0  8 13 28 38 48
0  5  9 18 27 38
8 13 22 27 30 45
13 22 25 38 48 52
13 16 19 28 45 49
```

Chiều OR-Tools ra **một lịch khác**, cùng makespan 55 — đúng như kỳ vọng: bài có
nhiều nghiệm tối ưu, hai engine duyệt theo hai thứ tự khác nhau nên chạm nghiệm
khác nhau. Đây là bằng chứng thêm rằng ba bản là ba cài đặt độc lập chứ không
phải chép của nhau.

### Số liệu

| Chiều | Ngôn ngữ | Engine | Obj | Thời gian giải | Nhánh | Fails / Conflicts |
|---|---|---|---|---|---|---|
| `opl` | OPL | CP Optimizer | 55 | 0,051 s | 140 843 | 4 636 |
| `docplexcp` | Python (docplex.cp) | CP Optimizer | 55 | 0,039 s | 141 455 | 4 653 |
| `ortools` | Python (ortools.sat) | CP-SAT | 55 | **0,011 s** | **219** | 3 |

Trung vị 3 lần chạy. Hai chiều CP Optimizer **tất định tuyệt đối** (ba lần chạy
ra đúng cùng số nhánh). Chiều CP-SAT chạy với `num_workers=1`, `random_seed=42`
để tái lập được — xem cảnh báo ở cuối mục.

---

### Trục NGÔN NGỮ — OPL vs DOcplex.cp (cùng engine CP Optimizer)

| | OPL | DOcplex.cp | chênh lệch |
|---|---|---|---|
| Nhánh | 140 843 | 141 455 | **+0,43 %** |
| Fails | 4 636 | 4 653 | +0,37 % |
| Thời gian giải | 0,051 s | 0,039 s | — |

**Kết luận: ở bài này, ngôn ngữ gần như KHÔNG ảnh hưởng gì.** Chênh lệch dưới nửa
phần trăm, và lời giải trả về trùng khít từng con số. Hai bản viết bằng hai ngôn
ngữ khác hẳn nhau nhưng **dịch xuống cùng một mô hình engine**.

Đối chiếu với **bài 1.2 N-Queens**, cũng cùng engine CP Optimizer:

| Bài | OPL (nhánh/fails) | DOcplex.cp (nhánh/fails) | Chênh |
|---|---|---|---|
| 1.2 N-Queens n=8 | 440 / 198 | 255 / 99 | **~73 %** |
| 2.1 Job-shop ft06 | 140 843 / 4 636 | 141 455 / 4 653 | **0,4 %** |

Hai kết quả trái ngược này **không mâu thuẫn** — chúng chỉ ra đúng điều kiện để
ngôn ngữ trở thành yếu tố quyết định:

> Ngôn ngữ chỉ làm đổi số liệu khi nó **ép ta viết một mô hình toán khác**.

Ở bài 1.2, `allDifferent` của OPL không nhận mảng biểu thức, nên bản OPL buộc
phải vật chất hoá hai đường chéo thành `dvar` phụ — **thêm 2n biến quyết định**,
tức engine nhận về một bài toán khác thật. Ở bài 2.1, mọi thứ OPL viết đều có
tương ứng một-một trong `docplex.cp`, không phải thêm biến nào, nên engine nhận
về **đúng cùng một bài**.

**Khác biệt cú pháp duy nhất đáng kể** ở bài này nằm ở `dvar sequence`:

```opl
// OPL — một câu lệnh: lọc theo điều kiện + gom nhóm + tạo biến thứ tự
dvar sequence mchs[m in Mchs] in all(j in Jobs, o in Mchs : Ops[j][o].mch == m) itvs[j][o];
forall (m in Mchs) noOverlap(mchs[m]);
```

```python
# DOcplex.cp — không có cú pháp khai báo tương ứng, phải gom nhóm bằng vòng lặp
machine_operations = [[] for m in range(NB_MACHINES)]
for j in range(NB_JOBS):
    for s in range(NB_MACHINES):
        machine_operations[MACHINES[j][s]].append(job_operations[j][s])
for mops in machine_operations:
    mdl.add(no_overlap(mops))
```

OPL có bộ **comprehension trên biến quyết định** (`all(... : điều kiện)`) ngay
trong ngôn ngữ, còn `sequence` là một **kiểu dữ liệu hạng nhất**. Bản Python phải
tự dựng danh sách. Nhưng — và đây mới là điểm — **cả hai đều sinh ra đúng một
ràng buộc `noOverlap` cho mỗi máy**, nên khác biệt dừng lại ở mức *dễ đọc / dễ
viết*, không lan xuống tới engine.

**Bẫy ngôn ngữ của bản DOcplex.cp.** Bản mẫu IBM mở đầu bằng
`from docplex.cp.model import *`, và lệnh này **che mất các hàm dựng sẵn của
Python**: `max`, `min`, `sum`, `abs`, `round` đều bị thay bằng hàm dựng *biểu
thức* của docplex. Trong khối mô hình đó chính là điều ta muốn —
`max(end_of(...) for ...)` phải sinh ra một `CpoExpr` chứ không phải tính ngay.
Nhưng ở phần đọc kết quả thì `round(t, 4)` báo lỗi
`TypeError: round() takes 1 positional argument but 2 were given`. Đây là thứ
**không thể xảy ra trong OPL**, nơi ngôn ngữ mô hình và ngôn ngữ script tách bạch.
Cái giá của việc nhúng ngôn ngữ mô hình vào một ngôn ngữ chủ (DSL nội sinh).

---

### Trục ENGINE — DOcplex.cp vs OR-Tools (cùng Python, cùng mã hoá interval)

| | CP Optimizer | CP-SAT | tỉ lệ |
|---|---|---|---|
| Nhánh | 141 455 | **219** | **645×** ít hơn |
| Fails / Conflicts | 4 653 | 3 | *(không so trực tiếp)* |
| Thời gian giải | 0,039 s | **0,011 s** | 3,5× nhanh hơn |
| Tốc độ duyệt | ~3,6 triệu nhánh/giây | ~20 nghìn nhánh/giây | ~180× chậm hơn mỗi nhánh |

Đây là **cặp số liệu đáng giá nhất của cả báo cáo**, vì hai bản Python đặt cạnh
nhau gần như ánh xạ một-một:

| docplex.cp | ortools.sat |
|---|---|
| `interval_var(size=d)` | `new_interval_var(start, d, end, name)` |
| `no_overlap(list)` | `add_no_overlap(list)` |
| `end_before_start(a, b)` | `add(start_b >= end_a)` |
| `minimize(max(end_of(...)))` | `add_max_equality(...)` + `minimize(...)` |

Cùng ngôn ngữ, cùng mô hình toán, cùng cách mã hoá — **chỉ khác engine**. Số liệu
vì thế đo đúng một thứ.

**Hai lối đi khác hẳn nhau, thấy rõ qua con số:**

- **CP Optimizer** duyệt **ồ ạt** với chi phí mỗi nhánh cực rẻ — 3,6 triệu
  nhánh/giây. Nó dùng 140 nghìn nhánh cho một bài 36 công đoạn, nhưng mỗi nhánh
  chỉ tốn ~0,28 µs.
- **CP-SAT** duyệt **cực ít** — 219 nhánh, 3 xung đột — vì mỗi lần đụng mâu thuẫn
  nó **học ra một mệnh đề** chặn vĩnh viễn cả một vùng không gian (CDCL /
  lazy clause generation). Đổi lại mỗi nhánh đắt hơn ~180 lần.

Ở ft06, cách của CP-SAT thắng rõ. Nhưng **không được suy rộng từ một instance**:
bảng benchmark bài 3.2 cho thấy thứ tự đảo ngược ở hai cấu hình lớn, nơi CP
Optimizer về trước 1,6–3,8× (xem [`models/3.2_timetable/NOTES.md`](../3.2_timetable/NOTES.md)).
Kết luận đúng phải là: **hai engine mạnh ở hai chế độ khác nhau**, và ft06 quá
nhỏ để phân định.

**Khác biệt nguyên thuỷ (primitive) giữa hai engine, thấy được ở bài này:**

1. **`end_before_start` — CP-SAT không có, và cũng không cần.** CP-SAT phơi
   `start` / `size` / `end` ra thành ba **biến nguyên thật**, nên precedence viết
   thẳng thành bất đẳng thức tuyến tính `add(start[j,o] >= end[j,o-1])`. CP
   Optimizer giấu interval sau một API riêng, bù lại bằng cả một **họ** ràng buộc
   thời gian (`endBeforeStart`, `startBeforeStart`, `endAtStart`, `startAtEnd`,
   `startBeforeEnd`…) cộng thêm khái niệm **interval vắng mặt** (optional interval)
   — thứ CP-SAT chỉ có dạng rút gọn qua `new_optional_interval_var`. Bài 3.2 đã
   cho thấy chỗ này tốn kém thế nào khi phải dựng tay bên CP-SAT.

2. **CP-SAT bắt buộc phải có HORIZON hữu hạn.** Mọi biến nguyên của CP-SAT phải
   khai báo miền đóng, nên bản OR-Tools phải tính $H=\sum p_{j,o}=197$ trước rồi
   mới dựng biến được. CP Optimizer không cần: miền mặc định của interval đã là
   $0..\texttt{INTERVAL\_MAX}$. Nhỏ nhưng là khác biệt kiến trúc thật — CP-SAT
   quy mọi thứ về mệnh đề Boolean nên phải biết trước kích thước bảng.

3. **`dvar sequence` không có bên CP-SAT.** Cả biến thứ tự lẫn các ràng buộc đi
   kèm nó (`first`, `last`, `before`, `previous`, sequence có setup time) đều là
   đặc sản CP Optimizer. Ở bài 2.1 điều đó chưa gây khó vì `add_no_overlap` là đủ,
   nhưng nếu bài có **thời gian setup phụ thuộc thứ tự** thì CP Optimizer khai
   báo một ma trận `noOverlap(seq, M)` là xong, còn CP-SAT phải dựng tay biến
   Boolean cho từng cặp.

**Cảnh báo về tính tái lập của CP-SAT.** Chạy cùng model với `--workers 8`, ba
lần liên tiếp cho:

| Lần | Nhánh | Conflicts | Thời gian |
|---|---|---|---|
| 1 | 165 | 13 | 0,016 s |
| 2 | **0** | **0** | 0,018 s |
| 3 | 183 | 1 | 0,018 s |

Lần thứ hai báo **0 nhánh** — một worker đã tìm ra và chứng minh nghiệm bằng
presolve trước khi worker nào kịp phân nhánh. Đây đúng hiện tượng `PLAN.md` §2.4
mô tả. Vì thế bản OR-Tools của bài này mặc định `num_workers=1`, `random_seed=42`;
mọi con số trong bảng trên đều tái lập được từng đơn vị.

> Nhắc lại: `fails` của CP Optimizer (số nhánh chết) và `conflicts` của CP-SAT
> (số mệnh đề xung đột học được) **đếm hai thứ khác nhau**, chỉ so được trong
> cùng một engine.

### Biểu đồ Gantt

Báo cáo dựng Gantt của chiều OR-Tools ngay tại chỗ, từ nghiệm vừa chạy — xem ô
`show_solution("2.1_jobshop")` trong notebook phần 2. Muốn có thêm bản Gantt của
chiều DOcplex.cp để đặt hai lịch cạnh nhau thì chạy hai model với cờ `--gantt`:

```bash
python3 models/2.1_jobshop/docplexcp/jobshop_cp.py data/jobshop/ft06.dat --gantt results/jobshop_ft06_docplexcp.png
python3 models/2.1_jobshop/ortools/jobshop_sat.py  data/jobshop/ft06.dat --gantt results/jobshop_ft06_ortools.png
```

Hai lịch khác nhau, cùng makespan 55. Nhìn vào biểu đồ thấy ngay vì sao chặn dưới
47 không đạt được: máy $M_5$ (tải 43) và job $J_1$ (tải 47) đều bị chèn khe hở —
$J_1$ không thể chạy liên tục vì các máy nó cần đang bận job khác, và $M_5$ không
thể chạy liên tục vì các job cần nó chưa tới lượt.

---

## Chạy

```bash
# cả ba chiều
make run P=models/2.1_jobshop

# từng chiều
tools/oplrun.sh models/2.1_jobshop/opl/sched_jobshop.mod data/jobshop/ft06.dat
python3 models/2.1_jobshop/docplexcp/jobshop_cp.py data/jobshop/ft06.dat
python3 models/2.1_jobshop/ortools/jobshop_sat.py   data/jobshop/ft06.dat

# xuất biểu đồ Gantt
python3 models/2.1_jobshop/docplexcp/jobshop_cp.py --gantt results/jobshop_ft06_docplexcp.png
python3 models/2.1_jobshop/ortools/jobshop_sat.py  --gantt results/jobshop_ft06_ortools.png

# xem CP-SAT mất tính tái lập khi chạy đa luồng
python3 models/2.1_jobshop/ortools/jobshop_sat.py --workers 8

# đối chiếu: instance 6x6 mặc định của IBM (KHÁC ft06, tối ưu 45)
tools/oplrun.sh models/2.1_jobshop/opl/sched_jobshop.mod \
  "/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222/opl/examples/opl/sched_jobshop/sched_jobshop.dat"
```
