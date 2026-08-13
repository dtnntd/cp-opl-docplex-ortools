/* Bài 1.1 — MỞ RỘNG: tối ưu sắc số (chromatic number) | Chiều OPL
 *
 * Nguồn: ✍️ VIẾT MỚI. Bản `color.mod` của IBM là CSP thuần — cho sẵn 4 màu và
 * chỉ hỏi "có tô được không". File này hỏi thêm câu tự nhiên tiếp theo: **ít
 * nhất bao nhiêu màu là đủ?** — tức tìm sắc số χ(G).
 *
 * Chạy:  tools/oplrun.sh models/1.1_graph_coloring/opl/color_min.mod data/coloring/map6.dat
 *
 * Hai điểm khác bản gốc, đều là cố ý:
 *
 *  1. Mô hình DỰNG TỪ DỮ LIỆU, không hardcode. Bản gốc khai 6 dvar có tên riêng
 *     và 9 ràng buộc viết tay; ở đây là `dvar int color[Countries]` cùng một
 *     `forall (e in Edges)`. Cách viết này chính là cách OPL được thiết kế để
 *     dùng — model tách khỏi dữ liệu — và đổi bản đồ chỉ cần đổi file .dat.
 *
 *  2. Thêm biến K = số màu dùng tới và cực tiểu hoá nó. Vì màu chỉ là NHÃN nên
 *     mọi nghiệm dùng k màu đều đánh lại nhãn được thành 0..k-1; do đó
 *     min(max color + 1) đúng bằng sắc số. Ràng buộc color[c] <= K-1 vừa định
 *     nghĩa K vừa phá bớt đối xứng hoán vị màu.
 */

using CP;

int NbColors = ...;
{string} ColorNames = ...;
{string} Countries = ...;
tuple Edge { string a; string b; }
{Edge} Edges = ...;

// color[c] = chỉ số màu của đỉnh c; K = số màu được phép dùng.
dvar int color[Countries] in 0..NbColors-1;
dvar int K in 1..NbColors;

minimize K;

subject to {
   // Hai đỉnh kề nhau khác màu — đúng 9 ràng buộc != của bản gốc, viết bằng forall.
   forall (e in Edges)
      color[e.a] != color[e.b];

   // K chặn trên mọi nhãn màu ⇒ nghiệm chỉ dùng các màu 0..K-1.
   forall (c in Countries)
      color[c] <= K - 1;
}

execute {
   // ILOG Script không có `item(set, i)`; đổ tập màu ra mảng để tra theo chỉ số.
   var names = new Array();
   var k = 0;
   for (var nm in ColorNames) names[k++] = nm;

   for (var c in Countries)
      writeln(c, ": ", names[color[c]]);

   var violations = 0;
   for (var e in Edges)
      if (color[e.a] == color[e.b]) violations++;

   // Số nhãn màu thật sự xuất hiện trong nghiệm — phải bằng K khi K đã tối ưu.
   var seen = new Array();
   var colorsUsed = 0;
   for (var c in Countries)
      if (seen[color[c]] == null) { seen[color[c]] = 1; colorsUsed++; }

   writeln("CHECK violations=", violations, " chromatic=", K, " colorsUsed=", colorsUsed);

   writeln("RESULT {\"status\":\"" + (violations == 0 ? "Optimal" : "Invalid") + "\""
         + ",\"objective\":" + K
         + ",\"solve_time_s\":" + cp.info.solveTime
         + ",\"branches\":" + cp.info.numberOfBranches
         + ",\"fails\":" + cp.info.numberOfFails
         + ",\"colors_used\":" + colorsUsed
         + ",\"violations\":" + violations
         + ",\"n_vertices\":" + Countries.size
         + ",\"n_edges\":" + Edges.size
         + ",\"mode\":\"min_colors\"}");
}
