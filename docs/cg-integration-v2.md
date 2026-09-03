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
| Forward | -382.5 | 65.44 | 23.64% |
| Nominal first-flight reservation | -370.0 | 68.52 | 25.00% |
| Aft | -332.5 | 75.39 | 28.04% |

The exact central-ledger pack centres required are -381.39, -369.99,
-358.58 and -335.77 mm for 24, 25, 26 and 28% MAC respectively. Therefore
25% is reachable without ballast.  The physical pack needs X=-460 at the
forward index; the X=-500 nose and top hatch are deliberate consequences of
that calculation, not an arbitrary long nose.  A real pack/dummy must prove
the removal path, cable bend radius, index stops and 44.4-N retention proof
before production CAD.

## Unified central mass result

The central summer estimate is **2539.5 g**: 60.5 g below the 2,600-g
integration design case.  Its bounded low/central/high mass screen is
**2266.6 / 2539.5 / 2852.4 g**. The low/high screen varies only entries with
explicit component-local ranges; fixed datasheet entries are held central. It
is not an acceptable release mass and shows why actual assemblies and their
moments must be weighed.

Included central groups are wing plus joiner 591.25 g, boom pair 120.28 g,
empennage 115 g, 13x10 motor/prop/ESC/mount 291 g, P60B pack 503 g, five
servos 43.2 g, mechanical linkages 40 g, avionics/regulators/sensor 140.8 g,
wiring 95 g (including the long 4-mm2 power pair/capacitor allowance),
fuselage structural group 398 g, and complete wheel gear 202 g.
The JSON lists every individual ledger component and its X/Y/Z point.

The 398-g fuselage group includes its structural hardpoints; they are not
added again to landing gear.  Wheel gear is replaced, not supplemented, by
the ski module.  The optional camera is likewise excluded from baseline.

## Seasonal and recording configurations

| Configuration | Mass at nominal rail | 25% target battery X | Result at current nominal / forward / aft rail |
|---|---:|---:|---|
| Wheels, FPV | 2539.5 g | -369.99 | 25.00 / 23.90 / 28.29% MAC |
| Skis, FPV | 2575.5 g | -362.15 | 24.32 / 23.24 / 27.56% MAC |
| Wheels, FPV + 45-g HD central payload | 2584.5 g | -348.20 | 23.12 / 22.05 / 26.35% MAC |

For skis, move the pack aft about 7.9 mm from the nominal index to make 25%.
For the 45-g recording case, move it aft about 21.8 mm. Both 25% cases close
without ballast.  The current rail does **not** cover the complete 24--28%
range for skis or the HD payload: these are explicitly reported limitations,
not reasons to put electronics in the tail.  The HD study range is 25--60 g;
its actual mount/camera mass must be entered before any flight release.

## Handling implication

At baseline 25% MAC the pack is roughly 436 mm ahead of aircraft CG.  Its
point-mass pitch-inertia contribution is about 0.096 kg m2 (about 0.097 kg m2
including its longitudinal extent).  It is an intentional penalty of
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
