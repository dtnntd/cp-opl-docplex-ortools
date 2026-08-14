# Bài 3.1 — Lập lịch thi đấu thể thao (double round-robin)

> **Đọc trước:** hai mẫu chính thức của IBM mang cùng tên *"sports scheduling"*
> nhưng là **hai bài toán khác nhau**. Xem mục (c). Mọi phần dưới đây, trừ khi ghi
> rõ, nói về **biến thể A** — bản `sports.mod` của OPL.

---

## (a) Phát biểu bài toán

Một giải đấu có $n$ đội ($n$ chẵn). Mỗi đội có một **sân nhà**.

**Thể thức double round-robin.** Mỗi cặp đội gặp nhau đúng **hai lần** trong mùa
giải: một lần trên sân của đội này, một lần trên sân của đội kia. Trong mỗi trận,
đội đá trên sân của mình gọi là **home team**, đội còn lại là **away team**. Tổng
cộng có $n(n-1)$ trận — mỗi cặp có thứ tự (nhà, khách) đúng một trận.

**Lịch.** Mùa giải dài $W = 2(n-1)$ tuần. Mỗi tuần có đúng $n/2$ chỗ đá giống hệt
nhau, và **mỗi đội đá đúng một trận mỗi tuần**. Nhân lên: $2(n-1)\cdot\frac n2 = n(n-1)$
chỗ đá cho $n(n-1)$ trận — vừa khít, không thừa không thiếu chỗ nào.

**Ràng buộc thi đấu.**

1. **Hai nửa mùa giải.** Hai lượt của cùng một cặp đội phải rơi vào hai nửa khác
   nhau của mùa giải (nửa đầu: tuần $1..W/2$; nửa sau: tuần $W/2+1..W$).
2. **Giãn cách hai lượt.** Ngoài ra hai lượt đó phải cách nhau ít nhất
   $\delta=\min(n/2,\,6)$ tuần.
3. **Mở màn và khép lại.** Mỗi đội phải đá sân nhà ở tuần đầu **hoặc** tuần cuối,
   nhưng **không cả hai**.
4. **Cân bằng nhà/khách.** Mỗi đội đá sân nhà đúng $W/2$ trận.

**Break là gì.** Với một đội, nhìn dãy tuần theo thứ tự và ghi H (đá nhà) hay A
(đá khách): ta được một xâu độ dài $W$, ví dụ `H H A A A H ...`. **Một break là
một cặp tuần liên tiếp có cùng ký tự** — đội hai tuần liền đều đá nhà, hoặc hai
tuần liền đều đá khách. Xâu trên có 3 break (vị trí 1–2, 3–4, 4–5).

> Bản mô tả của IBM gọi "break" là *cả một đoạn* tuần liên tiếp cùng loại, nhưng
> công thức trong code — `teamBreaks[t] == sum(w in 2..nbWeeks)(playHome[t][w-1] == playHome[t][w])`
> — đếm theo **cặp liền kề**. Bài này dùng định nghĩa theo code.

5. **Cấm break dài.** Không đội nào được có ba tuần liên tiếp cùng loại (ba trận
   nhà liền, hoặc ba trận khách liền).
6. **Số break của mỗi đội phải chẵn.** Đây là hệ quả hình thức của (3) — xem ghi
   chú ở (C12) — bản gốc khai báo tường minh vì nó giúp engine cắt nhánh sớm.

**Mục tiêu.** Cực tiểu **tổng số break của toàn giải**, $\min\sum_t\beta_t$. Lịch
càng ít break thì càng "đảo" đều nhà–khách, càng công bằng cho khán giả và cho
việc di chuyển của các đội.

---

## (b) Mô hình toán học — dùng chung cho chiều `opl` và chiều `ortools`

### Tập hợp

| Ký hiệu | Định nghĩa | Ý nghĩa |
|---|---|---|
| $\mathcal{T}$ | $\{1,\dots,n\}$ | tập đội, $n$ chẵn |
| $\mathcal{W}$ | $\{1,\dots,W\}$, $W=2(n-1)$ | tập tuần |
| $\mathcal{G}$ | $\{1,\dots,\gamma\}$, $\gamma=n/2$ | tập chỗ đá trong một tuần |
| $\mathcal{M}$ | $\{1,\dots,M\}$, $M=n(n-1)$ | tập **trận** — mỗi cặp có thứ tự (nhà, khách) một trận |
| $\mathcal{S}$ | $\{1,\dots,M\}$ | tập **chỗ đá** của cả mùa, đánh số phẳng qua các tuần |
| $\mathcal{P}$ | $\{\{i,j\}: i,j\in\mathcal{T},\ i<j\}$ | tập cặp đối thủ, $|\mathcal{P}|=\binom n2$ |

Hai tập $\mathcal{M}$ và $\mathcal{S}$ **cùng lực lượng** $M$ — đó là điều kiện để
ràng buộc song ánh (C3) dùng được.

### Tham số

$$W = 2(n-1),\qquad \gamma=\frac n2,\qquad M=n(n-1)$$

$$\mu \;=\; \frac W2 + 1 \quad(\text{tuần đầu tiên của nửa sau mùa giải}),
\qquad
\delta \;=\;\begin{cases}\min\bigl(\tfrac n2,\,6\bigr) & n\ge 6\\[2pt] 0 & n<6\end{cases}$$

**Phép đánh số chỗ đá.** Chỗ đá thứ $g$ của tuần $w$ có số hiệu phẳng

$$s(w,g) \;=\; (w-1)\,\gamma + g \;\in\;\mathcal{S}$$

**Phép đánh số trận.** Cặp có thứ tự $(h,a)$ với $h\ne a$ ứng với đúng một trận

$$\iota(h,a) \;=\; (h-1)(n-1) + a - \mathbb{1}[a>h] \;\in\;\mathcal{M}$$

$\iota$ là **song ánh** từ $\{(h,a): h\ne a\}$ sang $\mathcal{M}$. Tập bộ ba hợp lệ:

$$\Pi \;=\;\bigl\{\,(h,\,a,\,\iota(h,a)) \;:\; h,a\in\mathcal{T},\ h\ne a\,\bigr\},
\qquad |\Pi| = M$$

### Biến quyết định

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $x_{w,g}$ | $\mathcal{M}$ | số hiệu **trận** được xếp vào chỗ đá $g$ của tuần $w$ |
| $h_{w,g}$ | $\mathcal{T}$ | đội **nhà** ở chỗ đá đó |
| $a_{w,g}$ | $\mathcal{T}$ | đội **khách** ở chỗ đá đó |
| $\sigma_m$ | $\mathcal{S}$ | **chỗ đá** (phẳng) của trận $m$ — biểu diễn kép của $x$ |
| $\omega_m$ | $\mathcal{W}$ | **tuần** diễn ra trận $m$ |
| $p_{t,w}$ | $\{0,1\}$ | $=1$ khi và chỉ khi đội $t$ đá **sân nhà** ở tuần $w$ |
| $\beta_t$ | $\{0,1,\dots,W/2\}$ | số break của đội $t$ |

Bốn nhóm biến đầu là **bốn góc nhìn dư thừa** vào cùng một lời giải: nhìn theo chỗ
đá ($x,h,a$), nhìn theo trận ($\sigma$), nhìn theo tuần ($\omega$), nhìn theo đội
($p$). Dư thừa có chủ ý — mỗi góc nhìn cho engine một kênh lan truyền riêng, và
(C1)(C3)(C4)(C7) là các **ràng buộc kênh** (channelling) buộc bốn góc nhìn khớp nhau.
Đây là mẫu thiết kế điển hình của CP; mô hình MILP tương đương sẽ phải chọn đúng
một cách mã hoá.

### Ràng buộc

**Kênh giữa (nhà, khách) và số hiệu trận** — ràng buộc bảng:

$$\bigl(h_{w,g},\;a_{w,g},\;x_{w,g}\bigr)\;\in\;\Pi
\qquad\forall w\in\mathcal{W},\ g\in\mathcal{G} \tag{C1}$$

(C1) một mình gánh ba việc: cấm $h_{w,g}=a_{w,g}$ (đội không tự đá với mình), **định
nghĩa** $x_{w,g}=\iota(h_{w,g},a_{w,g})$ mà không cần viết công thức số học, và giữ
cho $x$ luôn nằm trong miền hợp lệ.

**Mỗi đội đá đúng một trận mỗi tuần:**

$$\operatorname{alldiff}\bigl(h_{w,1},\dots,h_{w,\gamma},\;a_{w,1},\dots,a_{w,\gamma}\bigr)
\qquad\forall w\in\mathcal{W} \tag{C2}$$

$2\gamma = n$ giá trị đôi một khác nhau lấy trong tập $n$ phần tử $\mathcal{T}$ ⇒
mỗi đội xuất hiện **đúng một lần** mỗi tuần. Đây là chỗ `allDifferent` mạnh hơn
$\binom{n}{2}$ bất đẳng thức $\ne$ rời rạc: bộ lọc miền của nó suy ra được điều đó
ngay ở mức lan truyền.

**Song ánh chỗ đá ↔ trận:**

$$x_{w,g}=m \;\Longleftrightarrow\; \sigma_m = s(w,g)
\qquad\forall w,g,\ \forall m\in\mathcal{M} \tag{C3}$$

(C3) chính là ràng buộc `inverse`. Nó là chỗ **thể thức double round-robin được
phát biểu**: vì $|\mathcal{M}|=|\mathcal{S}|=M$ và quan hệ là song ánh, mỗi trận
$m\in\mathcal{M}$ xuất hiện **đúng một lần** trong cả mùa. Cùng với (C1) và song
ánh $\iota$, điều đó nói: mỗi cặp có thứ tự (nhà, khách) đá đúng một trận, tức mỗi
cặp đội gặp nhau đúng hai lần, mỗi sân một lần. **Không cần viết thêm ràng buộc nào
cho thể thức giải đấu.**

**Tuần của một trận:**

$$\omega_m \;=\; \Bigl\lfloor \frac{\sigma_m-1}{\gamma}\Bigr\rfloor + 1
\qquad\forall m\in\mathcal{M} \tag{C4}$$

**Hai lượt ở hai nửa mùa giải.** Với mọi cặp $\{i,j\}\in\mathcal{P}$, đặt
$m_1=\iota(i,j)$ (i đá nhà) và $m_2=\iota(j,i)$ (j đá nhà):

$$\bigl[\omega_{m_1}\ge\mu\bigr] \;=\; \bigl[\omega_{m_2}<\mu\bigr] \tag{C5}$$

$$\bigl|\,\omega_{m_1}-\omega_{m_2}\,\bigr| \;\ge\; \delta \tag{C6}$$

trong đó $[\,\cdot\,]$ là hàm chỉ báo (nhận giá trị 0/1). (C5) đọc là: *đúng một
trong hai lượt nằm ở nửa sau mùa giải.*

**Kênh sang góc nhìn đội — ràng buộc đếm:**

$$p_{t,w} \;=\; \bigl|\{\,g\in\mathcal{G} \;:\; h_{w,g}=t\,\}\bigr|
\qquad\forall t\in\mathcal{T},\ w\in\mathcal{W} \tag{C7}$$

Vế phải là số lần đội $t$ xuất hiện trong dãy đội nhà của tuần $w$. Vì $p_{t,w}$
khai báo là biến **nhị phân**, (C7) đồng thời ép số đó $\le 1$ — điều này đã tự
đúng nhờ (C2), nhưng viết như vậy cho engine biết ngay.

**Cấm ba tuần liên tiếp cùng loại:**

$$1 \;\le\; p_{t,w}+p_{t,w+1}+p_{t,w+2} \;\le\; 2
\qquad\forall t\in\mathcal{T},\ w\in\{1,\dots,W-2\} \tag{C8}$$

Tổng $=3$ nghĩa là ba trận nhà liền; tổng $=0$ nghĩa là ba trận khách liền.

**Đếm break:**

$$\beta_t \;=\; \sum_{w=2}^{W} \bigl[\,p_{t,w-1}=p_{t,w}\,\bigr]
\qquad\forall t\in\mathcal{T} \tag{C9}$$

**Mở màn sân nhà thì khép lại sân khách:**

$$p_{t,1}\;\ne\;p_{t,W} \qquad\forall t\in\mathcal{T} \tag{C10}$$

**Cân bằng nhà/khách:**

$$\sum_{w\in\mathcal{W}} p_{t,w} \;=\; \frac W2 \qquad\forall t\in\mathcal{T} \tag{C11}$$

**Số break của mỗi đội là số chẵn:**

$$\beta_t \equiv 0 \pmod 2 \qquad\forall t\in\mathcal{T} \tag{C12}$$

> (C11) và (C12) là **ràng buộc xúc tác** (bản gốc gọi là *catalyzing constraints*):
> chúng **không đổi tập nghiệm**, chỉ giúp engine cắt nhánh sớm.
> (C11) suy ra từ thể thức giải đấu: theo (C1)+(C3), đội $t$ tiếp đón mỗi đội
> trong $n-1$ đội còn lại đúng một lần, nên nó đá sân nhà đúng $n-1=W/2$ trận.
> Suy luận đó đi qua ràng buộc song ánh nên **không nằm trong tầm lan truyền cục
> bộ** của engine — viết thẳng ra thì rẻ hơn nhiều.
> (C12) suy ra từ (C10): xâu H/A độ dài $W$ có hai đầu khác nhau nên số vị trí
> **đổi ký tự** là số lẻ; số break $=(W-1)-\#\text{đổi}$ là số chẵn vì $W-1$ lẻ.

**Phá đối xứng.** Các đội hoán vị được cho nhau, và thứ tự các trận trong một tuần
là tuỳ ý. Hai họ ràng buộc sau cắt hai nhóm đối xứng đó:

$$h_{1,g}=2g-1,\qquad a_{1,g}=2g \qquad\forall g\in\mathcal{G} \tag{C13}$$

$$x_{w,g} \;>\; x_{w,g-1} \qquad\forall w\in\mathcal{W},\ g\in\{2,\dots,\gamma\} \tag{C14}$$

(C13) cố định hẳn tuần 1 (đội 1 tiếp đội 2, đội 3 tiếp đội 4, …) — vừa phá đối
xứng hoán vị đội, vừa phá đối xứng **lật gương** của cả lịch thi đấu. (C14) ép các
trận trong một tuần xếp tăng dần theo số hiệu.

### Hàm mục tiêu

$$\boxed{\;\min\;\; B \;=\; \sum_{t\in\mathcal{T}} \beta_t \;}$$

### Tóm tắt kích thước

| Đại lượng | Công thức | $n=6$ | $n=8$ | $n=10$ |
|---|---|---|---|---|
| Tuần $W$ | $2(n-1)$ | 10 | 14 | 18 |
| Trận $M$ | $n(n-1)$ | 30 | 56 | 90 |
| Biến (mô hình toán) | $3\gamma W + 2M + nW + n$ | 216 | 400 | 640 |
| $\log_2$ không gian tìm kiếm | — | **510.6** (đo được) | *≈1 090 (ước tính)* | *≈1 925 (ước tính)* |

Cột cuối là lý do bài này chạy ở $n=6$ chứ không phải $n=10$ như bản gốc — xem (d).

### Biến thể B — mô hình của mẫu DOcplex.cp chính thức

Mẫu notebook của IBM giải một bài **khác**, ngắn gọn như sau. Ký hiệu $K$ = số đội
mỗi bảng, $n=2K$, số lượt gặp nhau $R=2$, số tuần $W=(K-1)R+KR=4K-2$ (**trùng khít**
công thức $2(n-1)$ của biến thể A).

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $y_{t_1,t_2,r}$ | $\{1,\dots,W\}$ | tuần diễn ra lượt $r\in\{0,1\}$ giữa $t_1$ và $t_2$ |

$$y_{t_1,t_2,r} = y_{t_2,t_1,r} \qquad\forall t_1\ne t_2,\ r \tag{B1}$$

$$\operatorname{alldiff}\bigl(\{y_{t_1,t_2,r} : t_2\ne t_1,\ r\}\bigr)\qquad\forall t_1 \tag{B2}$$

$$\sum_{t_1\ne t_2,\;r} \mathbb{1}\bigl[(t_1,t_2)\text{ cùng bảng}\bigr]\cdot
\bigl[\,y_{t_1,t_2,r}\in\{1,\dots,\lfloor W/2\rfloor\}\,\bigr] \;\ge\; \lfloor W/3\rfloor \tag{B3}$$

$$\max\;\sum_{t_1\ne t_2,\;r}\ \mathbb{1}\bigl[(t_1,t_2)\text{ khác bảng}\bigr]\cdot y_{t_1,t_2,r}$$

**Không có khái niệm sân nhà/sân khách, do đó không có break và không có hàm mục
tiêu break.** Đó là lý do objective của chiều `docplexcp` (208) không so được với
objective của hai chiều còn lại (12).

---

## (c) Nguồn từng chiều

| Chiều | Nguồn | Biến thể | File | Phạm vi |
|---|---|---|---|---|
| `opl` | ✅ **lấy mẫu chính thức** — [`sports.mod`](https://www.ibm.com/docs/en/icos) trong `CPLEX_Studio_Community222/opl/examples/opl/sports/` | **A** | [`opl/sports.mod`](opl/sports.mod) | đầy đủ |
| `docplexcp` | ✅ **lấy mẫu chính thức** — [`sports_scheduling.ipynb`](https://github.com/IBMDecisionOptimization/docplex/blob/master/examples/cp/jupyter/sports_scheduling.ipynb) | **B** | [`docplexcp/sports_scheduling_cp.py`](docplexcp/sports_scheduling_cp.py) | đầy đủ |
| `ortools` | ✍️ **viết mới** — port đầy đủ biến thể A | **A** | [`ortools/sports_sat.py`](ortools/sports_sat.py) | **đầy đủ, 14/14 ràng buộc** |
| *(phụ trợ)* | ✍️ viết mới — port biến thể A sang docplex.cp | **A** | [`docplexcp/sports_portA_cp.py`](docplexcp/sports_portA_cp.py) | đầy đủ |

Bản `sports.mod` gốc của IBM giữ nguyên tại
[`opl/sports_reference.mod`](opl/sports_reference.mod) để đối chiếu.

### Hai mẫu chính thức là hai bài toán khác nhau — phát hiện của bài này

| | biến thể A — `sports.mod` | biến thể B — `sports_scheduling.ipynb` |
|---|---|---|
| Bài | giải đấu tổng quát, có sân nhà/sân khách | lịch NFL, hai bảng đấu |
| Biến chính | trận ↔ chỗ đá ↔ đội nhà/khách (4 góc nhìn) | tuần của mỗi cặp đấu (1 góc nhìn) |
| Home/away | **có** — trung tâm của bài | **không có** |
| Break | **có** — chính là mục tiêu | không có khái niệm |
| Mục tiêu | $\min$ tổng break | $\max$ tổng tuần của các trận **khác bảng** |
| Ràng buộc toàn cục | `allowedAssignments`, `allDifferent`, `inverse`, `count` | `all_diff`, `allowed_assignments` |
| Số biến ($n=6$) | 216 | 60 |

⇒ **KHÔNG so objective giữa chiều `docplexcp` và hai chiều còn lại.** Để hai trục
so sánh vẫn có số liệu thật trên **cùng một bài toán**, dự án viết thêm file phụ
trợ `docplexcp/sports_portA_cp.py` — port biến thể A sang docplex.cp. Nhờ nó:

* **trục NGÔN NGỮ** = `opl/sports.mod` vs `docplexcp/sports_portA_cp.py`
  (cùng engine CP Optimizer, cùng tham số engine, cùng mô hình toán)
* **trục ENGINE** = `docplexcp/sports_portA_cp.py` vs `ortools/sports_sat.py`
  (cùng ngôn ngữ Python, cùng mô hình toán)

### Hai thay đổi duy nhất trên bản `sports.mod` của IBM

1. `int n = 10;` → `int n = ...;` — đưa $n$ ra `data/sports/sports.dat` để cả ba
   chiều dùng chung đúng một nguồn dữ liệu. Không đụng tới mô hình.
2. Thêm khối `execute EMIT_RESULT` in dòng `RESULT {json}` theo giao kèo của
   `tools/runner.py`. Chỉ đọc lời giải, không thêm ràng buộc.

### Hai lỗi nhỏ trong mẫu notebook của IBM, giữ nguyên có chủ ý

Bản `docplexcp/sports_scheduling_cp.py` **không sửa** hai chỗ sau vì nguyên tắc
"giữ nguyên phần dựng mô hình của bản gốc":

* `intra_divisional_pair` so `t1 <= nbTeamsInDivision` trong khi `TEAMS = range(NB_TEAMS)`
  đánh số từ **0**. Với $K=3$, hai bảng thành $\{0,1,2,3\}$ và $\{4,5\}$ — chia
  **4/2** chứ không phải 3/3.
* Phần markdown nói mục tiêu là đẩy trận **nội bảng** ra cuối mùa, còn code lại
  cộng các trận **liên bảng** vào hàm mục tiêu (`if not intra_divisional_pair(...)`).
  Code mới là thứ chạy, nên mô hình (B) ở mục (b) mô tả theo code.

---

## (d) Quan sát so sánh

### d.1 — Bảng đối chiếu ràng buộc toàn cục: CP Optimizer vs CP-SAT

Đây là điểm so sánh đắt nhất của bài. Cột "biến phụ" đếm ở $n=6$ (10 tuần, 30 trận).

| # | CP Optimizer (`sports.mod`) | CP-SAT tương ứng | Có sẵn? | Biến phụ ($n=6$) |
|---|---|---|---|---|
| (C1) | `allowedAssignments(playSlots, h, a, g)` — bảng 3 ngôi trên tupleset | `add_allowed_assignments([h,a,g], tuples)` | ✅ **1-1** | 0 |
| (C2) | `allDifferent(append(...))` | `add_all_different([...])` | ✅ **1-1** | 0 |
| (C3) | `inverse(allGames, allSlots)` | `add_inverse(flat, all_slots)` | ✅ **1-1**, nhưng CP-SAT **bắt buộc** miền $0..k-1$ còn OPL cho $1..k$ ⇒ phải dời gốc chỉ số | 0 |
| (C4) | `((allSlots[g]-1) div γ) + 1` — `div` viết thẳng trong biểu thức | `add_division_equality(ω, σ, γ)` — phải gọi ràng buộc chuyên dụng | ⚠️ có, khác cách viết | 0 |
| (C5) | `(ω[m1] >= μ) == (ω[m2] < μ)` — engine tự **reify** hai bất đẳng thức rồi so bằng | tạo bool $z_m$, buộc hai chiều bằng `only_enforce_if`, rồi `z[m1] + z[m2] == 1` | ❌ **phải diễn đạt vòng** | **30** bool |
| (C6) | `abs(ω[m1] - ω[m2]) >= δ` — `abs` là **biểu thức**, dùng ngay tại chỗ | `add_abs_equality(d, ω[m1]-ω[m2])` rồi `d >= δ` — `abs` phải **vật chất hoá** thành biến | ❌ phải thêm biến | **15** int |
| (C7) | `playHome[t][w] == count(home[w][*], t)` — `count` là **biểu thức số** | không có `count`. Mã hoá **1-hot** toàn bộ `home[w][g]` bằng `add_map_domain`, rồi $p_{t,w}=\sum_g$ bool | ❌ **phải diễn đạt vòng** | **180** bool |
| (C8) | `1 <= sum(...) <= 2` | `add_linear_constraint(sum, 1, 2)` | ✅ 1-1 | 0 |
| (C9) | `sum(w)(playHome[t][w-1] == playHome[t][w])` — cộng thẳng **biểu thức so sánh** vào một tổng | mỗi số hạng phải là bool được buộc hai chiều bằng `only_enforce_if` | ❌ phải diễn đạt vòng | **54** bool |
| (C10)(C11) | tuyến tính | tuyến tính | ✅ 1-1 | 0 |
| (C12) | `teamBreaks[t] % 2 == 0` — `%` là biểu thức | `add_modulo_equality(r, β, 2)` rồi `r == 0` — cần biến đích | ⚠️ có, cần biến phụ | **6** int |
| (C13)(C14) | gán/so sánh trực tiếp | như nhau | ✅ 1-1 | 0 |
| | | | | **Tổng: 285** |

**Kết luận rút ra từ bảng.**

**1. Ba trong bốn ràng buộc toàn cục "đặc thù CP Optimizer" hoá ra CP-SAT cũng có.**
Giả định ban đầu ở `PLAN.md` §4 — *"`sports.mod` dùng `allowedAssignments`, `inverse`,
`count` — CP-SAT không có tương đương trực tiếp"* — **chỉ đúng một phần ba**.
`add_allowed_assignments`, `add_all_different`, `add_inverse` đều tồn tại và cùng
ngữ nghĩa. Chỉ có **`count` là thật sự thiếu**.

**2. Nhưng khoảng cách thật không nằm ở danh mục ràng buộc — nó nằm ở khả năng
REIFY.** Nhìn cột "biến phụ": bốn dòng tốn kém nhất là (C5), (C6), (C7), (C9), và
cả bốn có chung một nguyên nhân. Trong OPL/docplex.cp, **một ràng buộc cũng là một
biểu thức**: `abs(...)`, `count(...)`, `(a == b)`, `(ω >= μ)` dùng được ngay tại
chỗ như một số hạng. Trong CP-SAT, mọi thứ như vậy phải **vật chất hoá thành biến
rồi buộc hai chiều bằng tay**. Đó mới là khác biệt engine, không phải chuyện thiếu
vài cái tên hàm.

**3. Cái giá đo được: +132% số biến.**

| | biến | ràng buộc | log₂ không gian tìm kiếm |
|---|---|---|---|
| CP Optimizer (`sports.mod`, $n=6$) | **216** | 271 | 510.6 (đo từ log engine) |
| CP Optimizer (`sports_portA_cp.py`) | **216** | 259 | 510.6 |
| CP-SAT (`sports_sat.py`) | **501** | 808 | — (CP-SAT không báo đại lượng này) |

$501 = 216 + 285$ — **khớp đúng đến từng biến** với cột "biến phụ" của bảng trên.
Ở $n=10$ con số biến phụ là **1 215**.

**4. `add_map_domain` là công cụ chuẩn để thay `count`.** Không có `count`, cách
diễn đạt vòng chuẩn là mã hoá 1-hot: `add_map_domain(home[w][g], col, offset=1)`
tạo $n$ bool với `col[t-1] ⇔ home[w][g] == t`, rồi $p_{t,w}=\sum_g \text{col}_t$.
Giá là $W\cdot\gamma\cdot n$ bool — $10\cdot3\cdot6=180$ ở $n=6$, tăng theo
$\Theta(n^3)$. Đây là dòng đắt nhất bảng, và cũng là ví dụ sạch nhất cho luận điểm
"CP-SAT quy mọi thứ về SAT nên phải bung ra biến bool".

### d.2 — Trục NGÔN NGỮ: OPL vs DOcplex.cp (cùng engine CP Optimizer, cùng bài, $n=6$)

Hai bản dựng **cùng 216 biến, cùng $\log_2$ không gian tìm kiếm 510.6**, chạy với
**cùng tham số engine** (`TimeLimit=60`, `DefaultInferenceLevel="Extended"` — đúng
những gì khối `execute` của `sports.mod` đặt). Trung vị 3 lần chạy:

| | Obj | Ràng buộc | Thời gian | Nhánh | Fails |
|---|---|---|---|---|---|
| `opl/sports.mod` | 12 | 271 | **1.51 s** | **556 103** | **280 303** |
| `docplexcp/sports_portA_cp.py` | 12 | 259 | 2.37 s | 850 352 | 429 850 |
| tỉ lệ | = | | **1.57× chậm hơn** | **1.53× nhiều nhánh hơn** | 1.53× |

Cả hai bản đều **tất định tuyệt đối** — ba lần chạy cho đúng cùng một con số nhánh.

**Đọc kết quả.** Cùng engine, cùng mô hình toán, cùng số biến, cùng không gian tìm
kiếm — mà lệch 1.5× cả thời gian lẫn số nhánh. Nguyên nhân là **thứ tự và cách bung
ràng buộc của hai front-end khác nhau** (271 so với 259 ràng buộc sau khi trích
xuất), đủ để đổi thứ tự duyệt của heuristic mặc định. Đây là **dẫn chứng thứ hai**
cho luận điểm "khác biệt do ngôn ngữ" của báo cáo, sau dẫn chứng N-Queens ở
`PLAN.md` §2.2 (440/198 nhánh của OPL so với 255/99 của DOcplex.cp).

Khác biệt so với bài N-Queens: ở đó OPL **buộc phải** viết dài hơn (`allDifferent`
không nhận mảng biểu thức). Ở bài này thì ngược lại — **OPL diễn đạt được mọi thứ
gọn hơn hoặc bằng** docplex.cp:

| Ý | OPL | docplex.cp |
|---|---|---|
| bảng 3 ngôi | `allowedAssignments(playSlots, h, a, g)` — nhận thẳng một `{PlaySlotTuple}` có `key` | `mdl.allowed_assignments([h,a,g], tuples)` — phải tự dựng `list[tuple]` |
| gốc chỉ số của `inverse` | theo **range khai báo** của mảng (ở đây $1..M$) | **cố định 0-based** — phải dời gốc id trận |
| bất đẳng thức kép | `1 <= expr <= 2` viết tự nhiên | phải gọi `mdl.range(expr, 1, 2)` |
| tổng có điều kiện | `sum(w in 2..W)(p[w-1] == p[w])` | `sum((p[w-1] == p[w]) for w in ...)` — tương đương |

⇒ Kết luận cho báo cáo: **ưu thế cú pháp không cố định về một phía.** OPL thắng ở
bài giàu tupleset và range (3.1); Python thắng ở bài cần mảng biểu thức (1.2).

### d.3 — Trục ENGINE: CP Optimizer vs CP-SAT (cùng ngôn ngữ Python, cùng bài, $n=6$)

| | Engine | Obj | Biến | Thời gian | Nhánh | Fails / Conflicts |
|---|---|---|---|---|---|---|
| `sports_portA_cp.py` | CP Optimizer | **12** | 216 | 2.37 s | 850 352 | 429 850 |
| `sports_sat.py` (`--workers 8`) | CP-SAT | **12** | 501 | **0.78 s** | 1 350 | 0 |
| `sports_sat.py` (**mặc định**: 1 worker, seed 0) | CP-SAT | **12** | 501 | 3.06 s | 80 264 | 9 150 |

> Từ nay `sports_sat.py` **mặc định** chạy `--workers 1 --seed 0`; muốn số liệu 8
> worker thì phải truyền cờ tường minh. Cột thời gian là trung vị 3 lần chạy.

> `fails` của CP Optimizer và `conflicts` của CP-SAT đếm hai thứ khác nhau, chỉ so
> được trong cùng một engine (xem `README.md`).

**1. Hai lối tìm kiếm khác hẳn nhau.** CP-SAT một worker duyệt **80 264** nhánh,
CP Optimizer duyệt **850 352** — gấp **10.6 lần** — mà hai bên về đích cùng cỡ thời
gian (3.06 s so với 2.37 s). CP Optimizer duyệt ồ ạt với chi phí mỗi nhánh rất rẻ
(**359 000 nhánh/giây**); CP-SAT duyệt ít hơn hẳn nhờ học mệnh đề xung đột nhưng mỗi
nhánh đắt hơn (**26 000 nhánh/giây**). Đúng cùng một kết luận đã thấy ở bài 3.2.

**2. Ưu thế của CP-SAT ở đây là ĐA LUỒNG, không phải mỗi-nhánh-thông-minh-hơn.**
Bật 8 worker, CP-SAT về đích trong 0.78 s và chỉ duyệt ~1 350 nhánh — nhanh hơn 3.9×
so với chính nó chạy một luồng. Các worker chạy chiến lược khác nhau (LNS, no-LP,
core-based…) và worker nào gặp may thì kéo cả nhóm về đích. CP Optimizer bản
Community cũng dùng 16 worker song song (log ghi rõ) nhưng không thu được lợi tương
đương trên bài này.

**3. Giá phải trả: số liệu CP-SAT không tái lập được.** Ba lần chạy 8 worker cho
**826 / 1 350 / 2 648** nhánh và **0 / 0 / 41** conflicts, trong khi objective và
thời gian gần như không đổi. Cố định `num_workers=1` + `random_seed=0` thì số liệu
tất định tuyệt đối (**80 264 / 9 150** ở cả ba lần chạy liên tiếp). Đây là **xác nhận
độc lập** cho `PLAN.md` §2.4 trên một bài toán thứ hai ⇒ mọi bảng benchmark của báo
cáo bắt buộc phải cố định worker và seed, và đó là **mặc định** của `sports_sat.py`.

### d.4 — Trần Community Edition: chỗ CP-SAT thắng tuyệt đối

Bản gốc của IBM đặt $n=10$. Trên **CPLEX Studio Community Edition** thì cả hai chiều
CP Optimizer đều **không chạy nổi bản gốc**:

| $n$ | Tuần | log₂ KGTK | OPL / DOcplex.cp (CP Optimizer Community) | OR-Tools (CP-SAT) |
|---|---|---|---|---|
| **6** | 10 | **510.6** (đo được) | ✅ tối ưu **12** — 1.51 s | ✅ tối ưu **12** — 3.06 s *(mặc định 1 worker)* / 0.78 s *(`--workers 8`)* |
| 8 | 14 | ≈1 090 (ước tính) | ❌ `FATAL[ENGINE_001]: Problem size limit exceeded` | ✅ tối ưu **16** — 14.8 s, **chỉ với `--workers 8`** |
| **10** *(cỡ bản gốc IBM)* | 18 | ≈1 925 (ước tính) | ❌ `FATAL[ENGINE_001]` | ✅ tối ưu **16** — 17.9 s, **chỉ với `--workers 8`** |

> ⚠️ **Hai dòng $n=8$ và $n=10$ chỉ đạt được nhờ ĐA LUỒNG.** Chạy đúng cấu hình tái
> lập (mặc định 1 worker, seed 0, `--time-limit 300`) thì CP-SAT **không đóng nổi**
> hai cỡ bài này: $n=8$ chạm giới hạn 300 s ở trạng thái `FEASIBLE` với objective 16
> (1 822 928 nhánh, 594 403 conflicts) — tức tìm ra lời giải tối ưu nhưng **không
> chứng minh được**; $n=10$ chạm 300 s ở `FEASIBLE` với objective **28**, còn xa
> nghiệm 16. Vì vậy hai dòng này **không** dùng chung cấu hình với bảng d.3 và không
> vào bất kỳ bảng benchmark tái lập nào — chúng là bằng chứng về *trần license*,
> không phải điểm đo hiệu năng.

Thông báo lỗi thật (cả `oplrun` lẫn `docplex.cp` đều báo giống nhau):

```
*** FATAL[ENGINE_001]: Exception from IBM ILOG Concert: Problem size limit exceeded.
CP Optimizer Community Edition solves problems with search spaces up to 2^1000.
```

$n=6$ là **giá trị lớn nhất chạy được** trên bản Community. Ba nhận xét:

1. **Trần 2^1000 là trần LICENSE, không phải trần thuật toán.** Với license
   academic thì $n=10$ chạy bình thường; đây là giới hạn thương mại của IBM.
2. **CP-SAT không có trần nào tương ứng** — và bản port có **nhiều hơn 132% số biến**
   mà vẫn *dựng và giải được* cỡ bài gấp ba. Nghịch lý biểu kiến này chính là điểm
   đáng nói: mã hoá "cồng kềnh" hơn không phải là bất lợi khi engine sinh ra để nuốt
   biến bool. Nhưng phải nói đủ: ở $n\ge 8$, việc **đóng** được bài trong 300 s là
   công của 8 worker chạy song song, không phải của một luồng đơn (xem cảnh báo trên).
3. Đây là dẫn chứng cụ thể cho luận điểm **hạ tầng/giấy phép cũng là một chiều so
   sánh**, ngang hàng với ngôn ngữ và engine: `ortools` là thư viện Apache-2.0 cài
   bằng `pip install`, còn CP Optimizer đòi cài Studio và bị chặn theo cỡ bài.

### d.5 — Ghi chú về chiều `docplexcp` (biến thể B)

Chiều này giải bài khác nên không vào hai bảng trên. Số liệu để tham khảo ($n=6$,
$W=10$, 60 s):

| Status | Obj | Thời gian | Nhánh | Fails |
|---|---|---|---|---|
| Feasible (**không chứng minh được tối ưu**) | 208 | 60.0 s (chạm giới hạn) | **79 268 907** | 38 573 731 |

> ⚠️ Đây là lần chạy **chạm giới hạn thời gian**, nên `Nhánh` và `Fails` ở hàng này
> đo *máy chạy nhanh cỡ nào trong 60 giây*, chứ không đo độ khó của bài — chúng đổi
> theo tốc độ và tải máy, và **không tái lập được** như mọi số khác trong báo cáo.
> Các lần chạy về sau trên cùng máy cho 86–88 triệu nhánh. Điều duy nhất tái lập
> được ở hàng này là **kết luận**: hết 60 s vẫn không đóng nổi bài.

Chỉ 60 biến, mà CP Optimizer duyệt **79 triệu nhánh** trong 60 s vẫn không đóng được
bài. Lý do: mô hình (B) **không có ràng buộc phá đối xứng nào**, trong khi biến thể A
có tới hai họ ((C13)(C14)). Đặt cạnh nhau, đây là minh hoạ rất gọn cho vai trò của
phá đối xứng trong CP: bài 216 biến **có** phá đối xứng đóng trong 1.5 s; bài 60 biến
**không** phá đối xứng, 60 s vẫn treo. Nó cũng cho thấy **tốc độ duyệt nhánh khủng
khiếp của CP Optimizer** — 1.3–1.45 triệu nhánh/giây tuỳ tải máy — và tốc độ đó một mình không cứu
được một mô hình dựng kém.

---

## Kiểm chứng chéo

Ba bản cài đặt **biến thể A** — ba cách viết, hai engine, hai kiểu mã hoá — cùng
chứng minh **objective tối ưu $B^\star=12$** ở $n=6$:

| Bản cài đặt | Ngôn ngữ | Engine | Objective | Trạng thái |
|---|---|---|---|---|
| `opl/sports.mod` | OPL | CP Optimizer | **12** | Optimal |
| `docplexcp/sports_portA_cp.py` | Python | CP Optimizer | **12** | Optimal |
| `ortools/sports_sat.py` | Python | CP-SAT | **12** | OPTIMAL |

Bản port CP-SAT sinh thêm 285 biến và diễn đạt vòng 5 ràng buộc, nên phép kiểm này
không hề tầm thường: port **thiếu** ràng buộc sẽ cho $B^\star<12$, port **thừa** sẽ
cho $B^\star>12$ hoặc vô nghiệm. Trùng khít đúng 12 ở cả ba ⇒ ba mô hình tương đương.

Kiểm thêm ở $n=8$ (`--workers 8`, vì một luồng không đóng được cỡ này trong 300 s)
với hai seed khác nhau (0 và 42): cùng cho tối ưu **16** — loại trừ khả năng số liệu
phụ thuộc may rủi của bộ sinh ngẫu nhiên.

Chiều `docplexcp` giải **biến thể B** nên **không** vào bảng này; nó được kiểm bằng
tính hợp lệ của lời giải theo tập ràng buộc của chính nó (mỗi đội đúng một trận mỗi
tuần, hai lượt của mỗi cặp ở hai tuần khác nhau).

---

## Chạy

```bash
# cả ba chiều
tools/runner.py --suite models/3.1_sports

# từng chiều
tools/oplrun.sh models/3.1_sports/opl/sports.mod data/sports/sports.dat
python3 models/3.1_sports/docplexcp/sports_scheduling_cp.py 6
python3 models/3.1_sports/ortools/sports_sat.py data/sports/sports.dat

# file phụ trợ cho hai trục so sánh
python3 models/3.1_sports/docplexcp/sports_portA_cp.py

# tái lập số liệu CP-SAT — 1 worker + seed 0 đã là MẶC ĐỊNH, hai cờ dưới chỉ để nói rõ
python3 models/3.1_sports/ortools/sports_sat.py --workers 1 --seed 0 --quiet

# vượt trần Community: CP-SAT dựng và giải được đúng cỡ bản gốc IBM.
# Cần đa luồng tường minh — một luồng thì 300 s vẫn chưa chứng minh được tối ưu.
python3 models/3.1_sports/ortools/sports_sat.py --n 10 --time-limit 300 --workers 8 --quiet
```
