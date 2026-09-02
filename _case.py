"""The worked case every example script uses.

One definition, imported by all four scripts, so the figures, the QA report and
the README block cannot describe different inks.

The ink is a p-i-n perovskite precursor of the kind used for blade- and
slot-die-coated minimodules. The numbers are plausible literature values, not
measurements: see docs/VERIFY_CHECKLIST.md item V5. Replace them with your own
rheometry, tensiometry and pycnometry before drawing any conclusion about your
own process.
"""

from __future__ import annotations

import os

from pvcoat import BladeGeometry, Fluid, SlotDieGeometry

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
FIGURE_DIR = os.path.join(OUTPUT_DIR, "figures")

#: Ink properties. Every one of these is an assumption until measured.
INK_ASSUMPTIONS = {
    "viscosity": "3 cP",
    "surface_tension": "30 mN/m",
    "density": "1.45 g/cm3",
    "molarity_mol_per_l": 1.4,
    "molar_mass_g_per_mol": 632.6,
    "film_density": "4.1 g/cm3",
    "evaporation_flux": "1e-10 m2/s",
}


def ink() -> Fluid:
    """1.4 M FAPbI3 in DMF/DMSO, as an order-of-magnitude stand-in."""
    return Fluid.from_molarity(
        viscosity=INK_ASSUMPTIONS["viscosity"],
        surface_tension=INK_ASSUMPTIONS["surface_tension"],
        density=INK_ASSUMPTIONS["density"],
        molarity_mol_per_l=INK_ASSUMPTIONS["molarity_mol_per_l"],
        molar_mass_g_per_mol=INK_ASSUMPTIONS["molar_mass_g_per_mol"],
        film_density=INK_ASSUMPTIONS["film_density"],
        evaporation_flux=INK_ASSUMPTIONS["evaporation_flux"],
        name="1.4 M FAPbI3 in DMF/DMSO",
    )


def slot_die() -> SlotDieGeometry:
    """A lab slot die over a 50 mm stripe."""
    return SlotDieGeometry(
        gap_downstream="100 um",
        gap_upstream="100 um",
        lip_length_downstream="1 mm",
        lip_length_upstream="1 mm",
        slot_width="100 um",
        coating_width="50 mm",
        name="lab slot die",
    )


def blade() -> BladeGeometry:
    """A blade at a 150 um gap over the same stripe."""
    return BladeGeometry(gap="150 um", coating_width="50 mm", name="lab blade")


#: The target the whole example is built around: a 700 nm dry perovskite layer.
TARGET_DRY_THICKNESS_M = 700e-9

#: Nominal coating speeds for the worked point.
SLOT_DIE_SPEED_M_S = 0.010
BLADE_SPEED_M_S = 0.015


def ensure_directories() -> None:
    os.makedirs(FIGURE_DIR, exist_ok=True)


def draft_stamp(axis, final: bool) -> None:
    """Stamp a figure DRAFT unless it was built with --final.

    The stamp comes off only after the verification gate in
    docs/VERIFY_CHECKLIST.md has been completed by the author.
    """
    if final:
        return
    axis.text(
        0.5,
        0.5,
        "DRAFT",
        transform=axis.transAxes,
        fontsize=64,
        color="0.5",
        alpha=0.18,
        ha="center",
        va="center",
        rotation=30,
        zorder=10,
    )
