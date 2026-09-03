# LR1600 CG integration v2

This is a reproducible **design estimate** for the 2,600-g integration case,
not a weighed aircraft or a flight-CG release.  The single editable mass
ledger is [`config/hardware.yaml`](../config/hardware.yaml); the complete,
machine-readable derived ledger and all arithmetic are in
[`analysis/mass/summary.json`](../analysis/mass/summary.json), produced by
[`scripts/cg_integration.py`](../scripts/cg_integration.py).  No mass in this
document is a second source.

## P60B placement and baseline closure

The P60B branch is a 503-g complete 6S1P **packaging estimate** with a
155 x 75 x 28-mm envelope.  The pack has a 50-mm indexed rail:

| Setting | Battery centre X | Baseline wheels CG X | CG % MAC |
|---|---:|---:|---:|
| Forward | -382.5 | 66.71 | 24.20% |
| Nominal rail reference | -370.0 | 69.19 | 25.30% |
| Aft | -332.5 | 76.64 | 28.59% |

The exact central-ledger pack centres required are -384.78, -373.40,
-362.03 and -339.27 mm for 24, 25, 26 and 28% MAC respectively. Therefore
25% is reachable without ballast by moving 3.40 mm forward of the nominal
rail reference. The exact 24% point is 2.28 mm ahead of the retained forward
rail limit and is no longer claimed reachable by this design estimate. This
is a reported consequence of removing 6 g at the forward nose-gear station;
the validated rail geometry was not changed. The physical pack needs X=-460 at the
forward index; the X=-500 nose and top hatch are deliberate consequences of
that calculation, not an arbitrary long nose.  A real pack/dummy must prove
the removal path, cable bend radius, index stops and 44.4-N retention proof
before production CAD.

## Unified central mass result

The central summer estimate is **2533.5 g**: 66.5 g below the 2,600-g
integration design case.  Its bounded low/central/high mass screen is
**2260.6 / 2533.5 / 2846.4 g**. The low/high screen varies only entries with
explicit component-local ranges; fixed datasheet entries are held central. It
is not an acceptable release mass and shows why actual assemblies and their
moments must be weighed.

Included central groups are wing plus joiner 591.25 g, boom pair 120.28 g,
empennage 115 g, 13x10 motor/prop/ESC/mount 291 g, P60B pack 503 g, five
servos 43.2 g, mechanical linkages 40 g, avionics/regulators/sensor 140.8 g,
wiring 95 g (including the long 4-mm2 power pair/capacitor allowance),
fuselage structural group 398 g, and complete fixed-nose wheel gear 196 g.
The JSON lists every individual ledger component and its X/Y/Z point.

The 398-g fuselage group includes its structural hardpoints; they are not
added again to landing gear.  Wheel gear is replaced, not supplemented, by
the ski module.  The optional camera is likewise excluded from baseline.

## Seasonal and recording configurations

| Configuration | Mass at nominal rail | 25% target battery X | Result at current nominal / forward / aft rail |
|---|---:|---:|---|
| Wheels, FPV | 2533.5 g | -373.40 | 25.30 / 24.20 / 28.59% MAC |
| Skis, FPV | 2569.5 g | -365.57 | 24.62 / 23.53 / 27.87% MAC |
| Wheels, FPV + 45-g HD central payload | 2578.5 g | -351.62 | 23.41 / 22.33 / 26.65% MAC |

For wheels, move the pack forward about 3.4 mm from the nominal rail reference
to make 25%; for skis, move it aft about 4.4 mm. For the 45-g recording case,
move it aft about 18.4 mm. All 25% cases close without ballast. The current
rail does **not** cover the complete 24--28% range for wheels, skis or the HD
payload: wheels miss exact 24% by 2.28 mm, while the other limitations remain
configuration-specific. These are explicitly reported limitations,
not reasons to put electronics in the tail.  The HD study range is 25--60 g;
its actual mount/camera mass must be entered before any flight release.

## Handling implication

At the exact 25% case, battery X=-373.4048 mm and CG X=68.5185 mm put the pack
441.92 mm (about 442 mm) ahead of aircraft CG. Its point-mass pitch-inertia
contribution is 0.0982 kg m2 (0.0992 kg m2 including the 155-mm pack's
longitudinal extent). It is an intentional penalty of
no-ballast closure.  The countermeasure is mass concentration: FC and the
three tail servos stay close to the wing/CG region; no heavy tail electronics
are accepted for mechanical convenience.

## Release blockers

- Weigh pack, wing, booms, tail, fuselage, gear and actual accessories, then
  recompute this ledger and physically measure all-up CG.
- Prove the pack box, long primary nose path, wing/boom/motor interfaces and
  gear/skis hardpoints before cutting production parts.
- Close motor/13x10 propulsion, cooling, vibration, EMI and servo/linkage
  evidence.  The 2,600-g value is technically coherent as an integration
  case, but remains conditional rather than a final flight MTOW.
