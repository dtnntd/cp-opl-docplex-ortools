"""Nối DOcplex.cp (Python trong WSL) với engine CP Optimizer (bản Windows).

Import module này TRƯỚC khi gọi solve():

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "tools"))
    import cpo_env  # noqa: F401

Vì sao cần: `docplex` cài qua pip CHỈ là lớp mô hình hoá bằng Python — nó không
chứa solver. Engine giải thật là `cpoptimizer`, đi kèm CPLEX Studio. Ở máy này
CPLEX Studio là bản Windows còn Python chạy trong WSL, nên phải trỏ
`context.solver.local.execfile` sang file .exe; WSL interop lo phần gọi tiến trình.
DOcplex trao đổi mô hình với engine qua stdin/stdout nên không phát sinh vấn đề
dịch đường dẫn.

Đây chính là minh hoạ cho kiến trúc tầng ở mục 1b của brief: DOcplex là NGÔN NGỮ
mô hình hoá, CP Optimizer là ENGINE — hai tầng tách rời, không phải hai lựa chọn
ngang hàng.
"""

from __future__ import annotations

import os
import pathlib

from docplex.cp.config import context

#: Nơi tìm cpoptimizer, theo thứ tự ưu tiên. Đặt biến môi trường CPOPTIMIZER_EXEC
#: để chỉ định thủ công nếu bạn cài ở chỗ khác.
_CANDIDATES = [
    os.environ.get("CPOPTIMIZER_EXEC"),
    # bản Windows đi kèm CPLEX Studio, gọi từ WSL qua interop
    "/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222/cpoptimizer/bin/x64_win64/cpoptimizer.exe",
    "/mnt/c/Program Files/IBM/ILOG/CPLEX_Studio_Community222/cpoptimizer/bin/x64_win64/cpoptimizer.exe",
    # bản Linux, nếu sau này cài thêm
    "/opt/ibm/ILOG/CPLEX_Studio_Community222/cpoptimizer/bin/x86-64_linux/cpoptimizer",
]


def _resolve() -> str:
    for c in _CANDIDATES:
        if c and pathlib.Path(c).exists():
            return c
    raise RuntimeError(
        "Không tìm thấy cpoptimizer. Cài IBM CPLEX Optimization Studio, hoặc đặt "
        "biến môi trường CPOPTIMIZER_EXEC trỏ tới file thực thi cpoptimizer."
    )


EXECFILE = _resolve()

# `context` của docplex là cây cấu hình động nên type checker không thấy được
# các thuộc tính này; chúng có thật lúc chạy.
context.solver.agent = "local"  # type: ignore[union-attr]
context.solver.local.execfile = EXECFILE  # type: ignore[union-attr]

#: Giới hạn của Community Edition: CP Optimizer chỉ giải bài có không gian tìm kiếm
#: tới 2^1000. Với mã hoá nhị phân thì con số này bằng đúng SỐ BIẾN bool, nên các
#: mô hình trong dự án ưu tiên mã hoá bằng biến nguyên miền nhỏ để lọt giới hạn.
COMMUNITY_LOG_SEARCH_SPACE_LIMIT = 1000

__all__ = ["EXECFILE", "COMMUNITY_LOG_SEARCH_SPACE_LIMIT"]
