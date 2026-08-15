# Kế hoạch thi công báo cáo CP

Tài liệu này biến bản đặc tả nội dung (brief, giữ ở máy — không theo git) thành các
gói việc chạy được. Brief chốt *báo cáo phải có gì*; file này nói **làm gì, theo thứ
tự nào, xong khi nào thì tính là xong**.

Quyết định phạm vi đã chốt:

- **5 notebook**, chia theo 3 phần của brief + intro + tổng hợp.
- **Đủ 3 chiều cho cả 6 bài** — kể cả bài 2.2 và 3.2 vốn không có mẫu DOcplex.cp.
- **Benchmark định lượng chỉ ở bài 3.2**; năm bài còn lại so sánh định tính.

---

## 1. Môi trường — đã kiểm chứng bằng cách chạy thật

| Chiều | Công cụ | Trạng thái |
|---|---|---|
| OPL | `oplrun.exe`, CPLEX Studio **Community 22.2** trên `D:\` | ✅ giải được `color.mod`, `sched_jobshop.mod`, N-Queens tự viết |
| DOcplex.cp | `docplex` 2.32.264 (pip, WSL) → `cpoptimizer.exe` | ✅ giải được N-Queens |
| OR-Tools | `ortools` 9.14.6206, native Linux | ✅ |
| Notebook | jupyter, nbconvert, pandas, matplotlib | ✅ có sẵn |

`make check` xác nhận lại cả ba bất cứ lúc nào.

**Bản `.mod` gốc đã có đủ trong máy** tại
`D:\Program Files\IBM\ILOG\CPLEX_Studio_Community222\opl\examples\opl\`:
`color`, `sched_jobshop` (+`.dat`), `sports`, `timetabling` (+3 `.dat`).
⇒ Không cần fetch link IBM, **né hẳn rủi ro 404** mà brief §3 và §6 cảnh báo.

**Ví dụ DOcplex.cp gốc** đã sparse-clone về `vendor/docplex/examples/cp/`:
`basic/color.py`, `basic/n_queen.py`, `visu/job_shop_basic.py` (+`data/jobshop_ft06.data`),
`jupyter/sports_scheduling.ipynb`.

---

## 2. Bốn ràng buộc cứng phát hiện được — ảnh hưởng trực tiếp tới mô hình

### 2.1 Community Edition chặn ở không gian tìm kiếm 2^1000

Thông báo thật khi vượt trần:

```
*** FATAL[ENGINE_001]: Exception from IBM ILOG Concert: Problem size limit exceeded.
```

Đã xác nhận: N-Queens `n=200` (≈2^1529) bị từ chối, `n=8` chạy bình thường.

**Trần này KHÔNG cản bài 3.2** — miễn là dùng mã hoá thời điểm bằng biến nguyên
như `timetabling.mod` gốc, thay vì mã hoá nhị phân như brief §4 phác thảo. Đã đo
thật (xem §2.5):

| Cách mã hoá | Số biến | log₂ không gian | Community? |
|---|---|---|---|
| Bool `X[c,t,d,p]` + `Y[c,s,d,p]` (brief §4) | 1600 + 1200 | ≈2800 (ước tính) | ❌ vượt |
| Int `Start[]`/`teacher[]`/`room[]` — **bản OPL gốc, bộ large** | 449 | **786.4 (đo được)** | ✅ |
| Int, **bản OPL gốc + availability**, bộ large | 449 | **780.3 (đo được)** | ✅ |

⇒ Kết luận: **bỏ mã hoá nhị phân của brief §4, dùng mã hoá biến nguyên**. Đây vẫn
là một nội dung học thuật hay — CP-SAT sinh ra để nuốt hàng vạn biến bool, còn CP
Optimizer thiên về biến miền rời rạc và biến interval; chọn cách mã hoá theo
engine chính là một kết luận của báo cáo.

> ⚠️ Nếu có **license academic** (miễn phí qua IBM Academic Initiative) thì trần
> biến mất hoàn toàn. Vẫn nên đăng ký, nhưng **không còn là điều kiện chặn**.

### 2.2 `allDifferent` của OPL không nhận mảng biểu thức

`allDifferent(dexpr int[])` → *"not available in context CP"*. Phải vật chất hoá
thành `dvar` phụ rồi buộc bằng `==`. Bản DOcplex.cp cùng engine viết thẳng
`all_diff(x[i] + i for i in ...)`.

⇒ Đây là **dẫn chứng số một** cho trục "khác biệt do ngôn ngữ" của brief. Và nó có
hệ quả đo được: N-Queens n=8 cùng engine CP Optimizer, bản OPL tốn **440 nhánh /
198 fails**, bản DOcplex.cp chỉ **255 / 99** — biến phụ đã làm đổi cả không gian
tìm kiếm. Cùng engine, cùng mô hình toán, khác số liệu, chỉ vì ngôn ngữ ép cách
viết khác.

**Tinh chỉnh quan trọng của luận điểm trên** (rút ra sau khi làm xong bài 2.1):
khác biệt do ngôn ngữ **không phải lúc nào cũng có**. Bài 2.1 job-shop, cùng engine
CP Optimizer, hai chiều OPL và DOcplex.cp chênh nhau **0.43 %** số nhánh và trả về
**cùng một lịch, từng con số trùng khít** — trong khi bài 1.2 chênh tới ~73 %.

Vì sao khác nhau: ở bài 1.2, `allDifferent` của OPL không nhận mảng biểu thức nên
**ép người viết dựng một mô hình toán khác** (thêm $2n$ biến phụ). Ở bài 2.1, mọi
khái niệm ánh xạ một-một giữa hai ngôn ngữ (`dvar interval` ↔ `interval_var`,
`endBeforeStart` ↔ `end_before_start`, `noOverlap` ↔ `no_overlap`) nên engine nhận
đúng cùng một bài toán.

⇒ Kết luận cho báo cáo: **ngôn ngữ chỉ ảnh hưởng tới hiệu năng khi nó ép viết một
mô hình toán khác đi.** Khác biệt thuần cú pháp (ví dụ `dvar sequence` là kiểu
hạng nhất trong OPL, còn Python phải gom nhóm bằng vòng lặp) dừng ở mức dễ đọc,
không lan xuống engine. Đây là kết luận sắc hơn hẳn "OPL chậm hơn DOcplex.cp".

### 2.3 Thiếu `using CP;` thì OPL rơi vào context CPLEX

Báo *"Function allDifferent(...) not available in context CPLEX"*. Liên hệ thẳng
tới sơ đồ kiến trúc tầng ở brief §1b: cùng một file `.mod` gọi được hai engine
khác nhau, và dòng đầu tiên là thứ quyết định.

### 2.4 CP-SAT không tất định giữa các lần chạy

Cùng model N-Queens n=8, hai lần chạy cho `branches` = 475 rồi 0 — CP-SAT chạy đa
luồng, worker nào về đích trước thì số liệu theo worker đó.

⇒ Phần benchmark bài 3.2 **bắt buộc** cố định `num_search_workers=1` và
`random_seed`, và mỗi điểm đo phải là **trung vị của ít nhất 5 lần chạy** — 5 là
sàn, không phải mặc định tuỳ chỉnh được xuống thấp hơn. Không làm vậy thì bảng số
liệu vô nghĩa. Phạm vi đo đầy đủ (**4 cấu hình**) đặc tả ở §WP6.

Ngoài ra `fails` (CP Optimizer) và `conflicts` (CP-SAT) đếm hai thứ khác nhau —
báo cáo phải nói rõ là **không so trực tiếp**, chỉ so trong cùng một engine.

**Quy ước đọc số của toàn báo cáo.** Số nhánh và số fails/conflicts là **tất định**,
trích được chính xác tới từng đơn vị. Thời gian thì không: nó là **trung vị 5 lần
chạy trên một máy cụ thể** và dao động cỡ 10 % theo tải, nên hai lần dựng báo cáo
cho hai con số khác nhau ở chữ số cuối. ⇒ Mọi kết luận phải dựa trên **bậc độ lớn
và tỉ lệ**, không dựa trên chữ số cuối; và bảng nào quyết bằng một lần chạy duy nhất
thì phải từ chối phân thắng bại khi chênh lệch nằm trong nhiễu — `axis_tables()`
ghi "≈ ngang nhau" dưới ngưỡng `NEGLIGIBLE_TIME_DIFF` của `tools/nbutil.py`.

### 2.5 `timetabling.mod` giàu hơn brief giả định — và mở rộng được

Brief §2 mô tả bản OPL sẵn có là "chỉ có teacher skills + không trùng giờ". Đọc
code thật thì nó có **nhiều hơn thế đáng kể**: phòng học và phòng chuyên dụng
(`DedicatedRoomSet`), thời lượng và số lần lặp mỗi môn, thứ tự thời gian giữa các
buổi cùng môn, `classTeacher` (**chính là RB9** mà brief liệt kê như phần bổ sung),
giờ nghỉ giữa cặp môn kỵ nhau (`NeedBreak`), cấm dạy trùng môn trong ngày, môn chỉ
học buổi sáng (`MorningDiscipline`), và mục tiêu **min makespan**.

Thứ nó thật sự thiếu đúng là **availability windows** — như brief §6 điểm 2 đã nói.

**Đã kiểm chứng bằng cách chạy thật** (bộ `base.dat` + `large.dat`, 3 lớp, 8 giáo
viên, 8 phòng, 8 ngày × 6 tiết):

| Mô hình | Biến | Ràng buộc | log₂ không gian | Makespan | Thời gian (trung vị 5 lần) |
|---|---|---|---|---|---|
| `timetabling.mod` gốc | 449 | 2 120 | 786.4 | 44 (tối ưu) | 17.94 s |
| + RB7/RB8/RB4 availability | 449 | 3 947 | **780.3** | 47 (tối ưu) | **8.60 s** |

Hai điều đáng chú ý:

1. **Thêm ràng buộc làm không gian tìm kiếm GIẢM, không tăng** (786.4 → 780.3).
   Ràng buộc khả dụng chỉ cắt miền của biến sẵn có chứ không thêm biến mới. Số
   ràng buộc tăng gần gấp đôi nhưng đại lượng bị Community Edition tính trần là
   *không gian tìm kiếm*, không phải *số ràng buộc*. ⇒ Còn nhiều chỗ để thêm ràng buộc.
2. **Cái giá của tính khả dụng nằm ở chất lượng lời giải, không ở thời gian giải.**
   Makespan xấu đi 44 → 47, nhưng thời gian giải lại *giảm* 17.94 s → 8.60 s: miền
   bị cắt bớt nên engine tìm và chứng minh tối ưu nhanh hơn. Ràng buộc thực tế hơn
   làm lịch dài ra, chứ không làm bài toán khó hơn về mặt tính toán.

Phần mở rộng được viết dưới dạng **chèn thêm 44 dòng, không sửa một dòng nào** của
bản gốc IBM (`diff` xác nhận), nên trong báo cáo có thể trình bày đúng phần delta.

> 📎 **Không có §2.6** — đánh số nhảy từ 2.5 sang 2.7 là *cố ý*. Số hiệu §2.7 và
> §2.8 đã được trích dẫn trong mã (`tools/runner.py`, `tools/nbutil.py`) và trong
> các `NOTES.md`; đánh số lại sẽ làm hỏng những tham chiếu đó. Không có mục nào bị
> mất.

### 2.7 Bẫy lớn nhất gặp phải: hai mẫu chính thức trùng tên nhưng khác bài

Xảy ra ở **hai** trong sáu bài, và cả hai lần đều suýt làm hỏng bảng so sánh:

| Bài | Mẫu OPL của IBM | Mẫu docplex của IBM | Có phải cùng bài? |
|---|---|---|---|
| 2.1 Job-shop | `sched_jobshop.dat` → makespan **45** | `jobshop_ft06.data` → makespan **55** | ❌ hai **instance** khác nhau |
| 3.1 Sports | `sports.mod` — double round-robin có sân nhà/khách, **min tổng break** | `sports_scheduling.ipynb` — lịch NFL hai bảng, **không có khái niệm home/away nên không có break**, max tuần liên bảng | ❌ hai **bài toán** khác nhau |

Nếu cứ mỗi bên lấy một mẫu rồi xếp số liệu cạnh nhau thì bảng so sánh đang so hai
thứ khác nhau — mà nhìn bảng thì không thấy được.

⇒ **Quy tắc:** trước khi coi hai mẫu là cùng một bài, phải **đọc và chạy cả hai**
rồi đối chiếu kết quả. `manifest.json` ghi khoá `variant` cho từng chiều, và khối
`two_official_variants` khi có xung đột; `cross_check()` chỉ đối chiếu các chiều
**cùng variant**.

### 2.8 CP-SAT thiếu ít ràng buộc toàn cục hơn dự đoán — rào cản thật là reify

Giả định ban đầu của kế hoạch (CP-SAT không có `allowedAssignments`, `inverse`,
`count`) **sai 3/4**. Đo thật trên `sports.mod`:

| `sports.mod` dùng | CP-SAT | Biến phụ phải bù (n=6) |
|---|---|---|
| `allowedAssignments` | ✅ `add_allowed_assignments` | 0 |
| `allDifferent` | ✅ `add_all_different` | 0 |
| `inverse` | ✅ `add_inverse` (bắt buộc miền `0..k-1`, phải dời gốc chỉ số) | 0 |
| `count` | ❌ **không có** → 1-hot | **180** bool |
| dùng ràng buộc như **biểu thức** (reify tại chỗ) | ❌ phải vật chất hoá | 99 bool + 21 int |

Tổng **285 biến phụ**: CP-SAT 501 biến / 808 ràng buộc so với CP Optimizer 216 /
271 (**+132 %**).

⇒ Khoảng cách giữa hai engine **không nằm ở danh mục ràng buộc toàn cục** mà ở chỗ:
trong CP Optimizer một ràng buộc đồng thời là một **biểu thức** dùng ngay được tại
chỗ (`(a >= b) + (c < d) <= 1`), còn CP-SAT phải tạo biến bool trung gian và buộc
hai chiều bằng `only_enforce_if`. Đây là kết luận sắc hơn hẳn "CP-SAT thiếu ràng
buộc X".

**Trần Community đo được ở bài này:** $n=6$ là mức lớn nhất CP Optimizer Community
chạy nổi (510.6/1000). $n=8$ và $n=10$ — đúng cỡ bản gốc IBM — đều `FATAL[ENGINE_001]`
ở **cả hai** chiều CP Optimizer, trong khi CP-SAT giải tối ưu cả hai, dù mô hình
của nó nhiều hơn 132 % số biến. Giới hạn ở đây là **giấy phép**, không phải năng
lực engine.

---

## 3. Hai quy ước hạ tầng

**`manifest.json` mỗi bài** — khai báo cho từng chiều: file model, tham số, nguồn
(`official` ✅ / `new` ✍️). Runner và notebook đọc chung ⇒ bảng ✅/✍️ trong báo cáo
không bao giờ lệch với code thật.

**Dòng `RESULT {json}`** cuối mỗi model, ở cả ba chiều ⇒ runner thu số liệu đồng
nhất thay vì đọc ba định dạng log. Chiều OPL lấy số từ `cp.info.numberOfBranches`,
`cp.info.numberOfFails`, `cp.info.solveTime` trong khối `execute`.

**Dữ liệu dùng chung.** Mỗi bài có đúng một nguồn dữ liệu trong `data/`, cả ba
chiều cùng đọc. Nếu ba chiều chạy trên ba bộ dữ liệu khác nhau thì mọi so sánh
đều mất giá trị.

**Cấu trúc `NOTES.md` chuẩn cho mọi bài.** Bốn mục, đúng thứ tự này:

| Mục | Nội dung |
|---|---|
| **(a) Phát biểu bài toán** | bằng lời, rõ dữ liệu vào/ra và ràng buộc |
| **(b) Mô hình toán học** | **chi tiết**, LaTeX: bảng tập hợp · bảng tham số · **bảng biến quyết định** · ràng buộc **đánh số** (C1),(C2)… · hàm mục tiêu. Dùng chung cho cả ba chiều |
| **(c) Nguồn từng chiều** | bảng ✅ lấy mẫu / ✍️ viết mới, kèm link và bản quyền |
| **(d) Quan sát so sánh** | trục NGÔN NGỮ (OPL vs DOcplex.cp) và trục ENGINE (DOcplex.cp vs OR-Tools), kèm số liệu thật đo được |

Mục (b) là phần bắt buộc chi tiết nhất. Mẫu tham chiếu:
`models/3.2_timetable/NOTES.md`. Khi ba chiều mã hoá khác nhau, mục (b) nêu **một**
mô hình toán rồi thêm một tiểu mục nói rõ ba cách mã hoá của cùng mô hình đó.

---

## 4. Phân phối công việc

### Phase 0 — Hạ tầng ✅ XONG

| Hạng mục | File |
|---|---|
| Cây thư mục | `models/` `data/` `notebooks/` `report/` `results/` `tools/` `vendor/` |
| Cầu nối OPL | `tools/oplrun.sh` — dịch đường dẫn WSL→Windows |
| Cầu nối CP Optimizer | `tools/cpo_env.py` — trỏ docplex.cp sang `cpoptimizer.exe` |
| Chạy & thu số liệu | `tools/runner.py` — `--suite`, `--all`, xuất json/csv |
| Chẩn đoán | `tools/check_env.py` — `make check` |
| Điều phối | `Makefile`, `requirements.txt`, `README.md` |
| Ví dụ IBM | `vendor/docplex/examples/cp/` (sparse clone) |
| Bài mẫu chạy thử | `models/1.2_nqueens/` — cả 3 chiều đã chạy ra kết quả |

### Phase 1 — Sáu gói bài toán

Mỗi gói giao nộp: 3 file model + `manifest.json` + `NOTES.md` (ghi nguồn từng
chiều và các khác biệt ngôn ngữ/engine quan sát được) + dữ liệu chung trong `data/`.

| Gói | Bài | OPL | DOcplex.cp | OR-Tools | Ghi chú thi công |
|---|---|---|---|---|---|
| **WP1** | 1.1 Tô màu | ✅ `color.mod` (cục bộ) | ✅ `basic/color.py` | ✍️ viết mới | Dữ liệu 6 nước châu Âu, 4 màu. Cần script sinh `.dat` từ JSON để 3 chiều chung dữ liệu |
| **WP2** | 1.2 N-Queens | ✍️ **đã xong** | ✅ **đã xong** | ✅ **đã xong** | ✅ **xong cả gói** — `NOTES.md` đã có (182 dòng) |
| **WP3** | 2.1 Job-shop | ✅ `sched_jobshop.mod` | ✅ `visu/job_shop_basic.py` | ✍️ viết mới | **Bài trọng tâm** — bài duy nhất có sẵn cả 3 bản chính thức. Dữ liệu chung: `ft06`. Thêm Gantt |
| **WP4** | 2.2 Employee | ✍️ viết mới | ✍️ viết mới | ✅ mẫu Google | IBM không có bản CP — chỉ có `nurses` bản MILP. Đây là **khoảng trống của hệ IBM**, một kết luận của báo cáo |
| **WP5** | 3.1 Sports | ✅ `sports.mod` | ✅ `jupyter/sports_scheduling` | ✍️ viết mới | ⚠️ **hai mẫu chính thức là hai bài toán khác nhau** — xem §2.7 |
| **WP6** | 3.2 Timetable | ✅+✍️ `timetabling.mod` + 44 dòng availability | ✍️ viết mới | ✍️ viết mới | **Đã đổi hướng — xem dưới.** Bài duy nhất có benchmark |

#### WP6 chi tiết — lấy `timetabling.mod` làm nền

Thay vì viết mới cả ba chiều, bài 3.2 lấy **bản OPL chính thức làm mốc**, rồi mỗi
chiều bổ sung availability lên trên đó. Cách này tốt hơn hẳn phương án ban đầu:

- Mốc so sánh là code IBM viết, không phải code ta viết ⇒ khách quan hơn.
- Cô lập đúng **một** biến số: ba chiều giải cùng một bài, chỉ khác ngôn ngữ/engine.
- Đo được **chi phí của tính khả dụng** bằng cách chạy có/không phần bổ sung.

| Chiều | Phạm vi | Mã hoá | Trạng thái |
|---|---|---|---|
| OPL | **đầy đủ** — `timetabling.mod` nguyên bản + 44 dòng RB7/RB8/RB4 | int `Start[]` + tổng có điều kiện (nguyên bản IBM) | ✅ **xong, chạy tối ưu** — makespan **47**, 8.60 s |
| OR-Tools | **đầy đủ** — port trọn mô hình gốc + availability | **interval + `AddNoOverlap`** | ✅ **xong, chạy tối ưu** — makespan **47**, 2.42 s |
| DOcplex.cp | **linh hoạt** — bám phần cốt lõi, không nhất thiết mọi ràng buộc | **interval + `no_overlap`** | ✅ **xong, chạy tối ưu** — makespan **47**, 1.50 s |

Ba chiều **cùng cho makespan tối ưu 47** ⇒ kiểm chứng chéo của WP6 đã đạt
(nguồn: `results/bench.csv`, cấu hình `large+avail`, trung vị 5 lần chạy. Chiều
OR-Tools nay mặc định 1 worker + seed 0 theo §2.4; `results/runs.csv` vẫn là bản
chụp cũ chạy 8 worker, cần `make run-all` lại).

Hai chiều Python mô hình hoá "tài nguyên dùng một lần tại mỗi thời điểm" bằng
**biến interval + noOverlap**, thay cho tổng có điều kiện của bản OPL gốc. Đó vừa
là cách viết tự nhiên của cả hai engine, vừa tạo ra so sánh đáng giá: *cùng một
bài, cách cổ điển (đếm có điều kiện) so với cách dùng biến interval chuyên cho lập
lịch.* Báo cáo ghi rõ ba chiều dùng ba cách mã hoá và **vì sao** — đây là kết quả,
không phải sự thiếu nhất quán.

**Dữ liệu dùng chung tuyệt đối.** Cả ba chiều đọc đúng những file `.dat` gốc của
IBM (`data/timetable/*.dat`) qua `tools/opl_dat.py` — một trình đọc định dạng `.dat`
viết cho dự án. Không duy trì bản JSON song song, nên không có đường nào để dữ
liệu ba chiều lệch nhau.

**Đặc tả benchmark WP6.** Đo trên **đúng 4 cấu hình** — tích Descartes
{gốc, +availability} × {small, large}, tức `small`, `small+avail`, `large`,
`large+avail` — mỗi cấu hình × 3 chiều = 12 điểm đo. Seed cố định, mỗi điểm đo lấy
**trung vị của ≥5 lần chạy** (§2.4). Bốn cấu hình và ngưỡng 5 lần chạy đều là bắt
buộc: bỏ bớt một cấu hình thì mất một ô của bảng 2×2, và dưới 5 lần chạy thì trung
vị không lọc nổi nhiễu của CP-SAT.

Thứ tự đề nghị: **WP2 → WP1 → WP3 → WP5 → WP4 → WP6**. Lý do: làm các bài có sẵn
mẫu trước để chốt khuôn `NOTES.md` và cách trình bày, để dành hai bài phải tự viết
nhiều nhất (2.2, 3.2) lại sau cùng khi khuôn đã ổn định.

WP6 phụ thuộc WP4 (cùng họ ràng buộc phủ/không trùng, tái dùng được cách viết).

### Phase 2 — Năm notebook

| Notebook | Nội dung |
|---|---|
| `00_intro_taxonomy.ipynb` | Brief §1 + §1b: 5 dạng bài CP, sơ đồ kiến trúc tầng, luận điểm ngôn ngữ-vs-engine, làm rõ CPLEX ≠ DOcplex |
| `01_combinatorial.ipynb` | Bài 1.1, 1.2 |
| `02_scheduling.ipynb` | Bài 2.1, 2.2 + Gantt |
| `03_assignment.ipynb` | Bài 3.1, 3.2 + bảng benchmark 3.2 |
| `99_comparison.ipynb` | Tổng hợp: bảng ✅/✍️ sinh từ `manifest.json`, đối chiếu ràng buộc có sẵn của hai engine, kết luận |

Mỗi bài trong notebook giữ đúng thứ tự:
**phát biểu → mô hình toán → code 3 chiều → quan sát so sánh**.

> Thứ tự này **thay cho** thứ tự ở brief §0 (vốn để code trước mô hình toán). Lý do:
> mô hình toán là hợp đồng chung mà cả ba chiều cùng cài đặt — đọc nó trước thì
> ba đoạn code sau đó chỉ còn là ba cách diễn đạt cùng một thứ, thay vì ba đoạn
> code rời rạc phải tự suy ra điểm chung.

Notebook **không nhúng lại code model**; nó đọc file từ `models/` và gọi
`tools/runner.py`. Như vậy code in trong báo cáo luôn là code vừa chạy ra kết quả
ngay bên dưới, không có đường nào để hai thứ lệch nhau.

### Phase 3 — Xuất bản và kiểm chứng

- `report/build.sh`: `nbconvert --execute` từng notebook → HTML → gộp `index.html`.
- Kiểm chứng cuối:
  - [x] cả 5 notebook chạy sạch từ kernel mới *(`make html` ngày 2026-08-15 chạy
        `nbconvert --execute` cả 5 notebook rồi xuất HTML: **0 ô lỗi**, 9 hình
        sinh ra đủ (0/2/2/2/3) và có mặt trong HTML)*
  - [x] `make run-all` xanh toàn bộ 18 model *(`results/runs.csv`: 18/18 hàng `ok=True`,
        6 bài × 3 chiều; `make check` xanh cả ba engine)*
  - [x] không file nào import `docplex.mp` *(quét toàn repo: chỉ nhắc tên trong văn
        xuôi để phân biệt paradigm, không có import nào)*
  - [x] mọi link trích dẫn còn sống *(21 URL trích trong `README.md`, `PLAN.md`,
        bản brief và 6 `NOTES.md` — kiểm ngày 2026-08-14, tất cả trả
        HTTP 200 sau khi theo redirect; trang IBM docs có lúc trả 503 tạm thời,
        thử lại 3 lần đều 200)*
  - [x] bảng ✅/✍️ trong báo cáo khớp `manifest.json` *(bảng được **sinh** từ manifest
        qua `tools/nbutil.py::show_source_matrix`, không có đường nào để lệch)*
  - [x] mọi số liệu benchmark tái lập được (seed cố định) *(`tools/bench_timetable.py`
        nay đủ **4 cấu hình / 5 lần chạy**; `results/bench.csv` đo lại toàn bộ ở
        cấu hình 1 worker + seed cố định — **12/12 ô tất định**, 5/5 lần trùng khít
        `branches`/`fails`. Mọi model CP-SAT của 6 bài đều đã cố định worker + seed.
        `results/runs.csv` đã chạy lại bằng `make run-all` ngày 2026-08-15 nên
        không còn số của bản 8 worker — xem §WP6)*
  - [x] HTML xuất ra đọc được độc lập *(`report/html/` dựng lại ngày 2026-08-15,
        mọi hình nhúng thẳng dạng `data:image/png` nên mở bằng trình duyệt là đọc
        được, không cần chạy lại notebook. **Chưa đẩy lên `gh-pages`** — nhánh đó
        vẫn là bản 2026-08-13, chạy `make pages` để đồng bộ)*

---

## 5. Tiêu chí nghiệm thu

Báo cáo coi là xong khi:

1. Sáu bài × ba chiều = **18 model chạy được**, cùng dữ liệu trong mỗi bài.
2. Mỗi bài đủ bốn mục theo cấu trúc `NOTES.md` chuẩn ở §3, đúng thứ tự
   **phát biểu → mô hình toán → code → so sánh**.
3. **Mô hình toán của mọi bài phải chi tiết**: bảng tập hợp, bảng tham số, bảng
   biến quyết định, ràng buộc đánh số, hàm mục tiêu — không viết tắt, không mô tả
   suông. Dùng chung cho cả ba chiều.
4. Mỗi bài chỉ rõ chiều nào lấy mẫu chính thức, chiều nào viết mới, kèm nguồn.
5. **Mỗi bài có kiểm chứng chéo**: ba chiều cho cùng nghiệm tối ưu (hoặc cùng kết
   luận khả thi). Không có bước này thì mọi so sánh hiệu năng đều vô nghĩa.
6. Có ít nhất một dẫn chứng **khác biệt do ngôn ngữ** (OPL vs DOcplex.cp, cùng
   engine) và một dẫn chứng **khác biệt do engine** (DOcplex.cp vs OR-Tools, cùng
   ngôn ngữ) — nêu cụ thể, không nói chung chung.
7. HTML xuất ra đọc được độc lập, không cần chạy lại notebook.

---

## 6. Rủi ro còn lại

| Rủi ro | Mức | Xử lý |
|---|---|---|
| ~~Trần 2^1000 chặn bài 3.2~~ | ~~Cao~~ → **Đã loại** | Đo thật: bộ large + availability chỉ dùng 780/1000. Dùng mã hoá biến nguyên là đủ (§2.1, §2.5) |
| Hai chiều Python của WP6 dùng mã hoá khác bản OPL ⇒ so sánh kém chặt | Trung bình | Chủ động biến thành nội dung: nêu rõ ba cách mã hoá và lý do (§WP6) |
| ~~`sports.mod` dùng ràng buộc CP-SAT không có tương đương~~ | ~~Trung bình~~ → **Đã đo, nhẹ hơn dự đoán** | CP-SAT có sẵn 3/4; chỉ thiếu `count`. Rào cản thật là **không reify được biểu thức tại chỗ** (§2.8) |
| Hai mẫu chính thức cùng tên nhưng khác bài (gặp ở 2.1 và 3.1) | **Cao** | Luôn đọc và chạy cả hai trước khi coi là cùng một bài; ghi `variant` vào `manifest.json` (§2.7) |
| Số liệu CP-SAT không tái lập | Trung bình | Cố định worker + seed, lấy trung vị (§2.4) |
| `job_shop_basic.py` phụ thuộc module `visu` (matplotlib) | Thấp | Đã có matplotlib; nếu vướng thì tách phần vẽ ra khỏi phần giải |
| Notebook chạy lâu do gọi `oplrun.exe` qua interop | Thấp | Mỗi lần gọi ~0.3s, chấp nhận được |
