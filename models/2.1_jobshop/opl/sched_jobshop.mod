/* Bài 2.1 — Job-shop scheduling | Chiều OPL (engine CP Optimizer)
 *
 * Nguồn: LẤY MẪU CHÍNH THỨC.
 *   IBM ILOG CPLEX Optimization Studio 22.2 — opl/examples/opl/sched_jobshop/sched_jobshop.mod
 *   Licensed Materials - Property of IBM
 *   5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55
 *   Copyright IBM Corporation 1998, 2026. All Rights Reserved.
 *
 * Phần DỰNG MÔ HÌNH (khai báo dữ liệu, dvar interval, dvar sequence, minimize,
 * subject to) giữ NGUYÊN VĂN bản gốc của IBM — không đổi một ký tự.
 * Bổ sung duy nhất: khối execute EMIT_RESULT ở cuối, in dòng RESULT theo giao
 * kèo của tools/runner.py.
 *
 * Dữ liệu: đổi từ sched_jobshop.dat (một instance 6x6 KHÁC) sang data/jobshop/ft06.dat
 * để cả ba chiều chạy đúng cùng một instance — xem NOTES.md mục (c).
 *
 * Chạy:  tools/oplrun.sh models/2.1_jobshop/opl/sched_jobshop.mod data/jobshop/ft06.dat
 *
 * GHI CHÚ NGÔN NGỮ (điểm so sánh với DOcplex.cp — cùng engine CP Optimizer):
 *   OPL có kiểu `dvar sequence` như một CÔNG DÂN HẠNG NHẤT của ngôn ngữ: khai báo
 *   `dvar sequence mchs[m] in all(...) itvs[j][o]` vừa gom nhóm các interval chạy
 *   trên cùng một máy, vừa tạo ra một biến thứ tự dùng lại được. Bản DOcplex.cp
 *   không có cú pháp khai báo tương ứng — nó phải gom nhóm bằng vòng lặp Python
 *   rồi gọi no_overlap(danh_sách). Cùng engine, cùng ràng buộc, khác cách viết.
 */

using CP;

int nbJobs = ...;
int nbMchs = ...;

range Jobs = 0..nbJobs-1;
range Mchs = 0..nbMchs-1;
// Mchs is used both to index machines and operation position in job

tuple Operation {
  int mch; // Machine
  int pt;  // Processing time
};

Operation Ops[j in Jobs][m in Mchs] = ...;

dvar interval itvs[j in Jobs][o in Mchs] size Ops[j][o].pt;
dvar sequence mchs[m in Mchs] in all(j in Jobs, o in Mchs : Ops[j][o].mch == m) itvs[j][o];

execute {
  		cp.param.FailLimit = 10000;
}

minimize max(j in Jobs) endOf(itvs[j][nbMchs-1]);
subject to {
  forall (m in Mchs)
    noOverlap(mchs[m]);
  forall (j in Jobs, o in 0..nbMchs-2)
    endBeforeStart(itvs[j][o], itvs[j][o+1]);
}

execute {
  for (var j = 0; j <= nbJobs-1; j++) {
    for (var o = 0; o <= nbMchs-1; o++) {
      write(itvs[j][o].start + " ");
    }
    writeln("");
  }
}

// ===== BỔ SUNG — dòng RESULT theo giao kèo của tools/runner.py =====
// Chỉ đọc lời giải rồi in, không đụng tới mô hình.
// Lưu ý: card() không dùng được trong execute, nên số công đoạn tính bằng nhân.
execute EMIT_RESULT {
  var makespan = 0;
  for (var j = 0; j <= nbJobs-1; j++) {
    var e = itvs[j][nbMchs-1].end;
    if (e > makespan) makespan = e;
  }
  // FailLimit = 10000 (dòng cấu hình engine của bản gốc IBM) có thể khiến search
  // dừng trước khi chứng minh tối ưu. Chỉ khai "Optimal" khi search kết thúc tự
  // nhiên, tức số fails chưa chạm trần.
  var proven = (cp.info.numberOfFails < cp.param.FailLimit);
  writeln("RESULT {\"status\":\"" + (proven ? "Optimal" : "Feasible") + "\""
        + ",\"objective\":" + makespan
        + ",\"solve_time_s\":" + cp.info.solveTime
        + ",\"branches\":" + cp.info.numberOfBranches
        + ",\"fails\":" + cp.info.numberOfFails
        + ",\"nb_jobs\":" + nbJobs
        + ",\"nb_machines\":" + nbMchs
        + ",\"nb_operations\":" + (nbJobs * nbMchs) + "}");
}
