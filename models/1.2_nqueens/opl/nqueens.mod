/* Bài 1.2 — N-Queens | Chiều OPL (engine CP Optimizer)
 * Nguồn: VIẾT MỚI. IBM không phát hành ví dụ N-Queens bằng OPL trong bộ
 * examples đi kèm CPLEX Studio 22.2 (xem NOTES.md).
 *
 * Chạy:  tools/oplrun.sh models/1.2_nqueens/opl/nqueens.mod data/queens/nqueens.dat
 *
 * GHI CHÚ NGÔN NGỮ (điểm so sánh với DOcplex.cp):
 *   OPL không cho truyền mảng biểu thức vào allDifferent — `allDifferent(dexpr int[])`
 *   bị từ chối với lỗi "not available in context CP". Vì vậy hai đường chéo phải
 *   được vật chất hoá thành dvar phụ rồi ràng buộc bằng ==. Bản DOcplex.cp cùng
 *   engine viết thẳng all_diff([q[i] + i for i in ...]) — đây là khác biệt thuần
 *   NGÔN NGỮ, không phải khác biệt engine.
 */

using CP;

int n = ...;
range R = 0..n-1;

// q[i] = cột đặt hậu ở hàng i. Mã hoá này đã ngầm loại hết xung đột theo hàng.
dvar int q[R] in R;

// Hai mảng phụ cho đường chéo. Xem ghi chú ngôn ngữ ở trên.
dvar int diagUp[R]   in 0..2*(n-1);
dvar int diagDown[R] in -(n-1)..(n-1);

subject to {
  forall (i in R) diagUp[i]   == q[i] + i;
  forall (i in R) diagDown[i] == q[i] - i;

  allDifferent(q);         // không hai hậu cùng cột
  allDifferent(diagUp);    // không hai hậu cùng đường chéo ↗
  allDifferent(diagDown);  // không hai hậu cùng đường chéo ↘
}

execute {
  var cols = "[";
  for (var i in R) cols += (i > 0 ? "," : "") + q[i];
  cols += "]";
  writeln("QUEENS ", cols);
  writeln("RESULT {\"status\":\"Feasible\""
        + ",\"solve_time_s\":" + cp.info.solveTime
        + ",\"branches\":" + cp.info.numberOfBranches
        + ",\"fails\":" + cp.info.numberOfFails
        + ",\"n\":" + n + "}");
}
