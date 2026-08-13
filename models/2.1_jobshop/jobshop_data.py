"""Đọc dữ liệu job-shop từ file `.dat` của OPL — dùng chung cho hai chiều Python.

VÌ SAO CẦN MODULE NÀY. Bài 2.1 chỉ có ĐÚNG MỘT file dữ liệu: `data/jobshop/ft06.dat`,
viết bằng cú pháp `.dat` của OPL để chiều OPL đọc được nguyên trạng. Hai chiều
Python đọc lại chính file đó, nên không tồn tại bản dữ liệu thứ hai để mà lệch.

Việc đọc cú pháp `.dat` do `tools/opl_dat.py` — trình đọc dùng chung của dự án —
đảm nhiệm. Module này chỉ làm hai việc riêng của bài 2.1: chuyển mảng `Ops` sang
đúng hình dạng mà hai bản mẫu chính thức dùng, và vẽ biểu đồ Gantt.

Trả về đúng bốn đại lượng mà cả hai bản mẫu chính thức (IBM OPL và IBM docplex)
đều dùng, giữ nguyên tên của bản docplex:

    NB_JOBS, NB_MACHINES
    MACHINES[j][o]   máy thực hiện công đoạn thứ o của job j
    DURATION[j][o]   thời gian gia công công đoạn đó
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from opl_dat import load as load_dat  # noqa: E402


def load(path: str | pathlib.Path):
    """Đọc `data/jobshop/*.dat` -> (NB_JOBS, NB_MACHINES, MACHINES, DURATION)."""
    d = load_dat(path)
    nb_jobs, nb_machines = d["nbJobs"], d["nbMchs"]

    # Ops[j] là dãy công đoạn của job j theo ĐÚNG thứ tự công nghệ bắt buộc;
    # mỗi công đoạn là cặp <máy, thời lượng>.
    ops = d["Ops"]
    if len(ops) != nb_jobs:
        raise ValueError(f"{path}: có {len(ops)} job, khai báo nbJobs = {nb_jobs}")
    for j, row in enumerate(ops):
        if len(row) != nb_machines:
            raise ValueError(
                f"{path}: job {j} có {len(row)} công đoạn, cần {nb_machines}"
            )

    machines = [[op[0] for op in row] for row in ops]
    duration = [[op[1] for op in row] for row in ops]

    # Bất biến của job-shop cổ điển: mỗi job đi qua mỗi máy đúng một lần.
    for j, row in enumerate(machines):
        if sorted(row) != list(range(nb_machines)):
            raise ValueError(f"{path}: job {j} không đi qua đủ mỗi máy đúng một lần: {row}")

    return nb_jobs, nb_machines, machines, duration


def write_gantt(path, nb_jobs, nb_machines, machines, starts, durations, title):
    """Vẽ biểu đồ Gantt theo máy. `starts[j][o]` là thời điểm bắt đầu đã giải ra."""
    import matplotlib

    matplotlib.use("Agg")  # không cần màn hình — chạy được cả trong CI/WSL
    import matplotlib.pyplot as plt

    cmap = plt.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(11, 0.6 * nb_machines + 1.6))
    for j in range(nb_jobs):
        for o in range(nb_machines):
            m = machines[j][o]
            ax.broken_barh(
                [(starts[j][o], durations[j][o])],
                (m - 0.35, 0.7),
                facecolors=cmap(j % 10),
                edgecolors="white",
                linewidth=0.8,
            )
            ax.text(
                starts[j][o] + durations[j][o] / 2,
                m,
                f"J{j}",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
            )
    makespan = max(starts[j][o] + durations[j][o] for j in range(nb_jobs) for o in range(nb_machines))
    ax.axvline(makespan, color="crimson", linestyle="--", linewidth=1)
    ax.set_yticks(range(nb_machines))
    ax.set_yticklabels([f"M{m}" for m in range(nb_machines)])
    ax.set_ylim(nb_machines - 0.45, -1.1)  # đảo trục y, chừa chỗ cho nhãn makespan
    ax.text(makespan, -0.95, f"makespan = {makespan} ", color="crimson", ha="right", va="center", fontsize=9)
    ax.set_xlabel("Thời gian")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


if __name__ == "__main__":  # kiểm tra nhanh: python3 models/2.1_jobshop/jobshop_data.py <file.dat>
    import sys

    nj, nm, mch, dur = load(sys.argv[1] if len(sys.argv) > 1 else "data/jobshop/ft06.dat")
    print(f"nbJobs={nj} nbMchs={nm}")
    for j in range(nj):
        print(f"  job {j}: " + "  ".join(f"M{mch[j][o]}/{dur[j][o]}" for o in range(nm)))
