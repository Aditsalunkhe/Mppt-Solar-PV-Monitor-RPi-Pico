"""Offline (CPython) run of the same PV model + Perturb & Observe loop used in src/main.py.

Purpose: reproduce the results without Wokwi, write a CSV in the same format the Pico prints
over serial, and draw the two figures used in the README.

Keep the model constants and the P&O update below in sync with src/main.py.

Usage:
    pip install -r analysis/requirements.txt
    python analysis/simulate_mppt.py
"""
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMG_DIR = ROOT / "docs" / "images"

# ---- PV model (same constants as src/main.py) -------------------------------------------
VOC_STC = 22.0
ISC_STC = 8.0
A = 1.21
I0 = ISC_STC / (math.exp(VOC_STC / A) - 1)


def pv_current(v, g):
    i = ISC_STC * g / 1000 - I0 * (math.exp(v / A) - 1)
    return i if i > 0 else 0.0


def pv_voc(g):
    return A * math.log(ISC_STC * g / 1000 / I0 + 1)


def true_mpp(g):
    voc = pv_voc(g)
    best_p, best_v, v = 0.0, 0.0, 0.0
    while v < voc:
        p = v * pv_current(v, g)
        if p > best_p:
            best_p, best_v = p, v
        v += 0.1
    return best_p, best_v


# ---- Scenario: pot position (fraction of full travel) changes every 100 iterations -------
LEVELS = [1.0, 0.5, 0.15, 0.0, 1.0]
ITER_PER_LEVEL = 100
DT_MS = 100
STEP = 0.2


def run():
    rows = []
    v, step, p_prev = 12.0, STEP, 0.0
    for k in range(ITER_PER_LEVEL * len(LEVELS)):
        g = 100 + LEVELS[k // ITER_PER_LEVEL] * 900
        i = pv_current(v, g)
        p = v * i
        pmax, vmpp = true_mpp(g)
        eff = 100 * p / pmax if pmax > 0 else 0.0
        rows.append((k * DT_MS, g, v, i, p, pmax, vmpp, eff))
        if p < p_prev:
            step = -step
        p_prev = p
        v = min(max(v + step, 0.5), pv_voc(g) - 0.1)
    return rows


# ---- Plot style (light surface, thin marks, recessive grid) ------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
BLUE = "#2a78d6"     # categorical slot 1
ORANGE = "#eb6834"   # categorical slot 2
SEQ = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # sequential blue, light -> dark


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASE)
    ax.tick_params(colors=MUTED, labelsize=9, length=3)
    ax.xaxis.label.set_color(INK2)
    ax.yaxis.label.set_color(INK2)
    ax.title.set_color(INK)


def plot_curves(path):
    gs = [200, 500, 800, 1000]
    fig, (ax_i, ax_p) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE)
    for g, col in zip(gs, SEQ):
        voc = pv_voc(g)
        vs = [k * 0.05 for k in range(int(voc / 0.05) + 1)]
        ax_i.plot(vs, [pv_current(v, g) for v in vs], color=col, linewidth=2,
                  label=f"{g} W/m²")
        ax_p.plot(vs, [v * pv_current(v, g) for v in vs], color=col, linewidth=2,
                  label=f"{g} W/m²")
        pm, vm = true_mpp(g)
        ax_p.plot([vm], [pm], "o", color=col, markersize=8, markeredgecolor=SURFACE,
                  markeredgewidth=2)
        ax_p.annotate(f"{pm:.0f} W", (vm, pm), textcoords="offset points", xytext=(-6, 8),
                      ha="right", fontsize=9, color=INK2)
        ax_i.plot([vm], [pv_current(vm, g)], "o", color=col, markersize=8,
                  markeredgecolor=SURFACE, markeredgewidth=2)
    ax_i.set_title("Current vs. voltage", loc="left", fontsize=11)
    ax_p.set_title("Power vs. voltage (dot = maximum power point)", loc="left", fontsize=11)
    ax_i.set_xlabel("Panel voltage (V)")
    ax_p.set_xlabel("Panel voltage (V)")
    ax_i.set_ylabel("Current (A)")
    ax_p.set_ylabel("Power (W)")
    for ax in (ax_i, ax_p):
        style(ax)
        ax.set_xlim(0, 23)
    handles, labels = ax_i.get_legend_handles_labels()
    leg = fig.legend(handles, labels, loc="lower center", ncol=len(gs), frameon=False,
                     fontsize=9)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax_i.set_ylim(0, 8.6)
    ax_p.set_ylim(0, 160)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_tracking(rows, path):
    t = [r[0] / 1000 for r in rows]
    g = [r[1] for r in rows]
    v = [r[2] for r in rows]
    p = [r[4] for r in rows]
    pmax = [r[5] for r in rows]
    vmpp = [r[6] for r in rows]
    fig, axs = plt.subplots(3, 1, figsize=(10, 7.4), sharex=True, facecolor=SURFACE)

    axs[0].step(t, g, where="post", color=BLUE, linewidth=2)
    axs[0].set_ylabel("Irradiance (W/m²)")
    axs[0].set_title("The 'sun' (potentiometer) changes; the tracker follows",
                     loc="left", fontsize=11)

    axs[1].plot(t, vmpp, color=ORANGE, linewidth=2, label="True MPP voltage")
    axs[1].plot(t, v, color=BLUE, linewidth=2, label="Tracked voltage")
    axs[1].set_ylabel("Voltage (V)")

    axs[2].plot(t, pmax, color=ORANGE, linewidth=2, label="True maximum power")
    axs[2].plot(t, p, color=BLUE, linewidth=2, label="Tracked power")
    axs[2].set_ylabel("Power (W)")
    axs[2].set_xlabel("Time (s)")

    for ax in axs:
        style(ax)
        ax.set_xlim(0, t[-1])
    for ax in axs[1:]:
        leg = ax.legend(frameon=False, fontsize=9, loc="lower right")
        for tx in leg.get_texts():
            tx.set_color(INK2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    rows = run()

    with open(DATA_DIR / "sample_run.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ms", "G", "V", "I", "P", "Pmax", "Vmpp", "eff"])
        for r in rows:
            w.writerow([r[0], f"{r[1]:.0f}", f"{r[2]:.2f}", f"{r[3]:.2f}", f"{r[4]:.1f}",
                        f"{r[5]:.1f}", f"{r[6]:.2f}", f"{r[7]:.1f}"])

    plot_curves(IMG_DIR / "pv_curves.png")
    plot_tracking(rows, IMG_DIR / "tracking.png")

    print("Settled operating point per irradiance level (last sample of each segment):")
    print(f"{'G (W/m2)':>9} {'V (V)':>7} {'I (A)':>6} {'P (W)':>7} {'Pmax (W)':>9} {'min eff last 20 (%)':>20}")
    for k in range(len(LEVELS)):
        seg = rows[k * ITER_PER_LEVEL:(k + 1) * ITER_PER_LEVEL]
        last = seg[-1]
        worst = min(r[7] for r in seg[-20:])
        print(f"{last[1]:>9.0f} {last[2]:>7.2f} {last[3]:>6.2f} {last[4]:>7.1f} {last[5]:>9.1f} {worst:>20.1f}")


if __name__ == "__main__":
    main()
