# LR1600 Fuselage Prototype v1 — dry-build and bonding sequence

**Status:** prototype procedure.  Follow the generated part IDs and drawings;
stop when a datum cannot be met rather than forcing a tab, a longeron or a
boom.  The aircraft datum is wing root leading edge, +X aft, Y=0 symmetry
plane.  The wing interface plane, boom axes (Y=+/-230), motor axis and landing
contact reference are inspected assembly datums, not cosmetic shell references.

## Materials and controls

- Use the measured actual 2-mm and 3-mm birch sheets that passed the kerf/fit
  coupon.  Keep grain/orientation marking visible until the relevant proof is
  complete.
- Structural wood bonds: an aircraft-suitable epoxy selected for the actual
  material/cure environment.  Prepare charred laser edges to sound wood,
  abrade carbon, solvent-clean only with a compatible process, then de-dust.
  Record adhesive, batch, mix, cure temperature/time and retained mass.
- Use non-structural flexible adhesive only for shell, mesh, fairings and
  chafe protection; it does not replace structural epoxy in a load path.
- Carbon longerons are dry-trialled and marked before mix.  Full-area saddles,
  shaped cauls and tape/soft clamps prevent point crushing; no clamp may bend a
  longeron against its natural line.
- No printed item, shell or hatch is used as an alignment datum or temporary
  structural substitute.

## Mandatory dry assembly

1. Make the 2-mm/3-mm calibration coupons; measure actual material and
   nominal-to-finished tab/slot clearance.  Apply compensation only in the
   laser job.  Inspect all `PROTOTYPE CUTTABLE` parts and compare them to the
   cut manifest.
2. On a flat datum board establish X=0, the Y=0 centreline and the wing
   interface plane.  Install removable laser-cut locator fences/blocks.
3. Dry-fit lower keel, side members and all normal formers, then the X=-285
   `FUS-NOSE-INDEX-*`, X=+65…+200 `FUS-GEAR-*` and X=+285/+365 boom/motor
   station members. Verify no part is inverted and
   that all four longeron grooves are continuous by passing sacrificial 5 x
   3-mm stock through them.
4. Install the wing-side mating gauges; check the two interface frames are
   square to Y=0 and repeatable after removal/refit.  Do not infer wing load
   approval from this check.
5. Install the two boom alignment fixtures at X=+285 and X=+365. Establish
   Y=+/-230 at both stations, equal X station separation, and the defined
   motor axis.  Measure before every bond phase and record the values.
6. Trial the GFRP main-leg dummy/root with 3.0, 3.5 and 4.0-mm shim sets;
   verify accessible fasteners and removal path.  Trial the real nose strut
   tang in its 12-mm keyed root, with the wheel pointing straight ahead.
7. Trial the 155 x 75 x 28 dummy pack over its full X=-387.5...-332.5 useful
   range, including the `FUS-BAT-FINE-CLAMP-*` positions for exact 24% and
   25% CG. With all simulated FC/wire objects installed, disconnect it and
   lift it through the hatch/removal volume.  Check the two strap paths,
   forward/aft stops, finger/tool access and connector service loop.
8. Trial the motor-plate gauge and 13-in prop disk at the specified gear
   compression/rough-field fixtures.  The disk is tooling only.

No adhesive is mixed until these checks pass.  Record an exception and resolve
it in source CAD/configuration before cutting a replacement; do not file a
primary slot ad hoc.

## Bond order

1. Bond the central lower keel, side rails and X=-55/+65/+130 central skeleton on
   the datum board.  Use removable datum fences and verify centreline/twist
   before cure.
2. Bond the paired lower longerons continuously from the front battery/nose
   region through the wing and main-gear box.  Allow full cure in the designed
   cauls before loading the skeleton.
3. Bond the X=-285 lower-keel/nose-index structure and the `FUS-BAT-*` stop/rail
   load path.  The strut and printed fairings are not bonded in this step.
4. Bond main-gear double-shear box closure webs and the fixed spreader support
   structure.  Install only removable shims, leg and service fasteners after
   cure so a failed leg can be replaced.
5. Bond upper longerons, hatch perimeter rails and the remaining torsion/shear
   webs.  Re-check that the hatch opening stays clear and that the pack dummy
   still removes vertically.
6. Bond the X=+285/+365 boom/motor stations and the fixed motor cross-member using the boom/motor
   fixture.  Do not set boom clamp torque or bond a tube until its liner/coupon
   data exists.
7. Install serviceable servo/equipment supports, linkage guides and wire
   tie-point structure.  Verify that all screws and tensioners remain
   reachable; these items must not block pack extraction.
8. Reinspect straightness, wing-interface plane, boom symmetry, motor axis,
   gear geometry and hatch service.  Only after these checks add removable
   shell panels, skid, camera hardware and cooling guards.

## Hold points and acceptance at each irreversible step

| Hold point | Record / pass condition |
| --- | --- |
| Dry skeleton | Diagonals, Y=0 and longeron-groove continuity agree with drawing; no forced tab. |
| Lower-longeron cure | Both lines continuous, fully supported and free of visible void/peel; no high-bay butt joint. |
| Gear boxes | Main dummy and nose keyed strut install/remove without destruction; no reliance on a printed primary part. |
| Battery bay | Full dummy sweep, guarded disconnect, vertical hatch removal, strap routing and both stop paths demonstrated. |
| Boom/motor bond | Fixture record proves Y=+/-230, station separation and motor axis before cure; clamp remains `NOT RELEASED` without tube coupon. |
| Final skeleton | Wing gauges repeat; booms, motor and gear geometry meet drawing; proof articles passed or are explicitly pending. |

Expected initial failure modes are plywood bearing/splitting, unprepared
carbon-bond peel, GFRP root delamination, local boom clamp crushing and
motor-plate bolt bearing.  A crack, permanent set, delamination, bond line
opening, unexplained alignment shift or clamp slip is a stop condition.  Do
not mask it with shell, filler or a larger washer: record it and revise/prove
the underlying load path.
