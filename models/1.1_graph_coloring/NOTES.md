# Bài 1.1 — Tô màu đồ thị (Graph Coloring)

## (a) Phát biểu bài toán

Cho một bản đồ gồm nhiều vùng và một bảng màu có $K$ màu. Hãy tô màu cho **mọi
vùng** sao cho **không có hai vùng chung biên giới nào cùng màu**.

Trừu tượng hoá thành đồ thị: mỗi vùng là một **đỉnh**, mỗi cặp vùng có chung biên
giới là một **cạnh**. Bài toán trở thành *tô màu đỉnh của đồ thị*: gán cho mỗi đỉnh
một trong $K$ màu sao cho hai đầu của mọi cạnh khác màu nhau.

| | Nội dung |
|---|---|
| **Dữ liệu vào** | đồ thị vô hướng $G=(V,E)$; số màu cho phép $K$; danh sách tên màu |
| **Dữ liệu ra** | một ánh xạ *đỉnh → màu*, tức một phép tô hợp lệ |
| **Ràng buộc** | hai đỉnh kề nhau không được cùng màu |
| **Mục tiêu** | không có — đây là **CSP thuần**: chỉ cần tìm một nghiệm khả thi |

Bộ dữ liệu dùng chung cho cả ba chiều là **đúng bộ của hai ví dụ chính thức**
(`color.mod` của OPL và `examples/cp/basic/color.py` của DOcplex.cp): bản đồ 6
nước Tây Âu với 9 đường biên giới, và bảng 4 màu.

| | Giá trị |
|---|---|
| $V$ | Belgium, Denmark, France, Germany, Luxembourg, Netherlands — $\lvert V\rvert=6$ |
| $E$ | BE–FR, BE–DE, BE–NL, BE–LU, DK–DE, FR–DE, FR–LU, DE–LU, DE–NL — $\lvert E\rvert=9$ |
| $K$ | 4 — blue, white, yellow, green |

File dữ liệu: [`data/coloring/map6.dat`](../../data/coloring/map6.dat).

**Phần mở rộng (tuỳ chọn, cờ `--min`):** biến bài toán thoả mãn ràng buộc thành
bài toán tối ưu — *ít nhất bao nhiêu màu là đủ để tô được $G$?* Đại lượng đó là
**sắc số** $\chi(G)$.

---

## (b) Mô hình toán học — dùng chung cho cả ba chiều

### Tập hợp

| Ký hiệu | Ý nghĩa |
|---|---|
| $V$ | tập đỉnh (vùng cần tô màu) |
| $E\subseteq\bigl\{\{u,v\}: u,v\in V,\ u\neq v\bigr\}$ | tập cạnh — mỗi cạnh là một cặp vùng chung biên giới |
| $\mathcal{K}=\{0,1,\dots,K-1\}$ | tập **nhãn màu** |

Đồ thị vô hướng nên mỗi cạnh chỉ ghi **một lần** trong dữ liệu; ràng buộc sinh ra
từ nó đối xứng theo hai đầu nên không cần ghi cả hai chiều.

### Tham số

| Ký hiệu | Kiểu | Ý nghĩa | Giá trị ở bộ dữ liệu này |
|---|---|---|---|
| $K$ | $\mathbb{Z}_{>0}$ | số màu được phép dùng | $4$ |
| $n=\lvert V\rvert$ | $\mathbb{Z}_{>0}$ | số đỉnh | $6$ |
| $m=\lvert E\rvert$ | $\mathbb{Z}_{\ge 0}$ | số cạnh | $9$ |
| $\mathrm{name}_k$ | chuỗi | tên hiển thị của màu $k\in\mathcal{K}$ | blue, white, yellow, green |

Màu chỉ là **nhãn**: $\mathrm{name}_k$ không tham gia vào mô hình, nó chỉ dùng lúc
in nghiệm. Đây là chỗ sinh ra đối xứng hoán vị màu, bàn ở cuối mục này.

### Biến quyết định

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $x_v$ | $\mathcal{K}=\{0,\dots,K-1\}$ | nhãn màu gán cho đỉnh $v\in V$ |
| $\kappa$ | $\{1,\dots,K\}$ | *(chỉ ở phần mở rộng)* số màu thực sự được dùng |

Cả mô hình chỉ có $n$ biến. Ràng buộc "**mỗi vùng được tô đúng một màu**" —
thường phải viết thành ràng buộc riêng — ở đây **không tồn tại**: nó đã nằm sẵn
trong cách mã hoá, vì $x_v$ là một biến đơn trị nên tự động nhận đúng một giá trị.
Đây là nét đặc trưng của CP đã gặp ở bài 1.2 (biến $q_i$ nuốt luôn ràng buộc "mỗi
hàng một hậu"): **chọn cách mã hoá tốt thì một phần ràng buộc tự biến mất.**

> **Đối chiếu với mã hoá nhị phân kiểu MILP.** Cách viết quen thuộc của quy hoạch
> nguyên là $y_{v,k}\in\{0,1\}$ ("đỉnh $v$ mang màu $k$"), và khi đó phải thêm
> $\sum_{k\in\mathcal{K}} y_{v,k}=1\ \forall v$ cùng $y_{u,k}+y_{v,k}\le 1\ \forall\{u,v\}\in E,\forall k$.
>
> | | biến | ràng buộc | không gian tìm kiếm |
> |---|---|---|---|
> | CP — biến miền $\mathcal{K}$ | $n=6$ | $m=9$ | $K^{n}=4^6=4\,096$ ($\log_2 = 12$) |
> | MILP — biến nhị phân | $nK=24$ | $n+mK=42$ | $2^{24}$ ($\log_2 = 24$) |
>
> Cùng một bài toán, mã hoá biến nguyên cho không gian tìm kiếm nhỏ hơn hẳn. Với
> bài 6 đỉnh thì chênh lệch này vô nghĩa, nhưng nó chính là lý do PLAN.md §2.1 chốt
> **bỏ mã hoá nhị phân** ở bài 3.2 để lọt trần $2^{1000}$ của Community Edition.
> Ở bài này $\log_2$ không gian tìm kiếm chỉ là **12** — cách trần 1000 rất xa.

### Ràng buộc

**(C1) Hai đỉnh kề nhau khác màu.** Đây là toàn bộ nội dung của bài toán:

$$x_u \neq x_v \qquad \forall\,\{u,v\}\in E \tag{C1}$$

Với bộ dữ liệu 6 nước, (C1) bung ra đúng 9 ràng buộc — cũng đúng 9 dòng `!=` mà hai
ví dụ chính thức của IBM viết tay:

$$
\begin{aligned}
&x_{\text{BE}}\neq x_{\text{FR}}, \quad
 x_{\text{BE}}\neq x_{\text{DE}}, \quad
 x_{\text{BE}}\neq x_{\text{NL}}, \quad
 x_{\text{BE}}\neq x_{\text{LU}}, \quad
 x_{\text{DK}}\neq x_{\text{DE}},\\[2pt]
&x_{\text{FR}}\neq x_{\text{DE}}, \quad
 x_{\text{FR}}\neq x_{\text{LU}}, \quad
 x_{\text{DE}}\neq x_{\text{LU}}, \quad
 x_{\text{DE}}\neq x_{\text{NL}}.
\end{aligned}
$$

**(C1′) Dạng mạnh hơn — `allDifferent` trên mỗi clique.** Nếu $Q\subseteq V$ là một
**clique** (mọi cặp đỉnh trong $Q$ đều kề nhau) thì $K$ ràng buộc $\neq$ rời rạc
tương đương với một ràng buộc toàn cục:

$$\texttt{allDifferent}\bigl(\{x_v : v\in Q\}\bigr) \qquad \forall\,Q\in\mathcal{Q} \tag{C1′}$$

với $\mathcal{Q}$ là một họ clique phủ hết các cạnh. (C1′) **cùng tập nghiệm** với
(C1) nhưng **lan truyền mạnh hơn**: bộ lọc của `allDifferent` dùng ghép cặp cực đại
trên đồ thị hai phía biến–giá trị, phát hiện được mâu thuẫn mà từng ràng buộc $\neq$
rời rạc không thấy. Ba bản cài đặt trong dự án đều dùng **(C1)**, vì phải giữ nguyên
văn phần dựng mô hình của hai ví dụ chính thức; (C1′) ghi ở đây để nêu rõ mô hình
này còn siết được, và vì nó là đường nối tới `allDifferent` của bài 1.2.

### Hàm mục tiêu

$$\text{(không có — CSP thuần)}$$

Bài toán chỉ hỏi *có tồn tại phép tô hợp lệ với $K$ màu không*. Mọi nghiệm khả thi
đều tốt ngang nhau, nên `objective` trong dòng `RESULT` của cả ba chiều là `null`.

### Phần mở rộng — tối ưu sắc số

Thêm biến $\kappa$ = số màu được dùng, và ép mọi nhãn nằm dưới nó:

$$x_v \le \kappa - 1 \qquad \forall v\in V \tag{C2}$$

$$\boxed{\ \min\ \kappa\ }$$

**Vì sao $\min\kappa$ đúng bằng $\chi(G)$.** Màu chỉ là nhãn, nên nếu tồn tại một
phép tô hợp lệ dùng $k$ màu thì luôn đánh lại nhãn được thành $\{0,\dots,k-1\}$;
khi đó $\max_v x_v = k-1$ và (C2) thoả với $\kappa=k$. Ngược lại mọi nghiệm của
(C1)+(C2) là một phép tô hợp lệ dùng không quá $\kappa$ màu. Vậy

$$\min\ \kappa \;=\; \min_{\text{phép tô hợp lệ}} \bigl(\max_v x_v + 1\bigr) \;=\; \chi(G).$$

**Đối xứng.** Với mọi hoán vị $\pi$ của $\mathcal{K}$, nếu $x$ là nghiệm thì
$\pi\circ x$ cũng là nghiệm ⇒ mỗi nghiệm "thật" xuất hiện tới $K!=24$ lần. (C2) phá
được một phần đối xứng đó (nó ép các nhãn dồn về đầu bảng màu). Muốn phá triệt để
thì thêm ràng buộc *precede*: màu $k$ chỉ được dùng nếu màu $k-1$ đã dùng ở một đỉnh
có chỉ số nhỏ hơn. Ba bản cài đặt **không** thêm ràng buộc này — bài quá nhỏ để bõ,
và giữ mô hình gọn thì so ba chiều mới sạch.

**Chặn dưới bằng clique — kiểm chứng bằng tay lời giải của solver.** Mọi đỉnh trong
một clique phải đôi một khác màu, nên

$$\chi(G)\ \ge\ \omega(G) \quad(\omega = \text{kích thước clique lớn nhất}).$$

Ở bộ dữ liệu này, bốn nước $\{$Belgium, France, Germany, Luxembourg$\}$ đôi một có
chung biên giới — cả 6 cạnh BE–FR, BE–DE, BE–LU, FR–DE, FR–LU, DE–LU đều nằm trong
$E$ — nên đó là một $K_4$ và $\chi(G)\ge 4$. Mặt khác phần CSP đã cho một phép tô
hợp lệ với 4 màu, nên $\chi(G)\le 4$. Kết luận:

$$\chi(G) = 4.$$

**Cả ba chiều đều trả về $\kappa^\star=4$ và đều báo *tối ưu đã chứng minh*** — khớp
đúng chứng minh bằng tay ở trên. Điều này cũng giải thích một quan sát nhỏ: ở phần
CSP, cả ba chiều đều dùng hết cả 4 màu (`colors_used=4`), và **bắt buộc phải thế**,
vì không phép tô hợp lệ nào của $G$ dùng ít hơn 4 màu.

---

## (c) Nguồn từng chiều

| Chiều | Nguồn | Đường dẫn |
|---|---|---|
| **OPL** (CP Optimizer) | ✅ **mẫu chính thức** | `<Install_dir>/opl/examples/opl/color/color.mod` — *Licensed Materials – Property of IBM, Copyright IBM Corporation 1998, 2026.* Bản online: [ibm.com/docs · color.mod](https://www.ibm.com/docs/en/icos/22.2.0?topic=SSSA5P_22.2.0/ilog.odms.ide.help/examples/html/opl/color/color.mod.htm) |
| **DOcplex.cp** (CP Optimizer) | ✅ **mẫu chính thức** | [`vendor/docplex/examples/cp/basic/color.py`](../../vendor/docplex/examples/cp/basic/color.py) — *(c) Copyright IBM Corp. 2015, 2022, Apache License 2.0*. Gốc: [github.com/IBMDecisionOptimization/docplex](https://github.com/IBMDecisionOptimization/docplex/tree/master/examples/cp/basic) |
| **OR-Tools** (CP-SAT) | ✍️ **viết mới** | Bộ hướng dẫn chính thức [developers.google.com/optimization](https://developers.google.com/optimization/cp) **không có** trang graph coloring (phần CP chỉ có N-Queens và cryptarithmetic). Kho `or-tools` chỉ có bản đóng góp trong `examples/contrib`, không phải tài liệu chính thức, và gói pip không kèm thư mục examples |
| **Mở rộng min sắc số** | ✍️ **viết mới** cả ba chiều | Không nền tảng nào có mẫu; OPL để ở file riêng `opl/color_min.mod` để `color.mod` không bị đụng vào |

**Phạm vi "giữ nguyên văn".** Với hai chiều lấy mẫu chính thức, phần **dựng mô hình**
— khai báo biến và toàn bộ ràng buộc — được chép nguyên xi. Những gì dự án thêm vào
đều nằm ngoài phần đó:

| Thêm gì | OPL | DOcplex.cp |
|---|---|---|
| cấu hình engine | — (oplrun tự lo) | `import cpo_env` |
| nạp dữ liệu chung | khai báo `... ;` đọc `map6.dat` | `opl_dat.load(...)` |
| chốt chặn chống lệch dữ liệu | 3 câu `assert` ở tầng model | 3 câu `assert` Python |
| bản sao đồ thị chỉ để đối chiếu | `{string} HardcodedCountries`, `{Edge} HardcodedEdges` | `_HARDCODED_EDGES` |
| kiểm tra nghiệm theo tập cạnh | khối `execute` thêm | vòng lặp Python |
| dòng `RESULT {json}` | trong khối `execute` thêm | `print(json.dumps(...))` |

**Đã kiểm chứng phần nguyên văn không bị đụng:** chạy thẳng file gốc của IBM
(`oplrun "<Install_dir>/.../color/color.mod"`, không kèm `.dat`) cho **202 nhánh /
62 fails** — trùng khít con số của bản trong dự án. Phần thêm vào không làm đổi một
nhánh nào của quá trình tìm kiếm.

**Ba chiều không có đường nào chạy lệch dữ liệu.** Hai ví dụ chính thức viết thẳng
đồ thị vào model, nên nếu chỉ để đó thì sửa `map6.dat` sẽ khiến chiều OR-Tools giải
một bài khác hai chiều kia mà không ai biết. Cách xử lý: cả hai chiều lấy mẫu đều
giữ **một bản sao đồ thị chỉ dùng để đối chiếu** (không tham gia dựng mô hình) và
so nó với `map6.dat` **trước khi giải**. Đã thử nghiệm bằng cách sửa hỏng dữ liệu —
cả hai chiều đều dừng, và `tools/runner.py` báo `[FAIL]`:

| Thử | OPL | DOcplex.cp |
|---|---|---|
| đổi cạnh `<"Denmark","Germany">` → `<"Denmark","France">` | `ERROR[GENERATE_100] … Model assertion failed` | `AssertionError: Tập cạnh hardcode không khớp Edges trong …` |
| xoá cạnh `<"Germany","Netherlands">` | `ERROR[GENERATE_100] … Model assertion failed` | `AssertionError: …` |
| sửa `NbColors = 3` | `ERROR[GENERATE_100]` | `AssertionError: Mẫu chính thức hardcode 4 màu, dữ liệu chung có 3` |

Chiều OPL còn có thêm một lớp nữa: khối `execute` kiểm tra lại nghiệm theo **đúng
tập cạnh trong file** rồi mới in `RESULT`, và đổi `status` thành `"Invalid"` nếu có
cạnh nào bị vi phạm. Chiều DOcplex.cp và OR-Tools làm y hệt bằng Python.

---

## (d) Quan sát cho phần so sánh

### Kiểm chứng chéo — điều kiện tiên quyết

| | OPL | DOcplex.cp | OR-Tools |
|---|---|---|---|
| CSP: tìm được nghiệm hợp lệ | ✅ | ✅ | ✅ |
| CSP: số vi phạm cạnh (tự kiểm tra lại theo `map6.dat`) | 0 | 0 | 0 |
| CSP: số màu dùng tới | 4 | 4 | 4 |
| Mở rộng: sắc số $\chi(G)$ | **4** (Optimal) | **4** (Optimal) | **4** (OPTIMAL) |

Ba chiều **cùng kết luận khả thi**, ba nghiệm đều **hợp lệ theo đúng tập cạnh của
file dữ liệu chung** (mỗi chiều tự kiểm tra lại nghiệm của mình rồi mới in `RESULT`),
và phần mở rộng cho **cùng một giá trị tối ưu 4**, khớp với chứng minh bằng tay
$\chi(G)=\omega(G)=4$ ở mục (b).

Ba nghiệm CSP **khác nhau về nội dung** — chuyện bình thường: bài có rất nhiều
nghiệm, chiều nào về đích trước ở nghiệm nào thì báo nghiệm đó.

### Số liệu đo được

Đo trên cùng một máy, cùng file dữ liệu, mỗi cấu hình chạy **5 lần**; cột thời gian
lấy **trung vị** kèm khoảng dao động. **Số nhánh và số fails/conflicts giống hệt
nhau ở cả 5 lần chạy, cả ba chiều** — chiều OR-Tools cố định `num_search_workers=1`
và `random_seed=0`; hai chiều CP Optimizer tất định sẵn.

| Chế độ | Chiều | Engine | Obj | `solve_time_s` (trung vị) | dao động | Nhánh | Fails / Conflicts |
|---|---|---|---|---|---|---|---|
| CSP | OPL | CP Optimizer | — | 0.021 | 0.019 – 0.028 | 202 | 62 |
| CSP | DOcplex.cp | CP Optimizer | — | 0.019 | 0.019 – 0.022 | 201 | 62 |
| CSP | OR-Tools | CP-SAT | — | **0.0021** | 0.0017 – 0.0022 | **37** | **0** |
| min $\kappa$ | OPL | CP Optimizer | **4** | 0.031 | 0.024 – 0.042 | 8 373 | 4 575 |
| min $\kappa$ | DOcplex.cp | CP Optimizer | **4** | 0.029 | 0.027 – 0.041 | 8 380 | 4 594 |
| min $\kappa$ | OR-Tools | CP-SAT | **4** | **0.0027** | 0.0017 – 0.0029 | **25** | **0** |

> **Đọc bảng này cho đúng.** Bài quá nhỏ nên cột thời gian ở thang **phần trăm giây**,
> nơi nhiễu hệ thống và chi phí trích mô hình lấn át phần giải thật — dao động
> 0.019–0.028 s của một cấu hình đã rộng gần bằng khoảng cách giữa hai chiều CP
> Optimizer. Đại lượng đáng tin ở bài này là **số nhánh**: nó tất định tuyệt đối và
> phản ánh đúng công sức tìm kiếm. Bài 3.2 mới là chỗ so thời gian có ý nghĩa.
>
> Nhắc lại cảnh báo chung của dự án: `fails` (CP Optimizer) và `conflicts` (CP-SAT)
> đếm hai thứ khác nhau — chỉ so được **trong cùng một engine**, không so chéo.

### Trục NGÔN NGỮ — OPL vs DOcplex.cp (cùng engine CP Optimizer)

**Ở tầng ràng buộc, hai ngôn ngữ trùng khít.** Hai bản mẫu chính thức gần như là
bản dịch từng dòng của nhau:

```opl
Belgium != France;                 // OPL
```
```python
mdl.add(Belgium != France)         # DOcplex.cp
```

Và số liệu xác nhận: **202/62 so với 201/62** — chênh đúng **một nhánh**. Đây là
tương phản đáng giá với bài 1.2, nơi cùng hai chiều này lệch nhau **440/198 so với
255/99**. Rút ra được một kết luận cụ thể chứ không chung chung:

> Khoảng cách giữa hai ngôn ngữ **không** xuất hiện ở ràng buộc vô hướng đơn giản.
> Nó xuất hiện đúng lúc mô hình cần đưa **biểu thức** vào **ràng buộc toàn cục** —
> chỗ mà `allDifferent` của OPL chỉ nhận `dvar int[]` nên phải vật chất hoá biến
> phụ, còn `all_diff` của DOcplex.cp nhận thẳng generator biểu thức. Bài 1.1 không
> có tình huống đó, nên hai chiều đi gần như trùng nhau.

**Chênh một nhánh đó từ đâu ra? — đã truy ra tận nơi.** Xuất file `.cpo` mà
DOcplex.cp gửi cho engine, thấy thứ tự khai báo biến là

```
France = intVar(0..3);  Belgium = ...;  Germany = ...;
Netherlands = ...;      Luxembourg = ...;  Denmark = ...;
```

tức **không** phải thứ tự người viết khai báo trong Python (Belgium, Denmark,
France, …) mà là thứ tự dẫn xuất từ cây biểu thức của các ràng buộc. Thí nghiệm
kiểm chứng — chỉ **đảo hai vế của đúng một ràng buộc**, `mdl.add(Belgium != France)`
thành `mdl.add(France != Belgium)`, không đổi gì khác:

| Bản Python | Thứ tự biến trong file `.cpo` | Nhánh | Fails | Nghiệm |
|---|---|---|---|---|
| `Belgium != France` (nguyên bản IBM) | France, Belgium, … | 201 | 62 | (2,2,0,1,3,3) |
| `France != Belgium` (chỉ đảo vế) | Belgium, France, … | **202** | 62 | (3,2,2,1,0,2) |

Bản đảo vế cho **đúng 202/62 và đúng nghiệm của chiều OPL**. Ngược lại, thí nghiệm
đối chứng ở phía OPL — đảo thứ tự 6 dòng `dvar` — **không** làm đổi gì (vẫn 202/62,
vẫn nguyên nghiệm cũ).

Kết luận sạch cho trục ngôn ngữ:

> Cùng engine, cùng mô hình toán, cùng 9 ràng buộc. **OPL chuẩn hoá mô hình trước
> khi giao cho engine** nên cách người dùng sắp xếp khai báo không ảnh hưởng. Còn
> **DOcplex.cp serialize mô hình theo đúng hình dạng biểu thức Python đã dựng**, nên
> một chi tiết vô hại như đảo hai vế của `!=` cũng đổi thứ tự biến trong file `.cpo`,
> và qua đó đổi cả đường đi tìm kiếm lẫn nghiệm trả về. Thứ tự này **không nhìn thấy
> được trong mã nguồn** — phải xuất `.cpo` ra mới thấy.

**Tầng dữ liệu: OPL có, Python không.** OPL có sẵn định dạng `.dat` và cú pháp
`int NbColors = ...;` để tách dữ liệu khỏi model — nạp bằng `oplrun model.mod data.dat`.
Python không có gì tương đương: hai chiều Python phải mượn `tools/opl_dat.py`, một
trình đọc `.dat` viết riêng cho dự án, thì mới đọc chung được một file dữ liệu với
chiều OPL. Đổi lại, OPL trả giá ở chiều ngược lại — xem mục kế.

**Tầng hậu xử lý: Python có, OPL trả giá.** Khối `execute` của OPL chạy ILOG Script
(nền JavaScript) và **không thấy được các hàm của tầng model**. Hai chỗ vấp thật khi
viết bài này:

| Cần làm | Trong model OPL | Trong `execute` OPL | Trong Python |
|---|---|---|---|
| số phần tử của một tập | `card(Edges)` | ❌ `Element "card" does not exist in OPL model` → dùng `Edges.size` | `len(EDGES)` |
| lấy phần tử thứ $i$ của tập | `item(ColorNames, i)` | ❌ `Element "item" does not exist in OPL model` → phải tự đổ tập ra `new Array()` | `COLOR_NAMES[i]` |

(Cả hai lỗi trên đều là `ERROR[SCRIPT_002]` lúc chạy, không phải lỗi biên dịch — nên
chỉ lộ ra khi model đã giải xong.)

**Ngay ở tầng model, OPL cũng thiếu vài phép toán mà Python có sẵn.** Chỗ vấp thật
khi viết chốt chặn chống lệch dữ liệu: cần khẳng định "tập cạnh trong `.dat` **đúng
bằng** tập cạnh hardcode".

```opl
assert Edges == HardcodedEdges;   // ❌ ERROR[GENERATE_002]:
                                  //    Operator not available for {Edge} == {Edge}
assert card(Edges inter HardcodedEdges) == card(HardcodedEdges)   // ✅ phải viết vòng
    && card(Edges) == card(HardcodedEdges);
```
```python
assert _HARDCODED_EDGES == {tuple(e) for e in EDGES}    # ✅ Python có sẵn == cho set
```

**Đổi lại, tầng dữ liệu của OPL kiểm tra chặt hơn Python.** `oplrun` từ chối chạy nếu
file `.dat` gán một phần tử mà model **không khai báo** — `ERROR[GENERATE_200]:
Element "NbColors" not defined`. Nghĩa là model và dữ liệu phải khớp nhau **hai
chiều**. Bên Python, `opl_dat.load()` chỉ trả về một `dict`; khoá thừa không ai kêu,
khoá thiếu thì tới lúc dùng mới nổ `KeyError`.

Nói cách khác, OPL là **hai ngôn ngữ trong một file** (ngôn ngữ mô hình + ngôn ngữ
script), và ranh giới giữa chúng là thứ phải học thuộc. DOcplex.cp chỉ có một ngôn
ngữ: dựng mô hình, đọc dữ liệu, kiểm tra nghiệm, in báo cáo — tất cả đều là Python.

**Một thứ OPL có mà Python phải tự làm: `assert` ở tầng model.** OPL cho viết
`assert card(Edges) == 9;` ngay trong model, và oplrun bắt lỗi ở giai đoạn *trích
mô hình* với mã lỗi riêng `ERROR[GENERATE_100]` trước khi engine chạy. Python dùng
`assert` của chính ngôn ngữ — cùng hiệu quả, nhưng đó là kiểm tra của chương trình
chứ không phải của công cụ mô hình hoá.

### Trục ENGINE — DOcplex.cp vs OR-Tools (cùng ngôn ngữ Python)

**Cú pháp gần như không phân biệt được.** Đặt cạnh nhau, hai thư viện khác nhau ở
tên hàm chứ không ở cách nghĩ:

```python
mdl   = CpoModel();       x = mdl.integer_var(0, 3, name)   ; mdl.add(x != y)     # docplex.cp
model = cp_model.CpModel(); x = model.new_int_var(0, 3, name); model.add(x != y)  # ortools
```

Khác biệt nằm **bên dưới**, và ở bài này nó lộ ra rất rõ:

| | CP Optimizer | CP-SAT | tỉ lệ |
|---|---|---|---|
| CSP — nhánh | 201 | **37** | 5.4× ít hơn |
| CSP — thời gian (trung vị) | 0.019 s | **0.0021 s** | ≈9× nhanh hơn |
| min $\kappa$ — nhánh | 8 380 | **25** | **335× ít hơn** |
| min $\kappa$ — thời gian (trung vị) | 0.029 s | **0.0027 s** | ≈11× nhanh hơn |
| đại lượng "thất bại" | 4 594 fails | **0** conflicts | — |

**Con số 0 conflict là điểm đáng nói nhất.** CP-SAT không hề vào tìm kiếm thật:
tầng *presolve* của nó rút gọn mô hình tới mức chứng minh xong tối ưu. CP Optimizer
đi lối ngược lại — duyệt cây tìm kiếm và **nâng dần chặn dưới bằng cách vét cạn**;
log của nó cho thấy đúng quá trình đó:

```
+ New bound is 3
*             4        7  0.03s        1      (gap is 25.00%)
+ New bound is 4 (gap is 0.00%)
```

Nó tìm ra nghiệm 4 màu rất sớm (7 nhánh), rồi tiêu **hơn 8 000 nhánh còn lại chỉ để
chứng minh 3 màu là không thể**. Trong khi đó chặn dưới $\chi\ge\omega=4$ là hiển
nhiên với con người khi nhìn thấy $K_4$ — nhưng CP Optimizer không suy luận theo
clique, nó phải vét. CP-SAT thì sinh mệnh đề và rút gọn ở presolve nên bắt được
ngay.

**Nhưng đừng vội kết luận "CP-SAT mạnh hơn".** Cùng phép so này ở bài 3.2, thứ tự
đảo ngược: trên bộ `large`, CP Optimizer về đích ở **0.67 s** còn CP-SAT mất
**2.52 s**. Kết luận đúng là *hai chiến lược khác nhau*:

- **CP-SAT** — ít nhánh, mỗi nhánh đắt; mạnh ở bài tổ hợp thuần và ở việc chứng
  minh tối ưu, nhờ học mệnh đề xung đột và presolve rất khoẻ.
- **CP Optimizer** — nhiều nhánh, mỗi nhánh cực rẻ; mạnh ở bài lập lịch, nơi nó có
  hơn 20 năm tối ưu riêng cho biến interval.

Bài 1.1 là bài tổ hợp thuần cỡ tí hon — đúng sân của CP-SAT. Bài 3.2 là bài lập
lịch cỡ lớn — đúng sân của CP Optimizer.

**Tính tái lập.** CP-SAT chạy đa luồng nên số liệu đổi giữa các lần chạy (bài 1.2 đã
ghi nhận `branches` lúc 475 lúc 0). Chiều OR-Tools của bài này vì thế cố định
`num_search_workers=1` và `random_seed=0`; năm lần chạy cho đúng 37 nhánh cả năm lần.
Hai chiều CP Optimizer tất định sẵn, không cần can thiệp.

### Ghi chú về mô hình còn siết được

Cả ba chiều đều dùng (C1) — 9 ràng buộc $\neq$ rời rạc — vì phải giữ nguyên văn hai
ví dụ chính thức. Nếu được viết lại tự do, cách siết là (C1′): phủ 9 cạnh bằng các
clique rồi đặt `allDifferent` lên mỗi clique. Ở đồ thị này, $K_4=\{$BE, FR, DE, LU$\}$
đã nuốt 6 trong 9 cạnh, còn lại 3 cạnh DK–DE, BE–NL, DE–NL. Với 6 đỉnh thì không bõ,
nhưng đây đúng là cách thu hẹp cây tìm kiếm khi đồ thị lớn lên — và nó lý giải vì sao
CP Optimizer phải vét 8 000 nhánh cho phần min sắc số: **thông tin clique có sẵn
trong dữ liệu, nhưng mô hình không nói cho engine biết.**

---

## Chạy

```bash
# cả ba chiều, phần CSP
make run P=models/1.1_graph_coloring
# hoặc:  python3 tools/runner.py --suite models/1.1_graph_coloring

# phần mở rộng: tối ưu sắc số (cả ba đều ra 4)
tools/oplrun.sh models/1.1_graph_coloring/opl/color_min.mod data/coloring/map6.dat
python3 models/1.1_graph_coloring/docplexcp/color_cp.py data/coloring/map6.dat --min
python3 models/1.1_graph_coloring/ortools/color_sat.py  data/coloring/map6.dat --min
```
