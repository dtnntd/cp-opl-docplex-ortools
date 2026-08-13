"""Đọc file dữ liệu `.dat` của OPL từ Python.

Vì sao cần: bài 3.2 lấy `timetabling.mod` của IBM làm nền, và dữ liệu đi kèm nằm
ở định dạng `.dat` của OPL. Nếu chuyển tay sang JSON cho hai chiều Python thì có
hai bản dữ liệu phải giữ đồng bộ — chỉ cần lệch một dòng là mọi so sánh trong báo
cáo mất giá trị. Module này cho cả ba chiều đọc **đúng cùng một file gốc**.

Hỗ trợ tập cú pháp mà các file dữ liệu của dự án dùng tới:

    tên = 42;                          -> int
    tên = { "a", "b" };                -> list[str]          (tập hợp)
    tên = { <"a","b">, <"c","d"> };    -> list[tuple]
    tên = { <"X","Maths", 2, 4> };     -> list[tuple] lẫn str và int
    tên = [ [<2,1>, <0,3>], [...] ];   -> list[list[tuple]]  (mảng, lồng nhau tuỳ ý)

OPL phân biệt tập hợp `{...}` với mảng `[...]`; ở phía Python cả hai đều thành
`list` vì thứ tự trong file đã đủ mang thông tin cần dùng (ví dụ thứ tự công đoạn
trong một job của bài job-shop chính là thứ tự công nghệ bắt buộc).

Ghi chú `//` và `/* */` được bỏ qua.

Dùng:
    from opl_dat import load
    data = load("data/timetable/base.dat", "data/timetable/large.dat")
    data["DayDuration"]        # 6
    data["RequirementSet"]     # [("X","Biology",1,4), ...]
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_ASSIGNMENT = re.compile(r"(\w+)\s*=\s*(.*?);", re.DOTALL)


def _strip_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))


#: Cặp ngoặc mở -> ngoặc đóng. `{}` là tập hợp, `[]` là mảng, `<>` là tuple.
_BRACKETS = {"{": "}", "[": "]", "<": ">"}


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _parse_value(s: str, i: int = 0) -> tuple[Any, int]:
    """Đọc một giá trị bắt đầu tại vị trí `i`, trả về (giá trị, vị trí kế tiếp).

    Đệ quy nên mảng và tập hợp lồng nhau bao nhiêu tầng cũng đọc được.
    """
    i = _skip_ws(s, i)
    if i >= len(s):
        raise ValueError("hết chuỗi khi đang chờ một giá trị")

    ch = s[i]

    if ch in _BRACKETS:
        close = _BRACKETS[ch]
        items: list[Any] = []
        i += 1
        while True:
            i = _skip_ws(s, i)
            if i >= len(s):
                raise ValueError(f"thiếu dấu đóng {close!r}")
            if s[i] == close:
                return (tuple(items) if ch == "<" else items), i + 1
            if s[i] == ",":
                i += 1
                continue
            value, i = _parse_value(s, i)
            items.append(value)

    if ch == '"':
        j = s.index('"', i + 1)
        return s[i + 1 : j], j + 1

    j = i
    while j < len(s) and (s[j].isdigit() or s[j] in "+-."):
        j += 1
    token = s[i:j]
    if not token:
        raise ValueError(f"không đọc được giá trị tại vị trí {i}: {s[i:i+30]!r}")
    return (float(token) if "." in token else int(token)), j


def parse(text: str) -> dict[str, Any]:
    """Đọc nội dung một file `.dat` thành dict."""
    out: dict[str, Any] = {}
    for name, raw in _ASSIGNMENT.findall(_strip_comments(text)):
        out[name], _ = _parse_value(raw.strip())
    return out


def load(*paths: str | pathlib.Path) -> dict[str, Any]:
    """Đọc và gộp nhiều file `.dat`, theo đúng cách oplrun nhận nhiều tham số dữ liệu.

    File sau ghi đè khoá trùng của file trước.
    """
    merged: dict[str, Any] = {}
    for p in paths:
        merged.update(parse(pathlib.Path(p).read_text(encoding="utf-8", errors="replace")))
    return merged


if __name__ == "__main__":  # kiểm tra nhanh: python3 tools/opl_dat.py <file...>
    import sys

    for key, value in load(*sys.argv[1:]).items():
        preview = value if not isinstance(value, list) else f"[{len(value)} phần tử] {value[:3]}"
        print(f"{key:<24} {preview}")
