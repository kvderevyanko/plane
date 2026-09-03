# LR1600 pusher / ground-clearance integration review v1

**Status:** preliminary integration review.  It is neither a propeller/motor
selection nor production landing-gear CAD.  It does not alter the wing geometry
or wing structural concept.  Coordinates are in **mm** from the root-wing-LE
datum; +X is aft and +Z is up.  The inputs below are the current typed
`config/aircraft.yaml` values at the time of this review.

## Decision

Keep **13 x 10 in pusher** as the preferred rough-field integration case.  At
the configured motor-axis height it retains a declared **69 mm** clearance in
the defined full-rough screen, 9 mm above the 60-mm requirement.  This is a
small, useful *preliminary* margin, not an approval for a rotating propeller.

A 14-in disk is a **secondary integration case only**.  With the very same
stance and deductions it removes 12.7 mm from every result, leaving 56.3 mm in
the declared full-rough case.  It therefore misses the 60-mm requirement by
3.7 mm before actual tyre, leg, mount and blade measurements.  Do not release a
14-in installation until its own higher-axis/gear and boom-clearance proof has
passed.

## Datum, source inputs and method

| Typed source field | Value | Status |
|---|---:|---|
| `aircraft.target_mass_g` | 2,600 g | preliminary integration/design case |
| `propulsion.propeller_plane_x_mm` / `motor_axis_z_mm` | X=430 / Z=+50 | preliminary integration assumption |
| `ground_operations.static_propeller_axis_height_mm` | 320 | preliminary installation assumption |
| `ground_operations.main_wheel_x_mm` / `nose_wheel_x_mm` | +125 / -250 | preliminary installation assumption |
| Main/nose wheel diameter; track | 100 / 75; 350 | preliminary installation assumption |
| Tail-low angle | 8 deg | bounded kinematic assumption |
| Full-rough clearance goal | 60 | preliminary requirement |
| Boom axes | Y=+/-230, Z=0 | initial design assumption; tube OD is TBD |

The static ground plane implied by the axis-height field is Z=-270.  For a
rigid circular disk, level lower-tip clearance is

`C_static = H_axis - D_prop / 2`.

At tail-low rotation about the main-contact line, the aft prop-plane motion is

`dZ_pitch = (X_prop - X_main) sin(theta)`.

Here, `X_prop - X_main = 305 mm`, and `dZ_pitch = 42.45 mm` at 8 deg.  The
typed `compressed`, `tail_low` and `full_rough` fields are retained results
from the structural integration screen; their individual allocations are not
yet typed.  They must not be represented as a new analytic prediction.

## Vertical-clearance results

| Case | 13 in, D=330.2 mm | 14 in, D=355.6 mm on identical stance | Requirement / finding |
|---|---:|---:|---|
| Static, level | 154.9 mm | 142.2 mm | geometric result |
| Compressed level | 137.0 mm (typed) | 124.3 mm | 14-in value is 13-in typed result -12.7 |
| Compressed + 8-deg tail-low | 93.0 mm (typed) | 80.3 mm | pitch loss is 42.45 mm before retained rounding/allocation |
| Full rough | **69.0 mm (typed)** | **56.3 mm** | 13 in passes 60 mm by 9.0; 14 in fails by 3.7 |

The 12.7-mm penalty is solely the radius change from 13 to 14 in.  A 14-in
installation needs **+12.7 mm axis height** to reproduce the 13-in clearance
table, or at least **+3.7 mm proven retained margin** merely to attain 60 mm in
the current scalar full-rough screen.  The former is the more defensible design
comparison; the latter consumes essentially all uncertainty margin.  A legacy
claim that the current 14-in case requires 13 mm taller gear is only applicable
when comparing like-for-like clearances; it is not a reason to retain a
different old 13-in geometry.

The configured static value is internally consistent: `320 - 165.1 = 154.9
mm`.  The following case fields cannot yet be regenerated only from typed
fields: 154.9 -> 137.0 loses 17.9 mm, 137.0 -> 93.0 loses 44.0 mm, and 93.0 ->
69.0 loses 24.0 mm.  Before production CAD, type and measure the components of
those deductions at minimum as actual tyre radius, normal/full compression,
one-main differential compression/airframe-centre descent, local obstacle/rut
height at the prop plane, wear/build allowance, motor-plate deflection and
rotating-blade envelope.  Until then 69 mm is an assumption, not a validated
dynamic clearance.

Pure rigid-body roll of an ideal circular propeller about its centred hub does
not change the vertical disk radius on a flat plane.  It does *not* clear the
one-main case: compliance can lower the hub, uneven terrain need not be flat at
the prop plane, and the motor/boom structure and blade are not rigid ideal
geometry.  The present 9-mm retained margin must cover only evidence-backed
terms; it is not an unallocated licence for one-wheel/rut operation.

## Gear-height and handling implications

The 100-mm main wheels place their axle at Z=-220 for the implied static plane;
with the typed main hardpoint at Z=-60 this leaves about 160 mm from hardpoint
to axle centre.  It is a geometry reservation, not a selected GFRP-leg length
or a spring-travel claim.  Reducing the wheel to 90 mm while holding the
hardpoint and leg geometry would lower the axle/aircraft by 5 mm; retaining the
current 320-mm prop-axis height would then require 5 mm more effective leg
height.  Thus the current 100-mm main is a sensible rough-surface integration
choice, provided its measured mass and rolling resistance remain acceptable.

The wheelbase is 375 mm.  At preliminary 25%-MAC CG X=68.52 mm, mains are
56.48 mm aft of CG and the level-ground static nose reaction is about 15.1% of
weight (`(125 - 68.52) / 375`).  Over the 24--28% MAC design CG range it is
13.3--15.7%.  This supports a positive nose-wheel load without placing the
mains unnecessarily far aft.  Rotation authority, braking nose-over, steering
loads and the actual stance angle remain TBD because CG height, wheel/tyre
properties, strut kinematics, braking and runway friction are not typed.

No numerical wheel/fuselage drag increment is justified yet: tyre widths,
wheel geometry, leg/axle frontal areas, fairing form and the external fuselage
sections are unselected.  The 900 x 180 x 190-mm fuselage envelope has a
rectangular upper-bound frontal area of 0.0342 m2 and length-to-maximum-height
ratio 4.68; this is only a packaging bound, not an aerodynamic CdA.  Keep
hatches flush, avoid a broad motor plate directly upstream of the disk, and
measure or model the all-airframe CdA with the selected wheels before making
endurance or top-speed claims.

The fuselage ends at X=+410 while the propeller plane is X=+430: only 20 mm
separates their reference stations.  This prevents a nominal envelope
intersection but is not an installed pusher-flow or blade-root clearance
validation.  The selected propeller's hub, root chord, axial blade sweep/flex,
adapter, motor plate, boom clamps and cooling-outlet flow must be checked as a
single 3-D rotating envelope.

## Boom / prop radial screen

This is a conditional screen using the prior 20-mm boom-OD study and a 30-mm
required free gap.  It is not a selection of the current TBD boom tube.  At
the prop plane, the hub-to-boom-axis radial distance is
`sqrt(230^2 + 50^2) = 235.37 mm`.

| Disk | Geometric blade-to-20-mm-boom-surface gap | Margin after 30-mm required free gap | Result |
|---|---:|---:|---|
| 13 in | 60.27 mm | 30.27 mm | conditional pass |
| 14 in | 47.57 mm | 17.57 mm | conditional pass, materially smaller margin |

Measure the actual boom OD, its station at X=430, local static/dynamic
deflection, clamp build-up and propeller runout before calling either result a
pass.  The 14-in case cannot consume this 17.6-mm screen margin to solve a
ground-clearance shortfall: raising its motor/axis does not improve this radial
boom relation, and a larger boom, blade flex or manufacturing error reduces it.

## Propulsive and aerodynamic applicability

A 13 x 10 has no-slip pitch speed 68.6 km/h at 4,500 RPM and 137.2 km/h at
9,000 RPM.  Its previously recorded 90-km/h TAS pitch-speed margin screen is
covered at 6,791--7,972 RPM.  This explains why 13 x 10 remains a coherent
*working envelope*, not why any particular motor/propeller is approved.  The
MN4014-400-class candidate requires a bench map of installed static thrust,
RPM, voltage/current/sag, torque, motor/ESC temperature and thrust versus
airspeed before takeoff or climb performance can be claimed.

The fuselage/gear contribution to CdA, pusher inflow loss and power-on tail
trim are TBD.  The existing wing polar alone cannot provide them.  Do not use
this review to revise wing incidence, washout, geometry or structural concept.

## Required gates for production fuselage CAD / ground release

1. Reconcile all ground-operation documents and generated analyses to the
   typed **2,600-g** integration mass, Ø100/75 wheels and 154.9/137/93/69-mm
   13-in table.  Landing reaction loads calculated from 2,400 g are not the
   requested mass case and must be regenerated by their owning analysis.
2. Add explicit typed inputs or a reproducible geometry calculation for every
   full-rough deduction; remove stale scalar values from master-layout text.
3. With the real wheels, legs and motor plate installed, use a guarded dummy
   13-in disk at full bilateral compression, one-main compression, 8-deg
   tail-low attitude and a measured 20-mm (or justified) rut at the prop plane.
   Demonstrate >=60 mm to every rotating-envelope extremity.
4. For a 14-in test, demonstrate its own >=60-mm result after all deductions;
   prove the actual boom, hub, plate and blade envelope simultaneously.  Do
   not use it for rough-field flight until then.
5. Measure complete gear drag/mass and all-up CG.  Confirm power-on pitch trim,
   low-speed control margin and takeoff/landing behaviour only after selected
   propulsion hardware has bench and installed validation.

**Handoff:** decision status is `preliminary_design_assumption`; datum is
`wing_root_leading_edge`; lengths are mm, mass is g.  Downstream code must use
`GroundOperationsConfig` and `PropulsionConfig` typed properties (especially
`static_propeller_axis_height_mm`, `propeller_diameter_mm`,
`main_wheel_x_mm`, `rotation_tail_down_deg`, `propeller_plane_x_mm` and
`motor_axis_z_mm`) rather than duplicating this document's arithmetic.
