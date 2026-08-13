/* Bài 1.1 — Tô màu đồ thị (Graph Coloring) | Chiều OPL (engine CP Optimizer)
 *
 * Nguồn: LẤY MẪU CHÍNH THỨC.
 *   <Install_dir>/opl/examples/opl/color/color.mod của IBM ILOG CPLEX
 *   Optimization Studio 22.2.
 *   Licensed Materials - Property of IBM.
 *   5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55
 *   Copyright IBM Corporation 1998, 2026. All Rights Reserved.
 *   Tài liệu: https://www.ibm.com/docs/en/icos/22.2.0?topic=SSSA5P_22.2.0/ilog.odms.ide.help/examples/html/opl/color/color.mod.htm
 *
 * PHẦN DỰNG MÔ HÌNH (khai báo dvar + khối `subject to`) GIỮ NGUYÊN VĂN bản gốc
 * của IBM, kể cả `range r = 0..3` và mảng `Names` viết thẳng trong model. Những
 * thứ dự án này thêm vào, tất cả đều nằm NGOÀI phần dựng mô hình:
 *
 *   (1) khai báo dữ liệu dùng chung đọc từ data/coloring/map6.dat + `assert`
 *       để bản hardcode của IBM không bao giờ lệch với bộ dữ liệu chung;
 *   (2) một khối `execute` kiểm tra nghiệm theo tập cạnh của file dữ liệu chung
 *       và in dòng RESULT theo giao kèo của tools/runner.py.
 *
 * Chạy:  tools/oplrun.sh models/1.1_graph_coloring/opl/color.mod data/coloring/map6.dat
 *
 * GHI CHÚ NGÔN NGỮ (điểm so sánh với DOcplex.cp — cùng engine CP Optimizer):
 *   Hai bản mẫu chính thức của IBM cho bài này gần như là bản dịch từng dòng của
 *   nhau: OPL viết `Belgium != France;`, DOcplex.cp viết `mdl.add(Belgium != France)`.
 *   Khác biệt thật nằm ở chỗ khác — xem NOTES.md mục (d): OPL là ngôn ngữ KHAI BÁO
 *   có tầng dữ liệu `.dat` riêng, còn DOcplex.cp là thư viện Python nên dựng mô
 *   hình bằng chính vòng lặp của Python.
 */

using CP;

/* ---- (1) DỮ LIỆU DÙNG CHUNG — phần dự án thêm, không thuộc mô hình gốc ------
 * Đọc từ data/coloring/map6.dat. Bản gốc của IBM viết thẳng đồ thị vào model;
 * ở đây ta không sửa nó, mà ĐỐI CHIẾU nó với bộ dữ liệu chung: `assert` dưới đây
 * chặn ngay lúc trích mô hình nếu file dữ liệu chung đổi số màu / số đỉnh / số
 * cạnh, còn khối execute cuối file kiểm tra nghiệm theo đúng tập cạnh của file.
 */
int NbColors = ...;
{string} ColorNames = ...;
{string} Countries = ...;
tuple Edge { string a; string b; }
{Edge} Edges = ...;

/* Chép lại tập đỉnh và tập cạnh mà bản gốc của IBM viết thẳng vào model, CHỈ để
 * đối chiếu — hai tập này không tham gia dựng mô hình. Ba câu `assert` dưới đây
 * chặn ngay ở giai đoạn trích mô hình (ERROR[GENERATE_100]) nếu ai đó sửa
 * data/coloring/map6.dat mà quên rằng chiều này viết đồ thị thẳng trong model.
 *
 * GHI CHÚ NGÔN NGỮ: OPL KHÔNG có toán tử so sánh bằng giữa hai tập —
 * `Edges == HardcodedEdges` bị từ chối với "Operator not available for
 * {Edge} == {Edge}". Phải diễn đạt vòng qua lực lượng giao. Bản DOcplex.cp cùng
 * engine chỉ cần viết `set_a == set_b` của Python.
 */
{string} HardcodedCountries = {
   "Belgium", "Denmark", "France", "Germany", "Luxembourg", "Netherlands"
};
{Edge} HardcodedEdges = {
   <"Belgium","France">, <"Belgium","Germany">, <"Belgium","Netherlands">,
   <"Belgium","Luxembourg">, <"Denmark","Germany">, <"France","Germany">,
   <"France","Luxembourg">, <"Germany","Luxembourg">, <"Germany","Netherlands">
};

assert NbColors == 4;   // bản gốc hardcode `range r = 0..3`
assert card(Countries inter HardcodedCountries) == card(HardcodedCountries)
    && card(Countries) == card(HardcodedCountries);
assert card(Edges inter HardcodedEdges) == card(HardcodedEdges)
    && card(Edges) == card(HardcodedEdges);

/* ---- BẮT ĐẦU PHẦN NGUYÊN VĂN CỦA IBM --------------------------------------- */

range r = 0..3;

string Names[r] = ["blue", "white", "yellow", "green"];

dvar int Belgium in r;
dvar int Denmark in r;
dvar int France in r;
dvar int Germany  in r;
dvar int Luxembourg in r;
dvar int Netherlands in r;

subject to {
   Belgium != France;
   Belgium != Germany;
   Belgium != Netherlands;
   Belgium != Luxembourg;
   Denmark != Germany;
   France != Germany;
   France != Luxembourg;
   Germany != Luxembourg;
   Germany != Netherlands;
}

execute {
   writeln("Belgium:     ", Names[Belgium]);
   writeln("Denmark:     ", Names[Denmark]);
   writeln("France:      ", Names[France]);
   writeln("Germany:     ", Names[Germany]);
   writeln("Luxembourg:  ", Names[Luxembourg]);
   writeln("Netherlands: ", Names[Netherlands]);
}

tuple resultT {
	string name;
	string value;
};
{resultT} solution = {};
execute{
   solution.add("Belgium", Names[Belgium]);
   solution.add("Denmark", Names[Denmark]);
   solution.add("France", Names[France]);
   solution.add("Germany", Names[Germany]);
   solution.add("Luxembourg", Names[Luxembourg]);
   solution.add("Netherlands", Names[Netherlands]);
   writeln(solution);
}

/* ---- HẾT PHẦN NGUYÊN VĂN CỦA IBM ------------------------------------------- */

/* ---- (2) Kiểm tra nghiệm theo dữ liệu chung + dòng RESULT -------------------
 * CHÚ Ý cú pháp: trong khối `execute` (ILOG Script) KHÔNG gọi được `card()` —
 * đó là hàm của tầng model. Số phần tử của một tập lấy bằng `.size`.
 */
execute {
   // Bảng tra tên nước -> màu, để đối chiếu được với tập cạnh của file dữ liệu.
   var colorOf = new Array();
   colorOf["Belgium"]     = Belgium;
   colorOf["Denmark"]     = Denmark;
   colorOf["France"]      = France;
   colorOf["Germany"]     = Germany;
   colorOf["Luxembourg"]  = Luxembourg;
   colorOf["Netherlands"] = Netherlands;

   // Mọi cạnh trong dữ liệu chung phải nối hai nước khác màu.
   var violations = 0;
   for (var e in Edges) {
      if (colorOf[e.a] == colorOf[e.b]) {
         violations++;
         writeln("VI PHẠM: ", e.a, " và ", e.b, " cùng màu ", Names[colorOf[e.a]]);
      }
   }

   // Số màu thực sự dùng tới — để đối chiếu với phần mở rộng sắc số (color_min.mod).
   var seen = new Array();
   var colorsUsed = 0;
   for (var c in Countries) {
      if (seen[colorOf[c]] == null) { seen[colorOf[c]] = 1; colorsUsed++; }
   }

   writeln("CHECK violations=", violations,
           " colorsUsed=", colorsUsed,
           " (dữ liệu chung: ", Countries.size, " đỉnh, ", Edges.size,
           " cạnh, ", NbColors, " màu)");

   writeln("RESULT {\"status\":\"" + (violations == 0 ? "Feasible" : "Invalid") + "\""
         + ",\"objective\":null"
         + ",\"solve_time_s\":" + cp.info.solveTime
         + ",\"branches\":" + cp.info.numberOfBranches
         + ",\"fails\":" + cp.info.numberOfFails
         + ",\"colors_used\":" + colorsUsed
         + ",\"violations\":" + violations
         + ",\"n_vertices\":" + Countries.size
         + ",\"n_edges\":" + Edges.size + "}");
}
