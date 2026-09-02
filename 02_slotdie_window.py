#!/usr/bin/env python3
"""Draw the slot-die operability window for the worked case.

    python examples/02_slotdie_window.py [--final]

Writes outputs/figures/slotdie_window.png and outputs/slotdie_window.csv.
Needs the optional viz extra: pip install "pvcoat[viz]".
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _case  # noqa: E402

from pvcoat import slotdie  # noqa: E402
from pvcoat.limits import low_flow_limit  # noqa: E402


def logspace(lo: float, hi: float, count: int):
    import math

    step = (math.log10(hi) - math.log10(lo)) / (count - 1)
    return [10 ** (math.log10(lo) + step * i) for i in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true", help="remove the watermark; use only after the verification checklist is complete")
    args = parser.parse_args()

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover
        print('matplotlib is needed for the figures: pip install "pvcoat[viz]"')
        return 1

    _case.ensure_directories()
    ink, die = _case.ink(), _case.slot_die()

    speeds = logspace(1e-3, 8.0, 70)  # 1 mm/s to 8 m/s, past the air-entrainment bound
    thicknesses = logspace(0.2e-6, 100e-6, 70)
    window = slotdie.window(ink, die, speeds, thicknesses)

    csv_path = os.path.join(_case.OUTPUT_DIR, "slotdie_window.csv")
    with open(csv_path, "w", encoding="utf-8") as handle:
        handle.write(window.to_csv())

    with open(os.path.join(_case.OUTPUT_DIR, "stats.json"), encoding="utf-8") as handle:
        stats = json.load(handle)
    slot = stats["slot_die"]

    verdict_value = {"not operable": 0.0, "marginal": 0.5, "operable": 1.0}
    grid = [
        [
            verdict_value[
                next(
                    p["verdict"]
                    for p in window.points
                    if p["speed_m_s"] == u and p["wet_thickness_m"] == h
                )
            ]
            for u in speeds
        ]
        for h in thicknesses
    ]

    figure, axis = plt.subplots(figsize=(7.2, 5.0))
    mesh = axis.pcolormesh(
        [u * 1e3 for u in speeds],
        [h * 1e6 for h in thicknesses],
        grid,
        cmap="viridis",
        shading="nearest",
        vmin=0,
        vmax=1,
    )
    colorbar = figure.colorbar(mesh, ax=axis, ticks=[0, 0.5, 1])
    colorbar.ax.set_yticklabels(["not operable", "marginal", "operable"])

    limit = [low_flow_limit(ink, die, u) * 1e6 for u in speeds]
    axis.plot(
        [u * 1e3 for u in speeds],
        limit,
        color="white",
        linewidth=2.0,
        label=r"low-flow limit $h_{min}=0.67\,H\,Ca^{2/3}$",
    )
    axis.axvline(
        slot["air_entrainment_speed_m_s"] * 1e3,
        color="white",
        linestyle="--",
        linewidth=1.6,
        label="air entrainment (Gutoff and Kendrick 1982)",
    )
    axis.plot(
        [slot["speed_m_s"] * 1e3],
        [slot["target_wet_thickness_m"] * 1e6],
        marker="o",
        markersize=9,
        markerfacecolor="white",
        markeredgecolor="black",
        linestyle="none",
        label="working point (700 nm dry)",
    )
    axis.annotate(
        f"{slot['speed_m_s'] * 1e3:.0f} mm/s, "
        f"{slot['target_wet_thickness_m'] * 1e6:.2f} um wet\n"
        f"margin to low-flow limit {slot['low_flow_margin']:.1f}x",
        xy=(slot["speed_m_s"] * 1e3, slot["target_wet_thickness_m"] * 1e6),
        xytext=(1.4, 30),
        color="white",
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="white", linewidth=1.2),
    )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("substrate speed (mm/s)")
    axis.set_ylabel("wet film thickness (um)")
    axis.set_title(
        "Slot-die operability window\n"
        f"{stats['ink']['name']}, H = {slot['gap_downstream_m'] * 1e6:.0f} um, "
        f"W = {slot['coating_width_m'] * 1e3:.0f} mm"
    )
    axis.legend(loc="lower right", framealpha=0.85, fontsize=8)
    _case.draft_stamp(axis, args.final)
    figure.tight_layout()

    path = os.path.join(_case.FIGURE_DIR, "slotdie_window.png")
    figure.savefig(path, dpi=200)
    print(window.summary())
    print(f"wrote {path}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
