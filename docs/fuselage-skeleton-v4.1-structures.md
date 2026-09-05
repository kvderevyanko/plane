# LR1600 skeleton v4.1 — structural and manufacturing acceptance note

**Scope:** only the dry-fit basic skeleton: 12 placed birch-plywood parts and
four carbon longerons.  This note neither releases nor assigns load credit to
the gear, nose, battery bay, wing-transfer hardware, motor, booms, avionics,
foam shell, closure shell, or aircraft mass/CG ledger.  Geometry values and
pass/fail evidence come from the v4.1 generated feature, collision, assembly,
and longeron-support reports; this note is the structural interpretation of
those results.

## v4.1 structural disposition — REJECT / preserve WIP

The geometry reviewed in this pass does **not** meet the following acceptance
contract and therefore is not ready for a laser-cut dry-fit prototype.  The
finding is confined to the 12-part/four-longeron skeleton scope.

- The final feature-level CSG report has 16 forbidden former/web intersections:
  two terminal keel intersections of 9.0 mm3 each and 14 side intersections of
  2.0 or 3.0 mm3 each.  Total forbidden volume is **56.0 mm3**, not 0.
- The real sampled-pose report fails S3 (formers into lower notches): its final
  sampled pose contains 18.0 mm3 forbidden collision.  It also fails S4 (side
  webs): four intermediate poses contain 755.0 mm3 each and the final pose
  contains 38.0 mm3.  Thus a reported insertion direction is not a valid
  assembly motion.
- The lower-longeron records still state a full-length support declaratively;
  they do not yet derive a finite carbon-to-plywood face intersection, area,
  or X intervals from the placed solids.  Consequently there is no defensible
  actual lower bond area or support-gap result to report.
- The upper former in-profile capture is only 1.5 mm in the 3-mm locating
  dimension.  It cannot demonstrate a full-depth 5Y x 3Z top-open saddle, and
  no accepted positive insertion-clearance value exists.

The stock solid itself remains correctly 5Y x 3Z.  This fact does not cure the
above support and assembly defects.  The required repair is physical:
reconcile each placed former tab with the matching web cutout, redesign the
lower shelf/U-support and upper top-open saddle from the actual rail solid,
then recompute face contacts, intervals, gaps, clearances, final CSG and every
motion pose.  Do not turn any of these failures into a broad mate whitelist or
an assumed support field.

## Stock datum and physical joint model

Aircraft axes are X aft, Y starboard, Z up.  All four rails are one actual
rectangular carbon stock orientation, with length along X, **5.0 mm along Y**
(the broad bonding/contact face), and **3.0 mm along Z** (the locating depth).
The same orientation must be visible in the placed STEP solid, the cut
plywood support, face-contact calculation, and each insertion sweep.  A
centreline, a metadata support, or a silently rotated 3Y x 5Z stock is not a
structural support.

The contact classification is deliberately strict:

| Interface | Permitted final condition | Structural credit |
| --- | --- | --- |
| Former/web tab-slot | The tab occupies only the receiving cut volume; bulk CSG overlap is zero within the report tolerance. | Registration and local shear transfer after bonding; not a substitute for a plywood face load path. |
| Plywood bonded face | Coincident prepared faces, no bulk solid intersection. | Only the actual face area reported by geometry. |
| Longeron saddle/land | A finite carbon-to-plywood face contact, with a non-captive open installation path. | Only the reported finite face area.  A line/edge touch has zero credit. |
| Datum jig/tool | Temporary tooling contact only. | None in flight. |

No whole-part-pair collision exemption is acceptable.  A permitted region must
name a specific feature/joint and be bounded; any remaining active
primary-primary intersection over 0.01 mm3 is a skeleton blocker.

## Required support geometry and continuity

The lower pair is placed on the datum jig first.  Every former that then
surrounds it needs a bottom-open U-notch or equivalent open saddle: it must
locate the 5Y x 3Z stock in Y/Z without trapping it.  The lower keel/web must
then provide an actual finite, planar bond land/shelf against the broad carbon
face.  Its local locating depth must sensibly accommodate the full 3-mm Z
stock depth; the historical approximately 1.5-mm partial capture is rejected.
The final rail and supporting plywood must meet face-to-face, rather than
overlap as solids.

The upper pair is installed from +Z after the formers and longitudinal webs.
Each locating feature is a top-open saddle/notch.  The open mouth, including
its swept 5 x 3-mm envelope, must remain unobstructed by a former, web, tab or
closure rail until the rail reaches its final pose.  It has positive nominal
geometric clearance before process/kerf compensation; a zero-clearance CAD
fit is a failure even if a particular laser happens to cut clearance.

The v4.1 support report must be derived by solid/face intersection and list
for each of the four rails: supporting part and feature ID, actual X contact
interval, measured contact/bond area, and the gap to the next actual interval.
It must not infer support from a part name or a declarative `support exists`
field.  Acceptance is no unsupported interval in the future wing-transfer
(-55…+65 mm), main-gear (+65…+200 mm), or boom/motor (+285…+365 mm) regions,
and no unsupported interval greater than 10 mm elsewhere in the rail run.
The report must identify any shorter end support explicitly.

## Assembly and manufacturing judgement

The intended dry sequence is:

1. Place the two lower longerons on the datum jig.
2. Fit the lower longitudinal keel/web members around the exposed rails where
   the real open geometry permits it.
3. Fit the side longitudinal webs without closing the upper saddle mouths.
4. Drop each transverse former onto the installed longitudinal members through
   its open notches; do not make a long web pass through a chain of closed
   slots.
5. Drop the two upper longerons from above into aligned top-open saddles.
6. Fit only the required closure/hatch rails last.

This order is preferred to the rejected v4 Method A because it never relies on
longitudinal threading through a chain of exact-size closed slots.  It keeps
the lower stock as the jig datum, keeps the upper mouths free until vertical
installation, and leaves each former/web engagement accessible for inspection.
The geometry validator must nevertheless select/report the final sequence
from actual collision-free motions, rather than pass this text as metadata.

For all 16 active instances, use transformed moving solids at 0, 25, 50, 75,
and 100 percent of the declared travel (and further samples where geometry
requires them).  At each pose, check against every already-installed active
solid.  Only the named bounded feature permission is allowed; final intended
face contact is not a volume-overlap allowance.  The correct dry-fit result is
therefore a pose-by-pose CSG PASS, not a valid `insertion_axis` field.

## Release controls for the first cut article

Before cutting flight-representative material, measure actual sheet thickness
and retain the 2- and 3-mm calibration coupons.  CAD stays nominal and
kerf-free; use the measured laser setting only at CAM.  Dry pass sacrificial
5 x 3 stock through both lower and upper routes.  Do not hammer a tab or flex
a former to compensate for a failed nominal path.

Before structural adhesive is applied, sand laser char to sound birch on every
bond land; abrade, clean and de-dust carbon; use a caul that loads the finite
bond face without crushing the rail; and record adhesive, mix, cure and clamp
procedure.  The expected early failure modes are bond peel at insufficient or
unprepared area, plywood splitting at a notch root, local carbon crush under a
narrow caul, or damaged tabs from a too-tight laser fit—not a claimed carbon
tensile failure.  Existing carbon-to-birch coupon and the skeleton proof
programme remain required; geometry alone supplies no adhesive allowable.

## Structural acceptance statement

The subsystem can be called **ready for a laser-cut dry-fit prototype only**
when the generated v4.1 evidence records all of the following:

- exactly 30 shared-definition former/web joints, no orphan tab or slot, and
  zero forbidden final former/web volume overlap;
- no whole-part collision whitelist; zero unexplained active primary
  intersections above 0.01 mm3;
- finite, actual lower-longeron bond faces and full-depth locating geometry;
- top-open upper saddles with a positive reported insertion clearance for both
  upper rails;
- actual contact intervals/areas and support gaps satisfying the critical-bay
  requirements above; and
- CSG pose-by-pose PASS for all 12 plywood instances and all four rails.

If any of those records fails, the appropriate status is preserved WIP,
**not** prototype-cuttable.  No mass optimisation is authorised in this pass:
the end-of-pass mass report is diagnostic plywood geometry mass, carbon mass,
and actual plywood-to-carbon face area only; adhesive mass is not to be
estimated from the retired guessed formula.
