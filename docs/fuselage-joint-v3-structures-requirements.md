# LR1600 Fuselage Joint & Assembly Convergence v3 — structural-joint requirements

**Status: engineering input to CAD convergence; not a cutting release.**  This
note freezes the v2 mass architecture as a 457.997-g candidate.  Added mass up
to 20 g is justified only where this note calls for an actual bearing land,
tab, doubler, retainer, or local load-transfer feature.  Kerf remains a laser
job setting; no kerf offset belongs in the nominal profiles.

The source constraints are `config/aircraft.yaml`, `docs/landing-gear.md`,
`docs/fuselage-proof-plan.md`, and the v2 gate record.  In particular, the
main box must survive one-main 121 N vertical and 35 N lateral/longitudinal
proof; the nose index must survive 60 N vertical and 35 N lateral/
longitudinal proof; P60B restraint proof is 44.4 N in each principal direction.

## Non-negotiable CAD contract

For every physical joint the model shall carry a machine-readable record with:

- a unique joint ID, each actual instance ID, one tab/key/bond-face feature ID
  on each participant, station, nominal material thickness, and insertion
  axis;
- a joint type (`through_tab`, `blind_notch`, `bonded_saddle`, `clamp`, or
  `bearing`), structural purpose, and permitted overlap/contact volume; and
- a declared dry-build step.  A part may enter only while its insertion path is
  clear of parts already installed, apart from the joint's declared contact.

At nominal geometry, a tab thickness shall equal the receiving sheet's nominal
thickness and the slot's narrow dimension shall equal that thickness.  The
laser-process clearance is applied downstream after the 2-mm/3-mm coupons are
measured.  A joint is invalid if it is metadata only, uses a generic rectangle
unrelated to a counterpart, leaves a zero-width ligament, or needs a forced
elastic deformation to assemble.

The validator shall report, per joint: feature existence; one-to-one partner;
nominal width/thickness match; placement alignment; translated insertion-path
clearance; and residual ligament.  It shall also report every primary-solid
intersection.  Only declared tab/slot material, declared bonded faces, and
declared clamp/bearing contacts are permitted; unexplained intersection volume
above 0.01 mm3 is a failure.  Generic quantity placement by an arbitrary Y
increment is prohibited: each left/right, fore/aft or stacked instance needs
its own physical placement and role.

## A. Skeleton and longerons

Use the existing station set `-285, -170, -55, +65, +130, +200, +285, +365`
mm.  Each transverse former must have real, paired features to the longitudinal
members it actually stabilises; do not cut full-width members across the
230 x 125-mm hatch opening.  A former-to-keel/side-web tab may be sacrificial
for alignment, but it cannot be credited for primary shear unless it has a
continuous surrounding ligament and bond land.

Choose one coherent assembly method: **recommended Method A** is lower
longerons on the datum jig, central formers/keels and side webs located around
them, then upper longerons installed through open aligned notches before the
hatch/closure rails close the path.  The model must prove this order.  It may
not mix a closed captive slot at one station with a slide-through procedure.

Each 5 x 3-mm carbon longeron requires a real 5-mm-wide by 3-mm-deep locating
groove/saddle or an explicitly open insertion notch, with a continuous plywood
bond face.  The lower pair remains X=-475…+365 and the upper pair
X=-170…+410.  No unsupported gap or square-ended support interruption is
allowed in the gear bay, wing-transfer bay, or motor/boom bay.  The CAD report
shall list, for each of four paths, start/end, every supporting part,
uninterrupted bond-face length, and the largest unsupported gap.  Acceptance:
no gap in those critical bays; any non-critical gap is <=10 mm and explicitly
explained.  The actual 5 x 3 solid must clear the receiving geometry except
for its declared saddle/bond contact and must pass the full declared insertion
translation.

## B. Main-gear cassette

The cassette is a closed, serviceable double-shear assembly between X=+65 and
+200, tied to both lower longerons.  It needs separately identifiable port and
starboard doublers, front and aft spreaders, upper and lower closure/load-path
webs, and two real clamp lands.  Every spreader/closure must tab into its web
or be a clearly documented bonded lap with adequate overlap; an intersecting
solid is not a joint.  The load path to show in CAD is wheel/leg root -> clamp
lands and side doublers -> front/aft spreaders and closures -> lower longerons
and adjoining shear webs.

Use an explicit *single-leg specimen* solid, with root width, clamp length and
bolt centres stated in the manifest.  The clamp pocket reference gap shall be
4.0 mm.  The only valid variant stacks are:

| GFRP specimen | Total shim in pocket | Check |
| --- | ---: | --- |
| 4.0 mm | 0.0 mm | 4.0 + 0.0 = 4.0 mm |
| 3.5 mm | 0.5 mm | 3.5 + 0.5 = 4.0 mm |
| 3.0 mm | 1.0 mm | 3.0 + 1.0 = 4.0 mm |

If shims are split across faces, their sum—not their nominal part label—must
meet the table.  A shim must never be fitted to the 4.0-mm leg or stacked such
that the assembly exceeds the pocket gap.  Generate three mutually exclusive
validation configurations; they are not simultaneously installed.

For each clamp fastener, emit the actual hole diameter, centre-to-each-free-
edge distance, net ligament in load direction, plywood thickness at the hole,
bearing-land width, washer/spreader outside diameter, and whether the leg is
between two real shear plates.  The washer envelope must remain on solid
material; it may not bridge a window, slot or thin remnant.  These values are
inputs to the proof article, not a substitute for the required 121/35/35-N
test.  Main-leg replacement acceptance: remove clamp hardware, translate the
leg along the stated axis out of the cassette, insert each specimen, and
reinstall hardware with all fuselage primary parts remaining installed.

## C. Fixed nose index

The nose module at X=-285/-170/-55 shall contain a physically modelled metal
tang envelope, a plywood index block, two actual doublers, capture bolt/pin,
clearance at the bolt head/nut, and a removal direction.  The 12-mm key is
acceptable only if a 12-mm-wide tang has two flats engaging matching plywood
index faces.  The bolt retains the strut; it is not the yaw reaction feature.

The validator shall show: tang translated through the hatch/insertion path to
the seated position; zero forbidden overlap; the two key flats bearing on the
index faces under either yaw sense; capture hardware installed after seating;
and reverse translation after hardware removal.  Report capture-hole diameter,
edge distances, local bearing land, remaining ligament and expected first
failure (key-face crush, plywood split, or bolt-bearing migration).  The proof
gate remains 60 N vertical then 35 N lateral and 35 N longitudinal.

## D. Battery bay and hatch

The 155 x 75 x 28-mm P60B dummy must be the solid used for all positions:
X=-387.5, exact 24% target, wheels-25% target, -370 nominal, and -332.5 mm.
At each position report collision-free status against every structural part;
rail support and declared stop contact are allowed contacts, not blanket
exemptions.  Include a conservative connector/service envelope and state its
dimensions and side of exit.

Forward stop, adjustable aft stop and both strap anchor paths must attach to
real rails/formers/webs through actual tabs, bolts or bonded faces.  The model
must show accessible buckle/strap routing and access to tighten/release the aft
fine clamp.  Neither hatch, pack shrink-wrap, wiring nor a printed part gets
structural credit.  The complete path for each independent stop/strap path is
required to be capable of the full 44.4-N proof reaction.

Removal must be checked as individual poses, not a union-box reservation:
installed -> connector-service displacement -> +Z 20 -> +Z 50 -> +Z 100 ->
clear of the real 230 x 125-mm hatch.  Check all five rail positions or explain
why a worst-case pair bounds the others.  Each pose must be collision-checked
against hatch rails, formers, longerons, stops, avionics reservations and the
connector envelope.  Do not suppress a member class globally; every permitted
contact must name the physical contact face.

## E. Wing transfer, motor and booms

At the present wing-interface stations, show discrete plywood frames/webs and
any necessary local 3-mm doublers transmitting fuselage-side wing reactions to
both upper and lower longerons plus adjacent side webs.  Do not create a solid
plate/box in lieu of these parts.  This CAD task does not approve the wing; its
interface remains conditional on the existing wing proof.

The motor crossmember must be an assembly of laser parts: crossmember members,
real slots/tabs into longeron-connected structure, a central cable/cooling
opening, and a removable plate with a candidate motor envelope.  Plate bolts
must be accessible and the plate must translate aft (or another explicitly
stated direction) without prop-adapter trapping.  The provisional proof screen
remains 15.1 N axial, 1.26 N m torque and 0.64 N m inertia bending; a single
thin tongue, adhesive-only feature or printed tab may not be credited for
torque.

At X=+285/+365 and Y=+/-230, boom placeholder frames must be actual placed
profiles with no collision with longerons or the motor structure.  They remain
`NOT RELEASED`; no tube/saddle clamp load or mass credit is permitted until
tube, liner, fastener and coupon evidence exists.

## Required assembly record and CAD acceptance

The CAD package shall contain a stepwise dry-build record: lower-longeron jig;
central formers/keels; side webs; upper longerons; gear cassette; battery rails
and stops; nose index; wing-transfer closure; motor structure; remaining
closures/rails.  Each entry names inserted instance(s), axis, already-installed
collision set, joint IDs, adhesive timing and an alignment measurement.

Before structural prototype cutting, pass all of the following:

1. every declared tab and slot has exactly one real counterpart; no orphan;
2. all four real carbon solids fit and are installable by the single stated
   method;
3. all three gear-leg configurations insert/remove and satisfy their stack gap;
4. the keyed nose tang inserts/removes and has geometric anti-rotation faces;
5. P60B placements and removal poses pass without unexplained collision;
6. motor plate removes and all primary contacts/overlaps are classified; and
7. contact report has zero unexplained primary overlaps above 0.01 mm3.

Only parts whose own interfaces pass may be marked `PROTOTYPE CUTTABLE`.
Passing CAD permits cutting a proof-test structural prototype, not flight use;
proof coupons and installed proof remain required.
