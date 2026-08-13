/* Bài 2.2 — Employee / Shift Scheduling có nguyện vọng | Chiều OPL (engine CP Optimizer)
 * ---------------------------------------------------------------------------
 * Nguồn: ✍️ VIẾT MỚI.
 *
 * IBM KHÔNG phát hành bản CP nào của bài xếp ca nhân sự. Ví dụ `nurses` đi kèm
 * CPLEX Studio 22.2 tồn tại, nhưng nó là bản **MILP chạy trên engine CPLEX**:
 *   - `nurses.mod` KHÔNG có dòng `using CP;` ⇒ rơi vào context CPLEX;
 *   - nó khai `dvar float+ NurseWorkTime[...]` — biến LIÊN TỤC, thứ context CP
 *     của OPL không nhận;
 *   - chính file `.oplproject` của IBM ghi: "Nurses Scheduling model, MIP".
 * Bằng chứng đầy đủ ở NOTES.md mục (c). Vì vậy file này viết mới hoàn toàn, lấy
 * mô hình của ví dụ chính thức Google OR-Tools làm phát biểu bài toán.
 *
 * Chạy:
 *   tools/oplrun.sh models/2.2_employee/opl/employee.mod data/employee/employee.dat
 *
 * GHI CHÚ NGÔN NGỮ (điểm so sánh với DOcplex.cp, CÙNG engine CP Optimizer)
 * ------------------------------------------------------------------------
 * 1. OPL đánh chỉ số mảng biến TRỰC TIẾP bằng phần tử của {string}:
 *        dvar boolean x[Employees][Days][Shifts];
 *    Một dòng khai báo này đưa cả 105 biến vào engine, ĐÚNG THỨ TỰ (e,d,s).
 *    Python không có kiểu "mảng đánh chỉ số bằng tập hợp", nên bản docplex.cp
 *    phải dựng dict {(e,d,s): binary_var} — và docplex chỉ đẩy biến xuống engine
 *    theo thứ tự chúng XUẤT HIỆN LẦN ĐẦU trong ràng buộc, không theo thứ tự tạo.
 *    Hệ quả đo được: cùng engine, cùng mô hình, khác số nhánh. Xem NOTES.md (d).
 *
 * 2. `req[e][d][s]` là THAM SỐ tính sẵn từ tuple set ShiftRequests bằng một biểu
 *    thức ngay trong phần khai báo. OPL cho định nghĩa mảng dữ liệu bằng công
 *    thức; Python phải viết vòng lặp.
 *
 * 3. Ràng buộc có NHÃN (ctOnePerShift, ctBalanceLow...). Nhãn là khái niệm của
 *    NGÔN NGỮ OPL, không phải của engine — nó phục vụ conflict/relaxation
 *    iterator. Hai chiều Python không có tương đương trực tiếp.
 *
 * 4. Khối `execute` KHÔNG đọc được `dexpr`. Cái bẫy ở đây: để in được giá trị
 *    mục tiêu, phản xạ tự nhiên là vật chất hoá nó thành một `dvar` phụ. Làm vậy
 *    thì mô hình đổi và số nhánh tăng ~40% (đo thật: 1 133 -> 1 583). Cách đúng
 *    là dùng `cp.getObjValue()` — không thêm biến nào. Xem NOTES.md (d).
 */

using CP;

{string} Employees = ...;
{string} Days      = ...;
{string} Shifts    = ...;

tuple requestT {
  string e;   // nhân viên
  string d;   // ngày
  string s;   // ca
}
{requestT} ShiftRequests = ...;

// --- tham số dẫn xuất -------------------------------------------------------
int nEmployees = card(Employees);
int nDays      = card(Days);
int nShifts    = card(Shifts);

// Tổng số suất phải phủ trong kỳ: mỗi ca mỗi ngày đúng một người.
int totalSlots = nDays * nShifts;

// Cân bằng tải: floor(DS/N) .. ceil(DS/N).
int minLoad = totalSlots div nEmployees;
int maxLoad = (totalSlots mod nEmployees == 0) ? minLoad : minLoad + 1;

// Ma trận nguyện vọng, tính sẵn từ tuple set thưa. req[e][d][s] = 1 nghĩa là
// nhân viên e MUỐN làm ca s ngày d — tương ứng shift_requests[n][d][s] của Google.
// Chỉ dùng để in lịch; hàm mục tiêu chạy thẳng trên tuple set thưa.
int req[e in Employees][d in Days][s in Shifts] =
  sum(<e2,d2,s2> in ShiftRequests : e2 == e && d2 == d && s2 == s) 1;

// --- cấu hình engine, để số liệu tái lập được và so được với hai chiều kia ---
// Khối execute đứng TRƯỚC phần mô hình sẽ chạy trước khi giải. Cả ba chiều đều
// chạy 1 worker + seed cố định; nếu không thì branches/fails đổi mỗi lần chạy
// và bảng so sánh trong NOTES.md mất giá trị (PLAN.md §2.4).
execute PARAMS {
  cp.param.workers = 1;
  cp.param.randomSeed = 0;
}

// --- biến quyết định --------------------------------------------------------
// x[e][d][s] = 1 <=> nhân viên e làm ca s trong ngày d.  (105 biến bool)
dvar boolean x[Employees][Days][Shifts];

// --- hàm mục tiêu: tối đa số nguyện vọng được đáp ứng ------------------------
// Tổng chạy thẳng trên TUPLE SET THƯA (20 hạng tử) thay vì quét cả lưới 105 ô
// nhân hệ số 0/1. Không có biến phụ nào.
maximize sum(<e,d,s> in ShiftRequests) x[e][d][s];

subject to {

  // (C1) mỗi ca của mỗi ngày do ĐÚNG một người đảm nhiệm
  forall(d in Days, s in Shifts)
    ctOnePerShift:
      sum(e in Employees) x[e][d][s] == 1;

  // (C2) mỗi người làm TỐI ĐA một ca mỗi ngày
  forall(e in Employees, d in Days)
    ctAtMostOneShiftPerDay:
      sum(s in Shifts) x[e][d][s] <= 1;

  // (C3) cân bằng tải — chặn dưới
  forall(e in Employees)
    ctBalanceLow:
      sum(d in Days, s in Shifts) x[e][d][s] >= minLoad;

  // (C4) cân bằng tải — chặn trên
  forall(e in Employees)
    ctBalanceHigh:
      sum(d in Days, s in Shifts) x[e][d][s] <= maxLoad;
}

// --- in lịch ----------------------------------------------------------------
execute POST_PROCESS {
  writeln("So nguyen vong duoc dap ung = ", cp.getObjValue(),
          " / ", ShiftRequests.size);
  for (var d in Days) {
    writeln("Ngay ", d);
    for (var s in Shifts) {
      for (var e in Employees) {
        if (x[e][d][s] == 1) {
          writeln("  ca ", s, "\t", e,
                  req[e][d][s] == 1 ? "\t(dung nguyen vong)" : "\t(khong xin)");
        }
      }
    }
  }
  writeln("Tai cua tung nhan vien (gioi han ", minLoad, "..", maxLoad, "):");
  for (var e in Employees) {
    var load = 0;
    for (var d in Days) for (var s in Shifts) load += x[e][d][s];
    writeln("  ", e, "\t", load, " ca");
  }
}

// --- dòng RESULT theo giao kèo của tools/runner.py --------------------------
// CHÚ Ý: card() không dùng được trong khối execute — phải dùng .size.
execute EMIT_RESULT {
  writeln("RESULT {\"status\":\"Optimal\""
        + ",\"objective\":" + cp.getObjValue()
        + ",\"solve_time_s\":" + cp.info.solveTime
        + ",\"branches\":" + cp.info.numberOfBranches
        + ",\"fails\":" + cp.info.numberOfFails
        + ",\"nb_employees\":" + Employees.size
        + ",\"nb_days\":" + Days.size
        + ",\"nb_shifts\":" + Shifts.size
        + ",\"nb_requests\":" + ShiftRequests.size
        + ",\"min_load\":" + minLoad
        + ",\"max_load\":" + maxLoad
        + ",\"nb_bool_vars\":" + (Employees.size * Days.size * Shifts.size) + "}");
}
