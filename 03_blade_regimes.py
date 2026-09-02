#!/usr/bin/env python3
"""Draw the blade-coating thickness-speed curve with both regimes.

    python examples/03_blade_regimes.py [--final]

Writes outputs/figures/blade_regimes.png and outputs/blade_curve.csv.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _case  # noqa: E402

from pvcoat import blade  # noqa: E402
from pvcoat.limits import (  # noqa: E402
    evaporation_regime_dry_thickness,
    landau_levich_thickness,
)


def logspace(lo: float, hi: float, count: int):
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
    ink, head = _case.ink(), _case.blade()
    radius = head.effective_meniscus_radius

    speeds = logspace(5e-5, 0.2, 200)
    rows = blade.thickness_curve(ink, head, speeds)

    csv_path = os.path.join(_case.OUTPUT_DIR, "blade_curve.csv")
    with open(csv_path, "w", encoding="utf-8") as handle:
        columns = list(rows[0])
        handle.write(",".join(columns) + "\n")
        for row in rows:
            handle.write(
                ",".join(
                    f"{row[c]:.6g}" if isinstance(row[c], float) else str(row[c])
                    for c in columns
                )
                + "\n"
            )

    with open(os.path.join(_case.OUTPUT_DIR, "stats.json"), encoding="utf-8") as handle:
        stats = json.load(handle)
    blade_stats = stats["blade"]

    speeds_mm = [u * 1e3 for u in speeds]
    evaporation = [evaporation_regime_dry_thickness(ink, u) * 1e9 for u in speeds]
    landau = [
        landau_levich_thickness(ink, u, radius) * ink.solids_volume_fraction * 1e9
        for u in speeds
    ]
    governing = [row["dry_thickness_governing_m"] * 1e9 for row in rows]

    figure, axis = plt.subplots(figsize=(7.2, 5.0))
    axis.plot(
        speeds_mm,
        evaporation,
        color="#440154",
        linestyle=":",
        linewidth=1.6,
        label=r"evaporation regime, $h\propto U^{-1}$",
    )
    axis.plot(
        speeds_mm,
        landau,
        color="#21918c",
        linestyle=":",
        linewidth=1.6,
        label=r"Landau-Levich regime, $h\propto U^{2/3}$",
    )
    axis.plot(speeds_mm, governing, color="#000000", linewidth=2.2, label="governing branch")

    crossover_mm = blade_stats["crossover_speed_m_s"] * 1e3
    thinnest_nm = blade_stats["minimum_dry_thickness_m"] * 1e9
    axis.plot([crossover_mm], [thinnest_nm], marker="o", color="black", markersize=7)
    axis.annotate(
        f"crossover U* = {crossover_mm:.2f} mm/s\nthinnest film {thinnest_nm:.0f} nm",
        xy=(crossover_mm, thinnest_nm),
        xytext=(crossover_mm * 0.06, thinnest_nm * 3),
        fontsize=9,
        arrowprops=dict(arrowstyle="->", linewidth=1.1),
    )
    axis.plot(
        [blade_stats["speed_m_s"] * 1e3],
        [blade_stats["dry_thickness_m"] * 1e9],
        marker="s",
        color="#fde725",
        markeredgecolor="black",
        markersize=9,
        linestyle="none",
        label="working point",
    )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("coating speed (mm/s)")
    axis.set_ylabel("dry film thickness (nm)")
    axis.set_ylim(10, 3000)
    axis.set_title(
        "Blade coating: the two deposition regimes\n"
        f"{stats['ink']['name']}, R_meniscus = {radius * 1e6:.0f} um, "
        f"E = {ink.evaporation_flux:.1e} m2/s (assumed)"
    )
    axis.legend(loc="upper left", fontsize=8, framealpha=0.9)
    axis.grid(True, which="both", alpha=0.15)
    _case.draft_stamp(axis, args.final)
    figure.tight_layout()

    path = os.path.join(_case.FIGURE_DIR, "blade_regimes.png")
    figure.savefig(path, dpi=200)
    print(f"wrote {path}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
