# Bài 3.2 — Xếp thời khoá biểu có ràng buộc khả dụng

## (a) Phát biểu bài toán

Xếp thời khoá biểu cho một trường: mỗi lớp phải học đủ số tiết từng môn, mỗi môn
do một giáo viên có chuyên môn phù hợp dạy, học trong một phòng phù hợp. Giáo
viên, lớp và phòng đều chỉ ở một chỗ tại một thời điểm. Mục tiêu: **tối thiểu
makespan** — kết thúc toàn bộ chương trình sớm nhất có thể.

Phần bài 3.2 thêm vào so với bản gốc là **ràng buộc khả dụng** (availability
windows): giáo viên có lịch bận, lớp có lịch bận, và mỗi môn có khung giờ cần tránh.

## (b) Mô hình toán học — dùng chung cho cả ba chiều

> Mô hình dưới đây mô tả đúng những gì ba chiều cài đặt. Nó **thay thế** bản phác
> thảo ở brief §4: bản đó dùng mã hoá nhị phân $X_{c,t,d,p}$ và bỏ sót phòng học,
> thời lượng, số lần lặp, giờ nghỉ và môn buổi sáng.

### Tập hợp

| Ký hiệu | Ý nghĩa |
|---|---|
| $\mathcal{C}$ | tập lớp |
| $\mathcal{S}$ | tập môn |
| $\mathcal{T}$ | tập giáo viên |
| $\mathcal{R}$ | tập phòng |
| $\mathcal{K}\subseteq\mathcal{T}\times\mathcal{S}$ | chuyên môn: $(t,s)\in\mathcal{K}$ nghĩa là $t$ dạy được $s$ |
| $\mathcal{D}\subseteq\mathcal{R}\times\mathcal{S}$ | phòng chuyên dụng: $(r,s)\in\mathcal{D}$ nghĩa là phòng $r$ dành cho môn $s$ |
| $\mathcal{B}\subseteq\mathcal{S}\times\mathcal{S}$ | cặp môn kỵ nhau, cần giãn cách |
| $\mathcal{M}\subseteq\mathcal{S}$ | môn chỉ được học buổi sáng |
| $\mathcal{Q}$ | chương trình học |

### Tham số

$$H=\text{số tiết mỗi ngày},\quad H_2=\tfrac{H}{2},\quad N_d=\text{số ngày},\quad
T_{\max}=H\!\cdot\!N_d,\quad \beta=\text{độ dài giãn cách}$$

Trục thời gian $\mathcal{H}=\{0,1,\dots,T_{\max}-1\}$, đánh số tiết liên tục qua các
ngày. Tiết $u$ thuộc ngày $\lfloor u/H\rfloor$ và buổi $\lfloor u/H_2\rfloor$.

### Từ chương trình học sang các buổi học

Mỗi phần tử $q=(c_q,\,s_q,\,p_q,\,n_q)\in\mathcal{Q}$ đọc là: *lớp $c_q$ phải học môn
$s_q$ thành $n_q$ buổi, mỗi buổi dài $p_q$ tiết.* Tách ra thành tập **buổi học**

$$\mathcal{I}=\bigl\{\,(q,k)\;:\;q\in\mathcal{Q},\ k\in\{1,\dots,n_q\}\,\bigr\}$$

Với $i=(q,k)\in\mathcal{I}$ viết gọn $c_i=c_q$, $s_i=s_q$, $p_i=p_q$, $q_i=q$, $k_i=k$.

### Tài nguyên dùng được

$$\mathcal{T}_s=\{t\in\mathcal{T}:(t,s)\in\mathcal{K}\}$$

$$\mathcal{R}_s=\underbrace{\{r:(r,s)\in\mathcal{D}\}}_{\text{phòng chuyên dụng của } s}
\;\cup\;
\underbrace{\{r: r\notin\Pi_\mathcal{R}(\mathcal{D})\ \wedge\ s\notin\Pi_\mathcal{S}(\mathcal{D})\}}_{\text{phòng thường, khi } s \text{ không đòi phòng riêng}}$$

trong đó $\Pi_\mathcal{R},\Pi_\mathcal{S}$ là phép chiếu $\mathcal{D}$ xuống thành phần
phòng và thành phần môn. Nói bằng lời: môn có phòng riêng thì chỉ học ở phòng riêng
đó; môn không đòi phòng riêng thì học ở bất kỳ phòng nào không bị dành riêng cho môn khác.

### Biến quyết định

| Biến | Miền | Ý nghĩa |
|---|---|---|
| $\sigma_i$ | $\mathcal{H}$ | tiết bắt đầu của buổi $i$ |
| $\eta_i$ | $\mathcal{H}$ | tiết kết thúc (hở phải): buổi $i$ chiếm $[\sigma_i,\eta_i)$ |
| $\theta_i$ | $\mathcal{T}_{s_i}$ | giáo viên dạy buổi $i$ |
| $\mu_i$ | $\mathcal{R}_{s_i}$ | phòng học buổi $i$ |
| $\gamma_{c,s}$ | $\mathcal{T}$ | giáo viên cố định của cặp (lớp $c$, môn $s$) |
| $\omega$ | $\mathcal{H}$ | makespan |

Việc $\theta_i$ và $\mu_i$ lấy miền $\mathcal{T}_{s_i}$, $\mathcal{R}_{s_i}$ đã **nuốt
luôn** hai ràng buộc "giáo viên phải đủ chuyên môn" và "phòng phải phù hợp" vào
trong khai báo biến — không cần viết thành ràng buộc riêng. Đây là nét đặc trưng
của CP đã gặp ở bài 1.2 với N-Queens.

> Lưu ý: $\eta_i\in\mathcal{H}$ nên $\eta_i\le T_{\max}-1$, tức tiết cuối cùng của kỳ
> không bao giờ được dùng. Đây là đặc điểm của bản OPL gốc; hai chiều còn lại giữ
> nguyên để ba chiều so được với nhau.

### Ràng buộc

**Cấu trúc thời gian**

$$\eta_i=\sigma_i+p_i \qquad \forall i\in\mathcal{I} \tag{C1}$$

$$\sigma_i<\sigma_j \qquad \forall i,j\in\mathcal{I}:\ q_i=q_j,\ k_i<k_j \tag{C2}$$

(C2) đánh số các buổi của cùng một môn theo đúng thứ tự thời gian — vừa hợp lẽ, vừa
phá đối xứng giữa các buổi giống hệt nhau, giúp engine chứng minh tối ưu nhanh hơn.

**Tài nguyên chỉ ở một chỗ tại một thời điểm.** Với mọi $i\ne j$:

$$c_i=c_j \;\Longrightarrow\; [\sigma_i,\eta_i)\cap[\sigma_j,\eta_j)=\varnothing \tag{C3}$$
$$\theta_i=\theta_j \;\Longrightarrow\; [\sigma_i,\eta_i)\cap[\sigma_j,\eta_j)=\varnothing \tag{C4}$$
$$\mu_i=\mu_j \;\Longrightarrow\; [\sigma_i,\eta_i)\cap[\sigma_j,\eta_j)=\varnothing \tag{C5}$$

Ba ràng buộc này là chỗ **ba chiều mã hoá khác nhau** — xem mục kế tiếp.

**Ổn định phân công**

$$\theta_i=\gamma_{c_i,\,s_i} \qquad \forall i\in\mathcal{I} \tag{C6}$$

Một lớp học một môn thì suốt kỳ chỉ một giáo viên dạy.

**Ràng buộc lịch**

$$p_i>1 \;\Longrightarrow\; \Bigl\lfloor \tfrac{\sigma_i}{H_2}\Bigr\rfloor=\Bigl\lfloor \tfrac{\eta_i-1}{H_2}\Bigr\rfloor \tag{C7}$$

$$s_i\in\mathcal{M} \;\Longrightarrow\; \sigma_i \bmod H < H_2 \tag{C8}$$

$$c_i=c_j,\ s_i=s_j,\ i\ne j \;\Longrightarrow\; \Bigl\lfloor\tfrac{\sigma_i}{H}\Bigr\rfloor\ne\Bigl\lfloor\tfrac{\sigma_j}{H}\Bigr\rfloor \tag{C9}$$

(C7) buổi dài hơn một tiết không được vắt qua giờ nghỉ trưa. (C8) môn buổi sáng phải
bắt đầu trong buổi sáng. (C9) một lớp không học cùng một môn hai lần trong một ngày.

**Giãn cách giữa hai môn kỵ nhau.** Với $i\ne j$, $c_i=c_j$, và $(s_i,s_j)\in\mathcal{B}$
hoặc $(s_j,s_i)\in\mathcal{B}$:

$$\Bigl\lfloor\tfrac{\sigma_i}{H}\Bigr\rfloor\ne\Bigl\lfloor\tfrac{\sigma_j}{H}\Bigr\rfloor
\;\;\vee\;\;
\Bigl\lfloor\tfrac{\sigma_i}{H_2}\Bigr\rfloor\ne\Bigl\lfloor\tfrac{\sigma_j}{H_2}\Bigr\rfloor
\;\;\vee\;\;
g_{ij}\ \ge\ \beta \tag{C10}$$

$$g_{ij}=\max(0,\ \sigma_i-\eta_j)+\max(0,\ \sigma_j-\eta_i)$$

Khác ngày, hoặc khác buổi, hoặc cách nhau đủ $\beta$ tiết. Do (C3) hai buổi cùng lớp
không chồng nhau nên nhiều nhất một số hạng của $g_{ij}$ dương — nó đúng bằng khoảng
trống giữa hai buổi.

### Phần bài 3.2 bổ sung — ràng buộc khả dụng

Dữ liệu vào thêm ba tập lịch bận:

$$\mathcal{U}^{T}\subseteq\mathcal{T}\times\mathcal{H},\qquad
\mathcal{U}^{C}\subseteq\mathcal{C}\times\mathcal{H},\qquad
\mathcal{U}^{S}\subseteq\mathcal{S}\times\mathcal{H}$$

lần lượt là lịch bận của giáo viên, lịch bận của lớp, và khung giờ cần tránh của môn.
Đặt vị từ "buổi $i$ **không** phủ tiết $u$":

$$\mathrm{free}(i,u)\;\equiv\;u\notin[\sigma_i,\eta_i)\;\equiv\;\bigl(\sigma_i>u\ \vee\ \eta_i\le u\bigr)$$

$$\theta_i=t \;\Longrightarrow\; \mathrm{free}(i,u) \qquad \forall i\in\mathcal{I},\ \forall (t,u)\in\mathcal{U}^{T} \tag{RB7}$$

$$\mathrm{free}(i,u) \qquad \forall i\in\mathcal{I},\ \forall (c,u)\in\mathcal{U}^{C}:\ c_i=c \tag{RB8}$$

$$\mathrm{free}(i,u) \qquad \forall i\in\mathcal{I},\ \forall (s,u)\in\mathcal{U}^{S}:\ s_i=s \tag{RB4}$$

Chú ý bất đối xứng: (RB7) phải viết dạng kéo theo vì $\theta_i$ là **biến**, còn
(RB8) và (RB4) lọc thẳng ở chỉ số vì $c_i,s_i$ là **hằng** của buổi học. Bất đối
xứng này hiện ra trong cả ba bản cài đặt.

### Hàm mục tiêu

$$\omega=\max_{i\in\mathcal{I}}\eta_i, \qquad
\omega\ \ge\ \max_{c\in\mathcal{C}}\sum_{i\,:\,c_i=c}p_i \tag{C11}$$

$$\boxed{\ \min\ \omega\ }$$

Bất đẳng thức trong (C11) là **chặn dưới hợp lệ**: một lớp có tổng $P$ tiết thì không
thể học xong trước tiết $P$, vì (C3) cấm lớp học hai buổi cùng lúc. Nó không đổi tập
nghiệm tối ưu, chỉ giúp engine chứng minh tối ưu sớm hơn.

### Ba chiều mã hoá (C3)–(C5) theo ba cách

Cùng một mô hình toán ở trên, ba chiều diễn đạt phần "tài nguyên dùng một lần tại
mỗi thời điểm" bằng ba cách khác nhau. **Đây là biến số mà bài 3.2 đo.**

**① OPL — đếm có điều kiện.** Hai đoạn giao nhau thì điểm bắt đầu muộn hơn luôn nằm
trong đoạn kia, nên (C3) tương đương: với mọi $i$, số buổi cùng lớp bắt đầu trong
$[\sigma_i,\eta_i)$ không quá 1.

$$\sum_{j\,:\,c_j=c_i}\mathbb{1}\bigl[\sigma_i\le\sigma_j<\eta_i\bigr]\ <\ 2 \qquad\forall i$$

Sinh $O(|\mathcal{I}|^2)$ tích có điều kiện — nguồn gốc của con số 17.9 s ở bảng benchmark.

**② DOcplex.cp — biến interval, `alternative` + `no_overlap`.** Mỗi buổi là một biến
interval $x_i$; mỗi tài nguyên dùng được sinh một interval tuỳ chọn; `alternative`
chọn đúng một.

$$\texttt{no\_overlap}\bigl(\{x_i : c_i=c\}\bigr)\quad\forall c\in\mathcal{C}$$

**③ OR-Tools — biến interval + literal hiện diện.** Cùng ý tưởng interval, nhưng
CP-SAT không có `alternative` nên phải dựng tay: $\pi_{i,t}\in\{0,1\}$ với
$\pi_{i,t}=1\iff\theta_i=t$, rồi `add_no_overlap` trên các interval tuỳ chọn.

Ba cách **tương đương về tập nghiệm** — đã kiểm chứng chéo ở mục dưới — nhưng khác
hẳn về sức lan truyền và chi phí mỗi nhánh.

## (c) Nguồn từng chiều

| Chiều | Nguồn | Phạm vi | Mã hoá |
|---|---|---|---|
| OPL | ✅+✍️ `timetabling.mod` của IBM **+ 44 dòng** | đầy đủ | int `Start[]` + tổng có điều kiện |
| DOcplex.cp | ✍️ viết mới | đầy đủ | interval + `alternative` + `forbid_extent` |
| OR-Tools | ✍️ viết mới | đầy đủ | interval + `add_no_overlap` + literal hiện diện |

Bản gốc để đối chiếu giữ nguyên tại `opl/timetabling_base_reference.mod`. Phần mở
rộng là **chèn thêm, không sửa** — `diff` cho 44 dòng thêm, 0 dòng đổi.

## Đính chính so với brief

Brief §2 mô tả bản OPL sẵn có là "chỉ có teacher skills + không trùng giờ". Đọc
code thật thì `timetabling.mod` giàu hơn hẳn. Nó đã có sẵn:

- phòng học và **phòng chuyên dụng** (`DedicatedRoomSet`) — brief không nhắc tới phòng
- thời lượng và số lần lặp mỗi môn
- thứ tự thời gian giữa các buổi cùng môn
- `classTeacher` — **chính là RB9** mà brief liệt kê như phần cần bổ sung
- giờ nghỉ giữa cặp môn kỵ nhau (`NeedBreak`)
- cấm dạy trùng môn hai lần trong ngày
- môn chỉ học buổi sáng (`MorningDiscipline`)
- mục tiêu min makespan

Thứ nó thật sự thiếu đúng là **availability windows**, như brief §6 điểm 2 đã nói.
⇒ Mô hình toán ở brief §4 cần viết lại theo mô hình gốc, và **bỏ mã hoá nhị phân**:
mã hoá thời điểm bằng biến nguyên của bản gốc chính là lý do bài này lọt trần
Community Edition.

## Kiểm chứng chéo

Ba chiều dựng độc lập, khác cách mã hoá, khác engine — mà **cùng ra một nghiệm
tối ưu** ở cả bốn cấu hình dữ liệu (60 lượt chạy của `make bench`, không lượt nào lệch):

| Cấu hình | OPL | DOcplex.cp | OR-Tools |
|---|---|---|---|
| `base + small` | 20 | 20 | 20 |
| `base + small + availability_small` | 21 | 21 | 21 |
| `base + large` | 44 | 44 | 44 |
| `base + large + availability` | 47 | 47 | 47 |

Đây là bằng chứng bản port trung thực. Không có kiểm chứng này thì mọi so sánh
hiệu năng phía dưới đều vô nghĩa — nhanh hơn mà giải sai bài thì không nói lên gì.

## (d) Quan sát cho phần so sánh

### Chi phí của tính khả dụng

| Bộ `large` | log₂ không gian | Makespan | OPL | DOcplex.cp | OR-Tools |
|---|---|---|---|---|---|
| không availability | 786.4 | 44 | 17.94 s | 0.67 s | 2.52 s |
| có availability | **780.3** | 47 | 8.60 s | 1.50 s | 2.42 s |

| Bộ `small` | Makespan | OPL | DOcplex.cp | OR-Tools |
|---|---|---|---|---|
| không availability | 20 | 0.39 s | 0.44 s | 0.051 s |
| có availability | 21 | 0.47 s | 0.36 s | 0.061 s |

Ba điều đáng nói:

1. **Thêm ràng buộc làm không gian tìm kiếm GIẢM** (786.4 → 780.3), dù số ràng
   buộc gần gấp đôi (2 120 → 3 947). Ràng buộc khả dụng chỉ cắt miền của biến sẵn
   có chứ không thêm biến mới. Community Edition tính trần theo *không gian tìm
   kiếm* chứ không theo *số ràng buộc* — nên còn nhiều chỗ để thêm ràng buộc nữa.
2. **Cái giá của tính khả dụng nằm ở chất lượng lời giải, không ở thời gian giải.**
   Makespan xấu đi 44 → 47, còn thời gian giải thì tuỳ chiều: OPL *nhanh hơn* hẳn
   (17.94 → 8.60 s) vì miền bị cắt bớt, DOcplex.cp chậm lại, OR-Tools gần như không đổi
   (2.52 → 2.42 s).
   Ràng buộc thực tế hơn làm lịch dài ra, chứ không làm bài toán khó hơn về tính toán.
3. **Hiện tượng đó lặp lại y hệt ở bộ nhỏ**, chỉ khác biên độ: makespan 20 → 21,
   OPL chậm lại một chút còn DOcplex.cp nhanh lên (0.44 → 0.36 s). Hai kích thước
   cùng nói một điều thì kết luận mới đứng được — mà muốn vậy thì bộ small phải có
   file availability của riêng nó, xem mục ngay dưới.

### Ràng buộc khả dụng chỉ có nghĩa khi nó nằm trong tầm dữ liệu

Ô `small+avail` của lưới 2×2 đã từng **rỗng nghĩa**: nó cho số trùng khít từng
chữ số với ô `small` ở cả ba chiều (makespan 20; 30 412 / 75 025 / 553 nhánh).
Không phải lỗi script, cũng không phải lỗi mô hình — mà vì cả bốn ô cùng dùng
`availability.dat`, một file viết cho bộ `large`:

| Tập | Nội dung bản `large` | Vào bộ `small` thì |
|---|---|---|
| `ClassBusySet` | `<"Z",42..44>`, `<"X",29>` | small chỉ có 4 ngày × 6 tiết = Time 0..23 ⇒ mọi mốc **ngoài tầm** |
| `DisciplineAvoidSet` | toàn môn `Sport` | small chỉ học French / Maths / Physics ⇒ **không khớp môn nào** |
| `TeacherBusySet` | Patrick (Sport), Odile (Economy), Marie-Laure (Geography, History), Paul (Physics) | ba người đầu dạy môn small không học; mốc của Paul là t = 33..35, cũng **ngoài tầm** |

Ràng buộc vẫn được sinh ra đủ cả — engine vẫn phải lan truyền chúng — nhưng
`Start > t ∨ End ≤ t` với `t = 42` là hằng đúng khi `End ≤ 23`. Không mốc nào cắt
được một nghiệm nào, nên số liệu không nhúc nhích một đơn vị.

Đây là quan sát đáng giữ: **một ràng buộc khả dụng chỉ đo được khi mốc thời gian và
tên tài nguyên của nó nằm trong tầm của chính bộ dữ liệu đang chạy.** Ràng buộc "có
mà không cắt" không báo lỗi ở bất cứ tầng nào — không phải lỗi cú pháp, không phải
lỗi kiểu, không làm bài vô nghiệm; nó chỉ lặng lẽ biến một ô thí nghiệm thành bản
sao của ô đối chứng. Dấu hiệu duy nhất là hai hàng số giống nhau đến từng chữ số —
thứ mà chỉ có yêu cầu *tất định* (1 worker, seed cố định) mới làm lộ ra được; với
số liệu dao động giữa các lần chạy thì hai hàng đó trông như "khác một chút", và
lỗi này đã lọt.

`data/timetable/availability_small.dat` là bản đúng tầm bộ small. Nguyên tắc dựng nó:

- **Giữ nguyên mật độ của bản large**, để hai ô "+avail" là cùng một loại can thiệp:
  large có 27 mốc trên 106 buổi học (0.255 mốc/buổi), chia `TeacherBusySet` :
  `ClassBusySet` : `DisciplineAvoidSet` = 15 : 4 : 8. Bộ small có 22 buổi học ⇒
  22 × 0.255 ≈ 5.6, làm tròn **6 mốc**, chia theo đúng tỉ lệ trên thành **3 : 1 : 2**.
- **Đủ cả ba nhóm RB7 / RB8 / RB4**, mỗi nhóm giữ đúng mô-típ của bản large: một
  giáo viên nghỉ trọn một buổi (Pierre, sáng ngày 2 — `t = 12..14`; anh dạy toàn bộ
  French, 14 trên 30 tiết của cả kỳ nên khoá anh lại là cắt vào chỗ chật nhất), một
  lớp bận tiết cuối ngày (`<"X",11>`, đúng mô-típ `<"X",29>` của bản large), một môn
  bị tránh ở tiết cuối ngày (`<"Maths",5>`, `<"Maths",17>`). Ngày đánh số từ 0, y
  như `availability.dat`.
- **Mọi mốc phải cắt thật.** Kiểm bằng cách chạy bộ small *không* availability
  nhưng ép một buổi học phủ đúng ô bị cấm: cả sáu ô đều vẫn cho lịch tối ưu
  makespan 20. Nghĩa là mỗi mốc loại bỏ nghiệm có thật, không phải ràng buộc thừa.

Chỗ cuối cùng đó không thừa lời: bản `large` có sẵn một ví dụ ràng buộc **thừa**.
`DisciplineAvoidSet` của nó cấm `Sport` ở tiết cuối buổi chiều, trong khi
`MorningDiscipline = {"Sport"}` đã ép mọi buổi Sport (dài 1 tiết) bắt đầu ở ba tiết
đầu ngày — nên tám mốc đó không loại thêm nghiệm nào. Bỏ hẳn `DisciplineAvoidSet`
khỏi bản large cho **đúng cùng một kết quả**: makespan 47, 13 305 nhánh, 183
conflicts. Vì thế RB4 của bộ small chọn `Maths`, môn không nằm trong
`MorningDiscipline`.

### Hiệu năng — bảng trung vị 5 lần chạy

Sinh bằng `make bench` → `results/bench.csv`. Seed và số worker cố định để tái lập.
Lưới đầy đủ **4 cấu hình × 3 chiều = 12 ô**, mỗi ô 5 lần chạy:

> **Quy ước đọc số.** Cột *Nhánh* và *Fails/Confl* là tất định, trích được chính xác
> tới từng đơn vị. Cột *Thời gian* là **trung vị 5 lần chạy trên một máy cụ thể** và
> dao động cỡ 10 % theo tải, nên đo lại sẽ ra số khác ở chữ số cuối. Mọi kết luận
> dưới đây vì thế nói bằng **bậc độ lớn và tỉ lệ**, không bằng chữ số cuối.

| Cấu hình | Chiều | Engine | Mã hoá | Obj | Thời gian | Nhánh | Fails/Confl |
|---|---|---|---|---|---|---|---|
| small | OPL | CP Optimizer | đếm có điều kiện | 20 | 0.39 s | 30 412 | 12 917 |
| small | DOcplex.cp | CP Optimizer | interval | 20 | 0.44 s | 75 025 | 33 825 |
| small | OR-Tools | CP-SAT | interval | 20 | **0.051 s** | 553 | 4 |
| small+avail | OPL | CP Optimizer | đếm có điều kiện | 21 | 0.47 s | 45 176 | 20 250 |
| small+avail | DOcplex.cp | CP Optimizer | interval | 21 | 0.36 s | 61 824 | 26 221 |
| small+avail | OR-Tools | CP-SAT | interval | 21 | **0.061 s** | 549 | 4 |
| large | OPL | CP Optimizer | đếm có điều kiện | 44 | 17.94 s | 216 066 | 96 460 |
| large | DOcplex.cp | CP Optimizer | interval | 44 | **0.67 s** | 34 194 | 7 037 |
| large | OR-Tools | CP-SAT | interval | 44 | 2.52 s | 15 439 | 236 |
| large+avail | OPL | CP Optimizer | đếm có điều kiện | 47 | 8.60 s | 125 151 | 55 086 |
| large+avail | DOcplex.cp | CP Optimizer | interval | 47 | **1.50 s** | 154 818 | 59 201 |
| large+avail | OR-Tools | CP-SAT | interval | 47 | 2.42 s | 13 305 | 183 |

> **Cả 12 ô đều tất định.** Trong mỗi ô, 5/5 lần chạy cho **đúng cùng một** số
> nhánh và số fails/conflicts (chỉ thời gian đồng hồ dao động; cột "Thời gian" là
> trung vị 5 lần). Ba chiều cũng cùng một objective ở cả 4 cấu hình — xem mục
> *Kiểm chứng chéo*. Điều này chỉ có được sau khi chiều OR-Tools cố định
> `num_workers = 1` + `random_seed = 0`: trước đó file mặc định 8 worker và bản
> chụp `results/bench.csv` cũ ghi 585/575/376 nhánh ở `small` cho ba lần chạy cùng
> một cấu hình. Số nhánh của bản 1 worker **cao hơn** bản 8 worker (đa luồng chạy
> nhiều chiến lược song song nên đích đến gần hơn) — đổi tốc độ lấy tính tái lập,
> và đó là đánh đổi bắt buộc: chính tính tất định mới làm lộ ra rằng ô
> `small+avail` từng là bản sao từng chữ số của ô `small`.

### Đọc bảng: hai phép so, mỗi phép đổi đúng một biến số

**Trục MÃ HOÁ** — OPL vs DOcplex.cp, *cùng engine CP Optimizer*:

| Cấu hình | đếm có điều kiện | interval | tỉ lệ |
|---|---|---|---|
| small | 0.39 s | 0.44 s | 0.9× (interval *chậm hơn*) |
| small+avail | 0.47 s | 0.36 s | 1.3× nhanh hơn |
| large | 17.94 s | 0.67 s | **27× nhanh hơn** |
| large+avail | 8.60 s | 1.50 s | **5.7× nhanh hơn** |

Ở bài nhỏ, mã hoá interval còn thua vì chi phí dựng mô hình lớn hơn phần lợi. Bài
càng lớn thì càng thắng đậm — vì cách đếm có điều kiện sinh ra số ràng buộc tăng
theo **bình phương** số khoá học, trong khi `no_overlap` chỉ là một ràng buộc toàn
cục cho mỗi tài nguyên.

Ô `small+avail` thêm một chi tiết: thêm ràng buộc khả dụng vào bộ nhỏ làm hai mã
hoá đi **ngược chiều nhau**. Đếm có điều kiện duyệt nhiều hơn hẳn (30 412 → 45 176
nhánh, 0.39 → 0.47 s) trong khi interval duyệt ít đi (75 025 → 61 824 nhánh,
0.44 → 0.36 s) — cùng một ràng buộc, một bên coi là gánh nặng, một bên coi là
thông tin cắt miền. Đủ để lật dấu của tỉ lệ: 0.9× thành 1.3×.

Đáng chú ý: ở `large+avail`, DOcplex.cp duyệt **nhiều nhánh hơn** OPL (154 818 so
với 125 151) mà vẫn nhanh hơn 5.7×. **Số nhánh và thời gian không đi cùng nhau** —
mỗi nhánh của mã hoá đếm-có-điều-kiện đắt hơn hẳn vì phải lan truyền qua hàng nghìn
tích có điều kiện.

**Trục ENGINE** — DOcplex.cp vs OR-Tools, *cùng mã hoá interval*:

| Cấu hình | CP Optimizer | CP-SAT | nhánh CPO | nhánh CP-SAT |
|---|---|---|---|---|
| small | 0.44 s | **0.051 s** | 75 025 | 553 |
| small+avail | 0.36 s | **0.061 s** | 61 824 | 549 |
| large | **0.67 s** | 2.52 s | 34 194 | 15 439 |
| large+avail | **1.50 s** | 2.42 s | 154 818 | 13 305 |

Hai engine đi hai lối rõ rệt. CP-SAT duyệt **ít hơn 2–136 lần** số nhánh nhờ học
mệnh đề xung đột, nhưng mỗi nhánh đắt hơn nhiều: ở `large` nó duyệt 15 439 nhánh
trong 2.52 s (**6 100 nhánh/giây**) trong khi CP Optimizer duyệt 34 194 nhánh trong
0.67 s (**51 000 nhánh/giây**) — chênh hơn 8× về chi phí mỗi nhánh. Ở hai cấu hình
nhỏ, cách của CP-SAT thắng tuyệt đối (6–9× nhanh hơn); ở hai cấu hình lớn, CP
Optimizer về trước — đúng với nhận
định ở brief §1 rằng CP Optimizer mạnh nhất ở bài lập lịch, nơi nó có 20 năm tối ưu
riêng cho biến interval.

Lưu ý cách đọc: khoảng cách "ít hơn 2–136 lần" **rộng hơn** con số ghi trước đây,
vì bản OR-Tools cũ chạy 8 worker — đa luồng cắt bớt số nhánh của luồng thắng cuộc
nhưng làm số đo không tái lập được. Số trong bảng nay là của một luồng đơn, tất định.

> Ghi nhớ khi đọc số: `fails` của CP Optimizer và `conflicts` của CP-SAT đếm hai
> thứ khác nhau, chỉ so được trong cùng một engine.

### Hai primitive CP Optimizer có mà CP-SAT không có

Chỗ này thấy rõ nhất khi đặt hai file Python cạnh nhau — cùng ngôn ngữ, cùng cách
mã hoá, chỉ khác thư viện.

**1. Chọn tài nguyên.** CP Optimizer có `alternative(master, [alt...])`: đúng một
lựa chọn hiện diện và tự đồng bộ thời gian với interval chính.

```python
mdl.add(mdl.alternative(x[i], list(alts_t.values())))          # docplex.cp
```

CP-SAT không có, phải dựng tay literal hiện diện cho từng cặp rồi tự buộc khớp:

```python
lit = model.new_bool_var(f"t_{i}_{tid}")                        # ortools
model.add(teacher[i] == tid).only_enforce_if(lit)
model.add(teacher[i] != tid).only_enforce_if(~lit)
```

**2. Lịch bận.** CP Optimizer có `forbid_extent(interval, F)` với hàm bậc thang —
khai báo thẳng lịch của tài nguyên, **không sinh thêm biến quyết định nào**:

```python
fn = CpoStepFunction(); fn.set_value(0, horizon, 1)             # docplex.cp
for t in busy: fn.set_value(t, t + 1, 0)
mdl.add(mdl.forbid_extent(xt[i][tid], fn))
```

CP-SAT phải bung thành phép tuyển kèm **một biến bool cho mỗi cặp (khoá học, thời
điểm bận)**:

```python
after = model.new_bool_var(...)                                 # ortools
model.add(start[i] > t).only_enforce_if([lit, after])
model.add(end[i] <= t).only_enforce_if([lit, ~after])
```

Đây chính là "20+ năm chuyên biệt cho scheduling với interval variable" mà brief §1
nói tới, ở dạng cụ thể sờ được.

## Chạy

```bash
make run P=models/3.2_timetable

# lưới benchmark 4 cấu hình × 3 chiều × 5 lần
make bench

# đo chi phí của availability: bỏ file availability.dat đi
python3 models/3.2_timetable/ortools/timetable_sat.py \
    data/timetable/base.dat data/timetable/large.dat

# bộ small dùng file availability RIÊNG — availability.dat viết cho bộ large,
# mọi mốc của nó nằm ngoài tầm Time 0..23 của bộ small nên không cắt được gì:
python3 models/3.2_timetable/ortools/timetable_sat.py \
    data/timetable/base.dat data/timetable/small.dat \
    data/timetable/availability_small.dat

# chiều OR-Tools mặc định --workers 1 --seed 0 (tái lập, PLAN.md §2.4).
# Chỉ nới ra khi muốn ĐO lợi ích đa luồng — số liệu khi đó không tái lập được:
python3 models/3.2_timetable/ortools/timetable_sat.py \
    data/timetable/base.dat data/timetable/large.dat --workers 8
```
