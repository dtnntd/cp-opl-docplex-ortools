"""Nối DOcplex.cp (lớp mô hình hoá Python) với engine CP Optimizer.

Import module này TRƯỚC khi gọi solve():

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "tools"))
    import cpo_env  # noqa: F401

Vì sao cần: `docplex` cài qua pip CHỈ là lớp mô hình hoá bằng Python — nó không
chứa solver. Engine giải thật là `cpoptimizer`, một file thực thi đi kèm IBM ILOG
CPLEX Optimization Studio. Module này dò tìm file đó rồi trỏ
`context.solver.local.execfile` sang nó. DOcplex trao đổi mô hình với engine qua
stdin/stdout nên KHÔNG phát sinh vấn đề dịch đường dẫn: kể cả khi Python chạy
trong WSL còn engine là bản Windows (`cpoptimizer.exe`) gọi qua interop — cấu
hình của máy gốc dự án — thì cũng không cần chuyển đổi đường dẫn như bên OPL.

Đây chính là minh hoạ cho kiến trúc tầng ở mục 1b của brief: DOcplex là NGÔN NGỮ
mô hình hoá, CP Optimizer là ENGINE — hai tầng tách rời, không phải hai lựa chọn
ngang hàng. Đổi chỗ cài CPLEX Studio chỉ đổi tầng dưới; mã mô hình không đụng tới.

Thứ tự dò, giống hệt `tools/oplrun.sh`:
  1. biến môi trường ``CPOPTIMIZER_EXEC`` — trỏ thẳng file thực thi
  2. biến môi trường ``CPLEX_STUDIO_DIR`` — trỏ thư mục cài CPLEX Studio
  3. các vị trí cài mặc định của từng hệ điều hành, glob mọi số hiệu phiên bản
"""

from __future__ import annotations

import os
import pathlib
import sys

from docplex.cp.config import context

#: Thư mục con chứa cpoptimizer BÊN TRONG thư mục cài CPLEX Studio, theo hệ.
#:
#: ĐÃ KIỂM CHỨNG trên máy gốc của dự án (WSL + CPLEX Studio Community 22.2 trên
#: ổ D: của Windows): ``cpoptimizer/bin/`` chỉ chứa đúng một thư mục
#: ``x64_win64`` với ``cpoptimizer.exe`` bên trong.
#:
#: THEO TÀI LIỆU IBM, chưa kiểm chứng được vì máy này không có bản Linux/macOS:
#:   cpoptimizer/bin/x86-64_linux/cpoptimizer
#:   cpoptimizer/bin/x86-64_osx/cpoptimizer   (Intel)
#:   cpoptimizer/bin/arm64_osx/cpoptimizer    (Apple Silicon)
_ARCH_SUBDIRS: dict[str, tuple[str, ...]] = {
    # Trên WSL vẫn giữ nhánh win64 phía sau: máy không có bản Linux thì rơi
    # xuống bản Windows gọi qua interop.
    "linux": (
        "cpoptimizer/bin/x86-64_linux/cpoptimizer",
        "cpoptimizer/bin/x64_win64/cpoptimizer.exe",
    ),
    "darwin": (
        "cpoptimizer/bin/arm64_osx/cpoptimizer",
        "cpoptimizer/bin/x86-64_osx/cpoptimizer",
    ),
    "win32": ("cpoptimizer/bin/x64_win64/cpoptimizer.exe",),
}

_ARCH_SUBDIRS_FALLBACK: tuple[str, ...] = (
    "cpoptimizer/bin/x86-64_linux/cpoptimizer",
    "cpoptimizer/bin/arm64_osx/cpoptimizer",
    "cpoptimizer/bin/x86-64_osx/cpoptimizer",
    "cpoptimizer/bin/x64_win64/cpoptimizer.exe",
)


def _arch_subdirs() -> tuple[str, ...]:
    return _ARCH_SUBDIRS.get(sys.platform, _ARCH_SUBDIRS_FALLBACK)


def _base_dirs() -> list[pathlib.Path]:
    """Các thư mục cha có thể chứa nhiều bản cài CPLEX Studio."""
    home = pathlib.Path.home()
    bases: list[pathlib.Path] = []
    if sys.platform == "linux":
        bases += [
            pathlib.Path("/opt/ibm/ILOG"),
            pathlib.Path("/opt/IBM/ILOG"),
            home / "ibm/ILOG",
            home / "IBM/ILOG",
        ]
        # WSL: bản Windows nằm trên ổ đĩa Windows mount vào /mnt/<ổ>.
        mnt = pathlib.Path("/mnt")
        if mnt.is_dir():
            try:
                drives = sorted(mnt.iterdir())
            except OSError:
                drives = []
            for d in drives:
                bases.append(d / "Program Files/IBM/ILOG")
    elif sys.platform == "darwin":
        bases += [
            pathlib.Path("/Applications"),
            home / "Applications",
            pathlib.Path("/opt/ibm/ILOG"),
        ]
    elif sys.platform == "win32":
        for env in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
            root = os.environ.get(env)
            if root:
                bases.append(pathlib.Path(root) / "IBM/ILOG")
    else:
        bases += [pathlib.Path("/opt/ibm/ILOG"), pathlib.Path("/Applications")]
    return bases


def _studio_dirs() -> list[pathlib.Path]:
    """Mọi thư mục cài CPLEX Studio tìm được, theo thứ tự ưu tiên.

    Bản đầy đủ (``CPLEX_Studio<ver>``) xếp trước bản Community
    (``CPLEX_Studio_Community<ver>``) vì bản đầy đủ không có giới hạn không gian
    tìm kiếm; trong mỗi nhóm thì số hiệu lớn (phiên bản mới) đứng trước. Glob bắt
    được mọi số hiệu: 221, 222, 2211, 2212, ...
    """
    found: list[pathlib.Path] = []
    for base in _base_dirs():
        if not base.is_dir():
            continue
        for pattern in ("CPLEX_Studio[0-9]*", "CPLEX_Studio_Community*"):
            try:
                hits = sorted((p for p in base.glob(pattern) if p.is_dir()), reverse=True)
            except OSError:
                hits = []
            found += hits
    return found


def _resolve() -> str:
    tried: list[str] = []

    # 1. Trỏ thẳng file thực thi.
    explicit = os.environ.get("CPOPTIMIZER_EXEC")
    if explicit:
        tried.append(f"$CPOPTIMIZER_EXEC = {explicit}")
        if pathlib.Path(explicit).is_file():
            return explicit
        raise RuntimeError(_not_found_message(tried))

    # 2. Trỏ thư mục cài CPLEX Studio.
    studio_dir = os.environ.get("CPLEX_STUDIO_DIR")
    roots = [pathlib.Path(studio_dir)] if studio_dir else _studio_dirs()

    # 3. Dò từng thư mục cài.
    for root in roots:
        for sub in _arch_subdirs():
            cand = root / sub
            tried.append(str(cand))
            if cand.is_file():
                return str(cand)

    raise RuntimeError(_not_found_message(tried))


def _not_found_message(tried: list[str]) -> str:
    where = "\n".join(f"  {t}" for t in tried) or "  (không có bản cài CPLEX Studio nào)"
    return (
        "Không tìm thấy cpoptimizer — engine của DOcplex.cp.\n"
        f"Hệ điều hành nhận diện được: {sys.platform}\n"
        "Đã dò các vị trí sau:\n"
        f"{where}\n"
        "Cài IBM ILOG CPLEX Optimization Studio, hoặc chỉ định thủ công bằng một\n"
        "trong hai biến môi trường:\n"
        "  CPOPTIMIZER_EXEC  trỏ thẳng tới file thực thi cpoptimizer (hoặc .exe)\n"
        "  CPLEX_STUDIO_DIR  trỏ tới thư mục cài CPLEX Studio, ví dụ\n"
        "                    /opt/ibm/ILOG/CPLEX_Studio2211 (Linux)\n"
        "                    /Applications/CPLEX_Studio2211 (macOS)\n"
        "                    '/mnt/d/Program Files/IBM/ILOG/CPLEX_Studio_Community222' (WSL)"
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
