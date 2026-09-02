#!/usr/bin/env python3
"""Rewrite the README worked-example block from outputs/stats.json.

The stats-file rule: no number is typed into prose. This script generates the
block between the GENERATED markers in README.md, so the documentation cannot
drift from the code that produced it.

    python examples/04_render_readme.py           # rewrite the block
    python examples/04_render_readme.py --check   # fail if it is out of date
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _case  # noqa: E402

BEGIN = "<!-- BEGIN GENERATED: examples/04_render_readme.py -->"
END = "<!-- END GENERATED -->"

README = os.path.join(os.path.dirname(_case.OUTPUT_DIR), "..", "README.md")
README = os.path.normpath(README)


def render(stats: dict) -> str:
    ink = stats["ink"]
    slot = stats["slot_die"]
    blade = stats["blade"]
    vacuum_lo, vacuum_hi = slot["vacuum_window_pa"]
    needs_vacuum = (
        "a vacuum box is required" if vacuum_lo > 0 else "no vacuum box is required"
    )

    return f"""{BEGIN}
A {ink['name']} ink, targeting a {slot['target_dry_thickness_m'] * 1e9:.0f} nm dry
perovskite layer over a {slot['coating_width_m'] * 1e3:.0f} mm stripe. Ink properties are
illustrative placeholders, not measurements: see verification point V5.

Ink: mu = {ink['viscosity_pa_s'] * 1e3:.3g} mPa s, sigma = {ink['surface_tension_n_m'] * 1e3:.3g} mN/m,
rho = {ink['density_kg_m3']:.4g} kg/m3, solids {ink['solids_concentration_kg_m3']:.4g} kg/m3,
film density {ink['film_density_kg_m3']:.4g} kg/m3, so the solids volume fraction is
{ink['solids_volume_fraction']:.3f} and the film shrinks by a factor of {1 / ink['solids_volume_fraction']:.2f} on drying.

**Slot die**, {slot['gap_downstream_m'] * 1e6:.0f} um gap at {slot['speed_m_s'] * 1e3:.0f} mm/s:

| quantity | value |
|---|---|
| wet thickness for the target | {slot['target_wet_thickness_m'] * 1e6:.2f} um |
| pump setting | {slot['flow_rate_ml_min']:.3f} mL/min |
| capillary number | {slot['capillary_number']:.3g} |
| Reynolds number | {slot['reynolds_number']:.3g} |
| low-flow limit | {slot['low_flow_limit_m'] * 1e6:.2f} um |
| margin to the low-flow limit | {slot['low_flow_margin']:.1f}x |
| minimum thickness with no vacuum | {slot['min_thickness_no_vacuum_m'] * 1e6:.2f} um |
| vacuum window | {vacuum_lo / 100:.1f} to {vacuum_hi / 100:.1f} mbar, so {needs_vacuum} |
| air-entrainment speed | {slot['air_entrainment_speed_m_s']:.2f} m/s ({slot['speed_margin']:.0f}x margin) |
| verdict | **{slot['verdict']}** |

At this gap the {slot['target_dry_thickness_m'] * 1e9:.0f} nm target stays coatable up to
{slot['max_speed_for_target_m_s'] * 1e3:.0f} mm/s, above which the rising low-flow limit
overtakes it.

**Blade**, {blade['gap_m'] * 1e6:.0f} um gap, meniscus radius {blade['meniscus_radius_m'] * 1e6:.0f} um:

| quantity | value |
|---|---|
| regime crossover U* | {blade['crossover_speed_m_s'] * 1e3:.2f} mm/s |
| thinnest achievable dry film, at U* | {blade['minimum_dry_thickness_m'] * 1e9:.0f} nm |
| at {blade['speed_m_s'] * 1e3:.0f} mm/s, governing regime | {blade['regime'].replace('_', '-')} |
| dry thickness there | {blade['dry_thickness_m'] * 1e9:.0f} nm |
| verdict | **{blade['verdict']}** |

Generated {stats['generated_utc']} by pvcoat {stats['pvcoat_version']} ({stats['status']}).
{END}"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the README block is out of date",
    )
    args = parser.parse_args()

    stats_path = os.path.join(_case.OUTPUT_DIR, "stats.json")
    if not os.path.exists(stats_path):
        print("run examples/01_worked_case.py first")
        return 1
    with open(stats_path, encoding="utf-8") as handle:
        stats = json.load(handle)

    with open(README, encoding="utf-8") as handle:
        text = handle.read()

    start = text.index(BEGIN)
    stop = text.index(END) + len(END)
    updated = text[:start] + render(stats) + text[stop:]

    if args.check:
        if updated != text:
            print("README worked-example block is out of date; run without --check")
            return 1
        print("README numbers match stats.json")
        return 0

    with open(README, "w", encoding="utf-8") as handle:
        handle.write(updated)
    print(f"rewrote the generated block in {README}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
