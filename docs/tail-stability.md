# LR1600 — Tail, Boom & Stability Integration v1

## Decision status

This is a **preliminary design assumption**, not release-to-manufacture and
not a first-flight approval.  The geometry is selected to make downstream
layout, boom and mass work testable; the existing wing geometry, Clark Y,
mass target and datum have not been changed.  Reproduce the numerical result:

```bash
./tools/cad-shell.sh scripts/tail_stability.py
```

The generated [tail summary](../analysis/tail/summary.json) and plots are
evidence, not source of truth.  The intended selected geometry is stored only
in typed `config/aircraft.yaml`; sweep cases remain in the generated study.

## Known

- The single aircraft datum is the root-wing leading edge: `+X` aft, `+Y`
  right and `+Z` up; all reported positions below use it.
- Wing area is 0.360 m², span 1600 mm and MAC is obtained from
  `WingConfig.mean_aerodynamic_chord_mm` (225.926 mm).  The model wing-MAC
  quarter-chord is x=68.519 mm; it is a longitudinal-model reference, not an
  assertion that the 2-D Clark-Y quarter-chord is the aircraft neutral point.
- Target mass is 2400 g; conservative wing stall study is 37.55 km/h.  The
  tail study does not change either result.
- The intended configuration is twin boom, one common horizontal stabilizer,
  two symmetric fins and a central pusher.  No propeller, motor, ESC or
  battery is selected.

## Selected preliminary baseline

The 650 mm arm is measured from the model wing AC to horizontal-tail AC.  It
is the middle of the 550/650/750 mm study: 550 mm needs 0.0665–0.0813 m² for
`Vh=0.45–0.55`, whereas 750 mm needs 0.0488–0.0596 m² but lengthens both boom
bending lever and overall aircraft.  At 650 mm, the selected 0.0630 m² gives
`Vh=0.5035`, close to the middle of that explicitly assumed screening range.
For a transparent trade-only paired-Ø20×18 tube mass proxy, 550/650/750 mm
means 95–108/113–128/130–148 g and boom mass moments about the wing AC of
0.026–0.030/0.037–0.042/0.049–0.055 kg·m; the bending-lever proxy grows
0.61/1.00/1.54. These are design estimates, not mass-ledger entries. The
corresponding tail-AC X positions are 618.5/718.5/818.5 mm. The structural
penalty is assessed separately in `docs/booms.md`.

| Item | Preliminary value |
|---|---:|
| Horizontal-tail AC / arm | x=718.519 mm / 650 mm |
| Horizontal stabilizer | 700 mm span × 90 mm chord; 0.0630 m²; AR 7.78 |
| Elevator | 40% chord (36 mm), 0.02520 m² |
| Each fin | 230 mm height, 135/96.17 mm root/tip chord, 0.026585 m² |
| Both fins, total effective area | 0.053169 m²; `Vv=0.06000` |
| Preliminary rudder | 30% chord; its actual need/effectiveness is TBD |

The two fin areas are added before calculating `Vv`; `Vv` is not the area of
one fin. A conservative directional proxy sweeps fin lift slope
2.8/3.15/3.5 per rad, twin-fin efficiency 0.65/0.78/0.90 and non-tail
`Cnβ=-0.08/-0.05/-0.02 per rad`. The selected `Vv=0.060` yields worst proxy
`Cnβ=+0.029/rad`, above the +0.025/rad screen. It cannot establish the full
aircraft derivative: fuselage/boom side areas, interference and rudder hinge
effectiveness remain TBD.

## Longitudinal model and CG

The reproducible stick-fixed, linear model is:

`h_n = h_ac,w + eta_t (a_t/a_w) (1 - d epsilon/d alpha) Vh + delta_h,fus`

Finite-surface lift slopes use a first-order lifting-line correction for the
wing (`a_w=4.787/rad`). The 90-mm-chord tail is independently swept at low Re
as `a_t=3.4/4.2/4.9 rad⁻¹`; this uncertainty is not folded into tail dynamic
pressure efficiency. The sweep is deliberately broad: tail efficiency
0.78/0.85/0.92, downwash gradient
0.35/0.45/0.55 and fuselage/boom neutral-point shift −0.040/−0.020/0 MAC.
The last term is left as uncertainty rather than silently zeroing an
unmodelled fuselage.

The resulting neutral-point sensitivity is **0.336–0.558 MAC**, or
**x=87.84–138.14 mm**. The nominal bookkeeping case (`a_t=4.2`, 0.85, 0.45,
−0.020) is **0.437 MAC**, x=110.66 mm. It is not a measured neutral point.

| CG case | CG (% MAC) | x from root-wing LE | Static margin across stated sensitivity |
|---|---:|---:|---:|
| Design forward | 24% | 66.26 mm | 9.55–31.82% MAC |
| First-flight preliminary | 25% | 68.52 mm | 8.55–30.82% MAC |
| Design aft | 28% | 75.30 mm | 5.55–27.82% MAC |

The limits are derived before YAML validation: low-speed trim at conservative
stall may use at most 12° (60% of future-proven ±20° travel), yielding a
forward limit 23.8% MAC; every design point must retain ≥5% MAC static margin,
yielding an aft limit 28.55% MAC. Therefore the deliberately rounded
**initial/design CG envelope is 24–28% MAC** (x=66.26–75.30 mm), using the
existing root-wing-LE datum only. The conservative preliminary first-flight
starting point is **25% MAC**, x=68.52 mm. Its nominal static margin is
18.65% MAC and its full stated-model range is 8.55–30.82% MAC. Before flight the assembled
aircraft must have measured mass properties and be checked against this
envelope; a ground and flight-test programme is still required.

The assumptions with greatest CG influence are tail dynamic-pressure
efficiency, downwash gradient and the unmodelled fuselage/boom contribution.
Tail incidence, tail airfoil/Re polar, propwash and thrust-line effects can
change trim even where the stick-fixed neutral-point screen remains stable.

## Trim and elevator authority

Using existing clean-polar `Cm` near −0.08 only as a representative wing
moment, the model sweeps `Cm=-0.10…−0.06`, tail efficiency 0.78…0.92,
tail lift slope 3.4…4.9/rad, elevator effectiveness 0.40…0.60 and all three CG points. Required
**incremental** elevator deflection relative to a tail zero-lift reference is
−11.78…−1.29° at 37.55 km/h, −11.14…−2.04° at 60 km/h, −11.03…−2.17° at 70 km/h
and −10.91…−2.31° at 90 km/h. The 60 km/h climb screening condition has the
same weight-based `CL` as level 60 km/h before future power-on effects.

These are not absolute servo-neutral settings: tail zero-lift angle, installed
incidence and actual downwash angle are TBD. They show that the preliminary
40%-chord elevator remains within 60% of future-proven ±20° usable linear
travel in the linear pre-stall screen. This is only a
conditional recovery-authority screen—no XFOIL post-stall result is used to
claim recovery behaviour.

## Pusher disk and boom clearance

At the propeller plane clearance is checked in 3-D, not with a simple
spacing-greater-than-diameter rule:

`sqrt(y_boom² + z_boom²) > R_prop + R_boom + clearance`.

The following is a **clearance study assumption** of 10 mm boom outer radius
and 30 mm manufacturing/dynamic clearance, aligned with the structural
preferred-OD screening envelope; it is not a selected tube.  At
`z=0`, the minimum symmetric boom axis spacing is:

| Study diameter | Minimum spacing | 460 mm baseline spacing (±230 mm) |
|---:|---:|---:|
| 10 in / 254 mm | 334.0 mm | clears |
| 12 in / 304.8 mm | 384.8 mm | clears |
| 14 in / 355.6 mm | 435.6 mm | clears |
| 15 in / 381 mm | 461.0 mm | does not clear |

The 12–14 in range is the preferred preliminary disk envelope: it leaves
meaningful clearance at the 460 mm study spacing while reducing disk loading
relative to 10 in for the 60–80 km/h cruise and climb thrust envelope from
`docs/propulsion.md`.  A 15 in disk is geometrically possible only while the
eventual boom OD, deflection allowance, prop-plane Z offset, fuselage/motor
structure and tail intersection retain the above radial margin; it has a
clear integration penalty and is not selected.  This conclusion is not a
propeller SKU recommendation.

## Remaining TBD

- tail airfoil, polar at its actual Reynolds range, incidence and setting;
- fuselage/boom aerodynamic contribution, tail dynamic pressure, downwash and
  power-on propwash/thrust-line trim;
- final rudder arrangement, control linkage travel and measured hinge
  effectiveness;
- boom section, OD, deflection, dynamic clearance and wing attachment;
- actual component masses/locations and first-flight measured CG; and
- all hardware choices and maximum propeller diameter.
