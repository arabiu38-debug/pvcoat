#!/usr/bin/env python3
"""Compute the worked case and write outputs/stats.json and outputs/qa_report.txt.

Every number quoted in the README, in the figures and in any document about this
package comes from stats.json, which this script writes. Nothing is typed into
prose by hand, so the text and the code cannot disagree.

    python examples/01_worked_case.py
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _case  # noqa: E402

import pvcoat  # noqa: E402
from pvcoat import blade as blade_module  # noqa: E402
from pvcoat import slotdie as slotdie_module  # noqa: E402
from pvcoat.limits import (  # noqa: E402
    air_entrainment_speed,
    low_flow_limit,
    regime_crossover_speed,
)
from pvcoat.thickness import flow_rate_for_dry_thickness, wet_thickness_for_dry  # noqa: E402


def build_stats() -> dict:
    ink = _case.ink()
    die = _case.slot_die()
    blade_head = _case.blade()

    target_wet = wet_thickness_for_dry(_case.TARGET_DRY_THICKNESS_M, ink)
    flow = flow_rate_for_dry_thickness(
        _case.TARGET_DRY_THICKNESS_M, ink, die.coating_width, _case.SLOT_DIE_SPEED_M_S
    )
    slot_point = slotdie_module.evaluate(
        ink, die, _case.SLOT_DIE_SPEED_M_S, target_wet_thickness=target_wet
    )
    blade_point = blade_module.evaluate(ink, blade_head, _case.BLADE_SPEED_M_S)
    crossover = regime_crossover_speed(ink, blade_head.effective_meniscus_radius)

    # Widest speed at which the 700 nm target still clears the low-flow limit.
    speed_ceiling = None
    speed = 1e-4
    while speed < 1.0:
        if low_flow_limit(ink, die, speed) > target_wet:
            break
        speed_ceiling = speed
        speed *= 1.01

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pvcoat_version": pvcoat.__version__,
        "python": platform.python_version(),
        "status": "DRAFT",
        "ink": {
            "name": ink.name,
            "assumptions": _case.INK_ASSUMPTIONS,
            "viscosity_pa_s": ink.viscosity,
            "surface_tension_n_m": ink.surface_tension,
            "density_kg_m3": ink.density,
            "solids_concentration_kg_m3": ink.solids_concentration,
            "film_density_kg_m3": ink.film_density,
            "solids_volume_fraction": ink.solids_volume_fraction,
            "capillary_length_m": ink.capillary_length,
        },
        "slot_die": {
            "gap_downstream_m": die.gap_downstream,
            "gap_upstream_m": die.gap_upstream,
            "coating_width_m": die.coating_width,
            "speed_m_s": _case.SLOT_DIE_SPEED_M_S,
            "target_dry_thickness_m": _case.TARGET_DRY_THICKNESS_M,
            "target_wet_thickness_m": target_wet,
            "flow_rate_m3_s": flow,
            "flow_rate_ml_min": flow * 6e7,
            "capillary_number": slot_point.capillary_number,
            "reynolds_number": slot_point.reynolds_number,
            "low_flow_limit_m": slot_point.low_flow_limit,
            "low_flow_margin": slot_point.low_flow_margin,
            "min_thickness_no_vacuum_m": slot_point.minimum_thickness_no_vacuum,
            "vacuum_window_pa": list(slot_point.vacuum_window),
            "air_entrainment_speed_m_s": slot_point.air_entrainment_speed,
            "speed_margin": slot_point.speed_margin,
            "verdict": slot_point.verdict,
            "max_speed_for_target_m_s": speed_ceiling,
        },
        "blade": {
            "gap_m": blade_head.gap,
            "meniscus_radius_m": blade_head.effective_meniscus_radius,
            "speed_m_s": _case.BLADE_SPEED_M_S,
            "capillary_number": blade_point.capillary_number,
            "wet_thickness_m": blade_point.wet_thickness,
            "dry_thickness_m": blade_point.dry_thickness,
            "regime": blade_point.regime,
            "crossover_speed_m_s": crossover,
            "minimum_dry_thickness_m": blade_point.minimum_dry_thickness,
            "air_entrainment_speed_m_s": blade_point.air_entrainment_speed,
            "verdict": blade_point.verdict,
        },
        "air_entrainment_gutoff_kendrick_m_s": air_entrainment_speed(ink),
    }


def qa_report(stats: dict) -> str:
    """Checks a reader can run against the source papers by hand."""
    slot = stats["slot_die"]
    blade = stats["blade"]
    ink = stats["ink"]
    lines = [
        "pvcoat QA report -- DRAFT",
        f"generated {stats['generated_utc']} with pvcoat {stats['pvcoat_version']}",
        "",
        "This report exists so that every number in the documentation can be",
        "checked by hand against the equations in docs/MODELS.md. Nothing here is",
        "fitted; each line is one closed-form evaluation.",
        "",
        "1. Metering arithmetic",
        f"   solids volume fraction c/rho_film = {ink['solids_volume_fraction']:.6f}",
        f"   target dry {slot['target_dry_thickness_m'] * 1e9:.1f} nm"
        f" -> wet {slot['target_wet_thickness_m'] * 1e6:.4f} um",
        f"   check: {slot['target_wet_thickness_m'] * 1e6:.4f} um"
        f" x {ink['solids_volume_fraction']:.6f}"
        f" = {slot['target_wet_thickness_m'] * ink['solids_volume_fraction'] * 1e9:.1f} nm",
        f"   pump setting Q = h W U = {slot['flow_rate_ml_min']:.4f} mL/min",
        "",
        "2. Dimensionless groups at the slot-die working point",
        f"   Ca = mu U / sigma = {ink['viscosity_pa_s']:.4g} x {slot['speed_m_s']:.4g}"
        f" / {ink['surface_tension_n_m']:.4g} = {slot['capillary_number']:.6g}",
        f"   Re = rho q / mu = {slot['reynolds_number']:.6g}",
        f"   both are well inside the viscocapillary validity range"
        if slot["capillary_number"] < 1 and slot["reynolds_number"] < 1
        else "   WARNING: outside the viscocapillary validity range",
        "",
        "3. Low-flow limit",
        f"   h_min = 0.67 H_down Ca^(2/3) = 0.67 x {slot['gap_downstream_m'] * 1e6:.1f} um"
        f" x {slot['capillary_number']:.4g}^(2/3) = {slot['low_flow_limit_m'] * 1e6:.4f} um",
        f"   margin h_wet / h_min = {slot['low_flow_margin']:.2f}",
        f"   the 700 nm target stays coatable up to"
        f" {slot['max_speed_for_target_m_s'] * 1e3:.1f} mm/s at this gap",
        "",
        "4. Vacuum window",
        f"   window = {slot['vacuum_window_pa'][0] / 100:.3f} to"
        f" {slot['vacuum_window_pa'][1] / 100:.3f} mbar",
        f"   width = 4 sigma / H_up ="
        f" {4 * ink['surface_tension_n_m'] / slot['gap_upstream_m'] / 100:.3f} mbar"
        f" (check: {(slot['vacuum_window_pa'][1] - slot['vacuum_window_pa'][0]) / 100:.3f} mbar)",
        f"   lower bound is"
        f" {'positive, so a vacuum box is required' if slot['vacuum_window_pa'][0] > 0 else 'negative, so no vacuum box is required'}",
        "",
        "5. Air entrainment",
        f"   U_ae = 6.9 mu^-0.67 with mu = {ink['viscosity_pa_s'] * 1e3:.4g} mPa s"
        f" -> {stats['air_entrainment_gutoff_kendrick_m_s']:.4g} m/s",
        f"   margin at the slot-die working point: {slot['speed_margin']:.1f}x",
        "",
        "6. Blade regimes",
        f"   crossover U* = {blade['crossover_speed_m_s'] * 1e3:.4f} mm/s",
        f"   thinnest achievable dry film at U*:"
        f" {blade['minimum_dry_thickness_m'] * 1e9:.1f} nm",
        f"   at {blade['speed_m_s'] * 1e3:.1f} mm/s the {blade['regime']} branch governs,"
        f" giving {blade['dry_thickness_m'] * 1e9:.1f} nm",
        "",
        "7. Spot checks for the author (docs/VERIFY_CHECKLIST.md)",
        "   V1 vacuum-window sign convention against Higgins and Scriven (1980)",
        "   V2 Gutoff-Kendrick prefactor and units against the 1982 paper",
        "   V3 R_downstream,min = H_down / 2 by geometry",
        "   V4 the Ca and Re ceilings in pvcoat.validity",
        "   V5 every ink property above, against your own measurements",
        "   V6 the package name and the author block",
        "",
        "verdicts: slot die " + slot["verdict"] + ", blade " + blade["verdict"],
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final",
        action="store_true",
        help="mark the outputs released; only after the verification checklist is complete",
    )
    args = parser.parse_args()

    _case.ensure_directories()
    stats = build_stats()
    if args.final:
        stats["status"] = "released"

    stats_path = os.path.join(_case.OUTPUT_DIR, "stats.json")
    with open(stats_path, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2, sort_keys=False)
        handle.write("\n")

    report = qa_report(stats)
    if args.final:
        report = report.replace(" -- DRAFT", "")
    qa_path = os.path.join(_case.OUTPUT_DIR, "qa_report.txt")
    with open(qa_path, "w", encoding="utf-8") as handle:
        handle.write(report)

    print(report)
    print(f"wrote {stats_path}")
    print(f"wrote {qa_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
