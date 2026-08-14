# Bài 1.2 — N-Queens

## (a) Phát biểu bài toán

Cho bàn cờ vuông $N \times N$. Đặt $N$ quân hậu lên bàn cờ sao cho không hai quân
nào ăn được nhau. Quân hậu trong cờ vua ăn theo hàng ngang, cột dọc và cả hai
đường chéo — nên điều kiện là: không hai quân nào cùng hàng, cùng cột, hoặc cùng
một đường chéo.

**Dữ liệu vào:** một số nguyên $N \ge 1$.
**Dữ liệu ra:** vị trí của $N$ quân hậu, hoặc kết luận không tồn tại lời giải
(xảy ra đúng với $N = 2$ và $N = 3$).

Đây là bài **CSP thuần** — chỉ tìm một cấu hình khả thi, không có hàm mục tiêu.
Bài toán thuộc lớp *Assignment / Labeling* trong bản đồ phân loại CP: gán giá trị
rời rạc cho các biến, ràng buộc chủ đạo là ràng buộc phân biệt.

## (b) Mô hình toán học — dùng chung cho cả ba chiều

### Tập hợp và tham số

| Ký hiệu | Ý nghĩa |
|---|---|
| $N$ | kích thước bàn cờ |
| $\mathcal{N} = \{0, 1, \dots, N-1\}$ | tập chỉ số, dùng chung cho hàng và cột |

### Biến quyết định

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $q_i$ | $\mathcal{N}$ | cột đặt quân hậu của hàng $i$, với $i \in \mathcal{N}$ |

**Chỉ $N$ biến, mỗi biến $N$ giá trị.** Cách mã hoá này là quyết định quan trọng
nhất của bài: vì mỗi hàng $i$ có đúng một biến $q_i$, ràng buộc "không hai hậu
cùng hàng" **tự động thoả** và không cần viết ra. Cách mã hoá ngây thơ dùng
$N^2$ biến nhị phân $x_{i,j}$ (có hậu ở ô $(i,j)$ hay không) sẽ phải viết thêm
ràng buộc hàng, và cho không gian tìm kiếm lớn hơn hẳn.

### Biểu thức dẫn xuất — chỉ số đường chéo

Hai quân hậu ở $(i, q_i)$ và $(j, q_j)$ nằm trên cùng một đường chéo khi nào?

- Đường chéo hướng $\nearrow$ (từ dưới-trái lên trên-phải) gồm các ô có **tổng**
  hàng và cột không đổi. Vậy hai hậu cùng đường chéo này $\iff i + q_i = j + q_j$.
- Đường chéo hướng $\searrow$ gồm các ô có **hiệu** không đổi. Vậy hai hậu cùng
  đường chéo này $\iff q_i - i = q_j - j$.

Đặt hai họ biểu thức dẫn xuất:

$$d^{\nearrow}_i = q_i + i \in \{0, \dots, 2(N-1)\}, \qquad
  d^{\searrow}_i = q_i - i \in \{-(N-1), \dots, N-1\}$$

### Ràng buộc

$$\texttt{allDifferent}\bigl(q_0, q_1, \dots, q_{N-1}\bigr) \tag{C1}$$

$$\texttt{allDifferent}\bigl(d^{\nearrow}_0, d^{\nearrow}_1, \dots, d^{\nearrow}_{N-1}\bigr) \tag{C2}$$

$$\texttt{allDifferent}\bigl(d^{\searrow}_0, d^{\searrow}_1, \dots, d^{\searrow}_{N-1}\bigr) \tag{C3}$$

(C1) không hai hậu cùng cột · (C2) không hai hậu cùng đường chéo $\nearrow$ ·
(C3) không hai hậu cùng đường chéo $\searrow$.

### Hàm mục tiêu

Không có. Bài toán là CSP thuần:

$$\text{tìm } q \in \mathcal{N}^{N} \text{ thoả (C1), (C2), (C3)}$$

### Vì sao dùng `allDifferent` chứ không phải các bất đẳng thức đôi một

Ba ràng buộc trên tương đương về mặt **tập nghiệm** với dạng viết đôi một:

$$q_i \ne q_j, \quad q_i + i \ne q_j + j, \quad q_i - i \ne q_j - j
\qquad \forall\, i < j \in \mathcal{N}$$

Nhưng chúng **không** tương đương về mặt **lan truyền ràng buộc**, và đây là điểm
cốt lõi của Constraint Programming:

| | Số ràng buộc | Mức lọc miền đạt được |
|---|---|---|
| đôi một $\ne$ | $3\binom{N}{2} = O(N^2)$ | chỉ loại được giá trị khi một biến đã cố định |
| `allDifferent` | 3 | **domain consistency** — thuật toán Régin dựa trên ghép cặp cực đại trên đồ thị hai phía, loại được mọi giá trị không thuộc bất kỳ ghép cặp hoàn hảo nào |

Ví dụ: nếu ba biến $q_1, q_2, q_3$ cùng còn miền $\{4, 5\}$, `allDifferent` phát
hiện ngay mâu thuẫn (ba biến không thể nhận hai giá trị phân biệt) trong khi các
bất đẳng thức đôi một không thấy gì cho tới khi phải gán thử. Đây chính là giá trị
của **ràng buộc toàn cục** (global constraint) — thứ phân biệt CP với cách mô hình
hoá bằng quy hoạch tuyến tính nguyên.

## (c) Nguồn từng chiều

| Chiều | Nguồn | Ghi chú |
|---|---|---|
| OPL | ✍️ **viết mới** | CPLEX Studio 22.2 không kèm ví dụ N-Queens bằng OPL (đã rà `opl/examples/opl/`) |
| DOcplex.cp | ✅ **mẫu chính thức** | `vendor/docplex/examples/cp/basic/n_queen.py` — (c) IBM Corp. 2015–2022, Apache 2.0 |
| OR-Tools | ✅ **mẫu chính thức** | https://developers.google.com/optimization/cp/queens |

Phần dựng mô hình của hai bản mẫu được giữ nguyên văn; chỉ thêm cấu hình engine,
tham số $N$ qua dòng lệnh, và dòng `RESULT` theo giao kèo của `tools/runner.py`.

## (d) Quan sát cho phần so sánh

### Trục NGÔN NGỮ — OPL vs DOcplex.cp (cùng engine CP Optimizer)

DOcplex.cp truyền thẳng mảng **biểu thức** vào ràng buộc, đúng như mô hình toán viết:

```python
mdl.add(mdl.all_diff(x[i] + i for i in range(NB_QUEEN)))
```

OPL không cho phép. `allDifferent(dexpr int[])` bị từ chối với thông báo
*"Function allDifferent(dexpr int[R]) not available in context CP"*. Hai họ
$d^{\nearrow}, d^{\searrow}$ phải được **vật chất hoá** thành mảng `dvar` phụ rồi
buộc bằng `==`:

```opl
dvar int diagUp[R] in 0..2*(n-1);
forall (i in R) diagUp[i] == q[i] + i;
allDifferent(diagUp);
```

Hệ quả đo được, cùng engine, $N = 8$:

| Chiều | Biến | Ràng buộc | log₂ không gian tìm kiếm | Nhánh | Fails |
|---|---|---|---|---|---|
| OPL | **24** | **21** | 24.0 | **440** | **198** |
| DOcplex.cp | **8** | **3** | 24.0 | **255** | **99** |

Đọc bảng này cho đúng — chỗ này dễ kết luận sai:

- **Không gian tìm kiếm y hệt nhau (24.0 = $8\log_2 8$).** Presolve của CP Optimizer
  nhận ra 16 biến phụ là **hàm xác định** của $q$ nên chúng không thêm một bậc tự
  do nào. Nói cách khác, hai mô hình mô tả đúng cùng một bài toán, không mô hình
  nào "to hơn".
- **Nhưng số nhánh lệch gần gấp đôi.** Nguyên nhân không phải kích thước không gian
  mà là **heuristic phân nhánh nhìn thấy 24 biến thay vì 8**, nên có thể chọn phân
  nhánh trên biến phụ — một quyết định gần như vô ích vì biến phụ sẽ tự cố định khi
  $q$ cố định. Cộng thêm 18 ràng buộc `==` phải lan truyền ở mỗi nút.

Đây là dẫn chứng sạch cho luận điểm trung tâm của báo cáo: **giới hạn của ngôn ngữ
mô hình hoá ép người viết dùng một cách diễn đạt kém hơn, và cái giá phải trả đo
được ngay cả khi engine không đổi.** Không có chiều DOcplex.cp thì không tách được
điều này khỏi ảnh hưởng của engine.

### Trục ENGINE — DOcplex.cp vs OR-Tools (cùng Python, cùng mô hình)

Cú pháp gần như trùng khít — cả hai đều nhận generator biểu thức:

| DOcplex.cp | OR-Tools |
|---|---|
| `mdl.all_diff(x)` | `model.add_all_different(x)` |
| `mdl.all_diff(x[i] + i for i in ...)` | `model.add_all_different(q[i] + i for i in ...)` |

Khác biệt nằm bên dưới:

- CP Optimizer báo **fails** — số nhánh chết trong cây tìm kiếm.
- CP-SAT báo **conflicts** — số mệnh đề xung đột học được, vì nó dịch mô hình xuống
  SAT rồi dùng lazy clause generation.

Hai đại lượng này **không so trực tiếp với nhau được**; chỉ so được trong cùng một
engine.

Thêm nữa, CP-SAT chạy đa luồng nên số liệu **đổi giữa các lần chạy** — cùng model
$N = 8$ đã ghi nhận `branches` lúc 475, lúc 0 (presolve giải xong trước khi vào tìm
kiếm). Vì thế bản trong repo cố định `num_search_workers = 1` và `random_seed = 0`;
sau khi cố định, ba lần chạy liên tiếp cho đúng một bộ số:

| Chiều | Nhánh | Fails / Conflicts |
|---|---|---|
| DOcplex.cp (CP Optimizer) | **255** | **99** (fails) |
| OR-Tools (CP-SAT) | **475** | **9** (conflicts) |

Con số 475 nhánh so với 9 conflict cho thấy rõ hai engine đếm hai thứ khác nhau:
CP-SAT duyệt nhiều nhánh nhưng chỉ học được 9 mệnh đề xung đột, trong khi CP
Optimizer báo 99 nhánh chết trên 255 nhánh.

### Giới hạn Community Edition

Không gian tìm kiếm của bài này là $N^N$, tức $\log_2 = N\log_2 N$. Trần 2^1000 của
Community Edition cho $N \lesssim 140$. Đã kiểm chứng: $N = 8$ chạy bình thường,
$N = 200$ ($\approx 2^{1529}$) bị engine từ chối với
`FATAL[ENGINE_001]: Problem size limit exceeded`.

## Chạy

```bash
make run P=models/1.2_nqueens

# đổi kích thước bàn cờ
python3 models/1.2_nqueens/ortools/nqueens_sat.py 20
```
