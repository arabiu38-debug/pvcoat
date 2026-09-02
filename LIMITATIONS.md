# Limitations

Numbered so they can be cited in an issue or a review. Written before the README,
so the README cannot outrun them.

## Scope of the physics

1. **Newtonian inks only.** Every model assumes a single viscosity. Perovskite
   precursors with high solids loading, polymer additives or colloidal content
   shear-thin or shear-thicken, and the effect on the operating window is not
   captured by simply substituting an apparent viscosity. Khandavalli and
   Rothstein (2016) show that at the same shear-rate-dependent capillary number, a
   shear-thinning fluid needs a wet film roughly twice as thick as a Newtonian one
   before the coating is stable, while shear-thickening reduces the minimum
   thickness by around 10%. If your ink is non-Newtonian, evaluate the viscosity
   at the gap shear rate `U/H` (`Fluid.representative_shear_rate`) and treat the
   answer as indicative.

2. **Only three of the failure modes that bound a real window are implemented.**
   The low-flow limit, air entrainment and the vacuum bounds. Not implemented:
   ribbing, rivulets, breaklines, dripping, flooding at the upstream lip beyond a
   simple thickness check, bubble entrainment from the feed, or streaklines from
   die-lip defects. A point pvcoat calls operable can still fail through a
   mechanism pvcoat does not model. In Khandavalli and Rothstein's experiments the
   *observed* failure mode changed from breaklines to ribbing to air entrainment
   depending on gap and ink, all within a region a three-limit model would pass.

3. **Two-dimensional, steady, isothermal.** No cross-web variation, no edge
   effects, no start-stop transients, no substrate temperature gradient. Edge
   beads and the first and last centimetres of a stripe are exactly where
   real minimodule yield is lost, and pvcoat says nothing about them.

4. **No inertial regime.** The viscocapillary models are asymptotic in Ca and Re.
   Above Ca ≈ 1 the measured minimum wet thickness stops following Ca^(2/3), and
   at higher Ca and Re it falls again as inertia lengthens the bead — so pvcoat is
   *conservative* there, predicting a window narrower than reality. Carvalho and
   Kheshgi's high-Ca low-flow limit is not implemented; see NEXT_STEPS.

5. **Perfect wetting assumed.** Contact angles do not appear. Ruschak's and
   Higgins and Scriven's models pin both menisci at lip corners. Imperfect wetting
   enlarges the range over which the downstream contact line "pins" and raises the
   thickness at which the low-flow limit is reached, so a poorly wetting substrate
   is worse than pvcoat predicts. This matters directly for coating on
   self-assembled-monolayer-treated ITO, where the substrate energy is the whole
   point.

6. **The dry thickness is a floor.** `h_dry = h_wet · c/ρ_f` assumes a fully dense
   film and no solid lost during drying or annealing. Residual porosity, solvent
   retention and volume change on crystallisation all make the real film thicker.
   For perovskites the intermediate-phase route to the final film is not a simple
   volume-conserving dry-down, and this is the single largest source of error
   between a predicted and a measured layer thickness.

7. **Drying is not modelled at all** for slot-die. There is no model here of
   solvent removal, quenching by gas knife or vacuum, nucleation, or the
   crystallisation that decides whether a perovskite film is any good. pvcoat
   tells you what lands on the substrate, not what it becomes.

8. **The blade evaporation flux E is an apparatus constant that must be
   measured.** It is not a material property and cannot be looked up. Every
   evaporation-regime and crossover number is only as good as that measurement.
   The value used in the worked example is an order-of-magnitude placeholder.

## Numerical and implementation

9. **The vacuum-window pressure balance is a reconstruction.** See MODELS.md
   section 4 and verification point V1. Limiting cases and the analytic window
   width check out; the sign convention has not been confirmed against the primary
   source.

10. **The Gutoff–Kendrick prefactor and its units are taken from secondary
    literature**, not the 1982 paper. See verification point V2.

11. **The bisection root-finder** for the zero-vacuum thickness relies on
    ΔP_min(h) being monotone decreasing, which holds for the implemented balance
    but would not survive an arbitrary extension of it.

12. **No propagation of input uncertainty.** A viscosity known to ±20% gives a
    low-flow limit known to about ±13% (the 2/3 power), and pvcoat reports neither
    the input uncertainty nor the output one. Every number is a point estimate.

## Validation

13. **pvcoat has not been validated against experiment.** v0.1 reproduces
    published equations and passes analytic self-consistency tests. No coating
    trial has been run against its predictions. Until that happens it is a
    calculator for published models, and should be described that way and no other
    way. Closing this gap is the first item in NEXT_STEPS.
