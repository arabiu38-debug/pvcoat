# pvcoat

**Status: released, v0.1.0, 2 September 2026.** Author verification complete; see
`docs/VERIFICATION_RECORD.md`.

Operability windows and film thickness for slot-die and blade coating, computed
from process parameters using published models.

Given an ink and a coating head, pvcoat answers two questions that otherwise get
answered by trial and error: **how thick will the film be, wet and dry**, and **is
that film inside the window where the bead or meniscus is stable**. It implements
the low-flow limit, the Landau-Levich film thickness, the coating-bead vacuum
window and the air-entrainment speed, each with the validity range it was derived
for, and warns when a process point falls outside it.

It was written for scalable perovskite photovoltaics, where blade and slot-die
coating set the film that everything else depends on, but nothing in the physics
is specific to perovskites.

**pvcoat has not been validated against coating experiments.** v0.1 reproduces
published equations and checks itself analytically. Treat it as a calculator for
those equations, not as a predictor of your line. See `docs/LIMITATIONS.md`.

## Install

```bash
pip install pvcoat            # once released
pip install "pvcoat[viz]"     # adds matplotlib for the example figures
```

No runtime dependencies. Python 3.9 or newer.

## Use

```python
from pvcoat import Fluid, SlotDieGeometry, slotdie

ink = Fluid.from_molarity(
    viscosity="3 cP", surface_tension="30 mN/m", density="1.45 g/cm3",
    molarity_mol_per_l=1.4, molar_mass_g_per_mol=632.6,
    film_density="4.1 g/cm3",
)
die = SlotDieGeometry(
    gap_downstream="100 um", lip_length_downstream="1 mm",
    lip_length_upstream="1 mm", coating_width="50 mm",
)

point = slotdie.evaluate(ink, die, speed="10 mm/s", target_wet_thickness="3.24 um")
print(point.render())
```

Every quantity takes a unit string or a bare SI number. The result carries the
dimensionless groups, the margin to each limit, the vacuum window and any
validity warnings, not just a number.

The same from the command line:

```bash
pvcoat slot-die --viscosity "3 cP" --surface-tension "30 mN/m" \
    --density "1.45 g/cm3" --molarity 1.4 --molar-mass 632.6 \
    --film-density "4.1 g/cm3" --gap "100 um" --width "50 mm" \
    --speed "10 mm/s" --wet-thickness "3.24 um"

pvcoat blade --viscosity "3 cP" --surface-tension "30 mN/m" \
    --density "1.45 g/cm3" --molarity 1.4 --molar-mass 632.6 \
    --film-density "4.1 g/cm3" --evaporation-flux "1e-10 m2/s" \
    --gap "150 um" --width "50 mm" --speed "15 mm/s"

pvcoat window --viscosity "3 cP" --surface-tension "30 mN/m" \
    --density "1.45 g/cm3" --gap "100 um" --width "50 mm" \
    --speed-range "1 mm/s,8 m/s,70" --thickness-range "0.2 um,100 um,70" \
    --out window.csv

pvcoat references          # every model's source, with DOIs
```

Add `--json` for machine-readable output.

## Worked example

<!-- BEGIN GENERATED: examples/04_render_readme.py -->
A 1.4 M FAPbI3 in DMF/DMSO ink, targeting a 700 nm dry
perovskite layer over a 50 mm stripe. Ink properties are
illustrative placeholders, not measurements: see verification point V5.

Ink: mu = 3 mPa s, sigma = 30 mN/m,
rho = 1450 kg/m3, solids 885.6 kg/m3,
film density 4100 kg/m3, so the solids volume fraction is
0.216 and the film shrinks by a factor of 4.63 on drying.

**Slot die**, 100 um gap at 10 mm/s:

| quantity | value |
|---|---|
| wet thickness for the target | 3.24 um |
| pump setting | 0.097 mL/min |
| capillary number | 0.001 |
| Reynolds number | 0.0157 |
| low-flow limit | 0.67 um |
| margin to the low-flow limit | 4.8x |
| minimum thickness with no vacuum | 0.71 um |
| vacuum window | -4.4 to 7.6 mbar, so no vacuum box is required |
| air-entrainment speed | 3.31 m/s (331x margin) |
| verdict | **operable** |

At this gap the 700 nm target stays coatable up to
106 mm/s, above which the rising low-flow limit
overtakes it.

**Blade**, 150 um gap, meniscus radius 75 um:

| quantity | value |
|---|---|
| regime crossover U* | 0.63 mm/s |
| thinnest achievable dry film, at U* | 34 nm |
| at 15 mm/s, governing regime | landau-levich |
| dry thickness there | 284 nm |
| verdict | **operable** |

Generated 2026-09-02T17:40:53+00:00 by pvcoat 0.1.0 (released).
<!-- END GENERATED -->

![Slot-die operability window](examples/outputs/figures/slotdie_window.png)

![Blade coating regimes](examples/outputs/figures/blade_regimes.png)

Reproduce both, and the numbers above, with:

```bash
python examples/01_worked_case.py     # stats.json and qa_report.txt
python examples/02_slotdie_window.py  # the window figure
python examples/03_blade_regimes.py   # the regime figure
python examples/04_render_readme.py   # rewrites the block above from stats.json
```

No number in the block above is typed by hand. Each is interpolated from
`examples/outputs/stats.json`, which the pipeline writes, so the text and the code
cannot disagree. `python examples/04_render_readme.py --check` fails if they do.

## What it implements

| model | expression | source |
|---|---|---|
| pre-metered wet thickness | h = Q/(WU) | mass conservation |
| dry thickness | h_dry = h c/rho_f | mass conservation |
| low-flow limit | h_min = 0.67 H_d Ca^(2/3) | Ruschak 1976; Higgins and Scriven 1980 |
| vacuum window | bead pressure balance, width 4 sigma/H_u | Higgins and Scriven 1980; Ding et al. 2016 |
| zero-vacuum minimum | root of dP_min(h) = 0 | Ruschak 1976; Ding et al. 2016 |
| air entrainment | U = 6.9 mu^(-0.67), or Ca_crit sigma/mu | Gutoff and Kendrick 1982 |
| Landau-Levich | h = 1.34 R Ca^(2/3), or 0.94 l_c Ca^(2/3) | Landau and Levich 1942 |
| blade evaporation regime | h_dry = c E/(rho_f U) | Le Berre et al. 2009; Huang et al. 2024 |
| regime crossover | U* = [E sigma^(2/3)/(1.34 R mu^(2/3))]^(3/5) | Le Berre et al. 2009 |

Full derivations, symbol table and validity ranges: `docs/MODELS.md`.

Nothing is fitted or tuned. Empirical coefficients are module constants in
`pvcoat.limits`, so they can be replaced with your own measurements.

## Two counter-intuitive results worth knowing

**Running faster makes thin films harder.** The low-flow limit rises as Ca^(2/3),
so doubling the speed raises the thinnest coatable film by about 60%. The window
narrows from below as you speed up, until air entrainment closes it from the
right.

**The blade regime crossover does not depend on solids loading.** Diluting the ink
moves the whole thickness-versus-speed curve down without moving the speed at
which the film is thinnest.

## Documentation

- `docs/MODELS.md` - every equation, symbol, assumption, validity range, source
- `docs/LIMITATIONS.md` - thirteen numbered things this does not do
- `docs/VERIFICATION_RECORD.md` - what was verified for v0.1.0, and how
- `docs/VERIFY_CHECKLIST.md` - the reusable pre-release checklist
- `docs/NEXT_STEPS.md` - what v0.2 and beyond add
- `docs/BUILD_SPEC.md` - the spec this was built from

## Citation

See `CITATION.cff`. Cite the version you used, and cite the original papers for
the physics: pvcoat implements their work and does not replace it.

## License

MIT, see `LICENSE`. Documentation CC BY 4.0.

## Author

Abdulai Rabiu ([0000-0002-3739-140X](https://orcid.org/0000-0002-3739-140X)),
Wright Center for Photovoltaics Innovation and Commercialization, Department of
Physics & Astronomy, University of Toledo, Toledo, Ohio, USA.

## Contributing

Issues and pull requests welcome, particularly experimental validation data and
corrections to the implemented physics. See `CONTRIBUTING.md`.

## AI assistance

Code, documentation drafting and literature triage were AI-assisted. Every
modelling decision, coefficient and validity threshold is the author's, and every
number in this repository was verified by the author against the source papers
before release. What was checked, and what was decided at each judgement call, is
recorded in `docs/VERIFICATION_RECORD.md`.
