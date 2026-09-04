# LR1600 Fuselage Prototype v1 — manufacturing definition

**Status:** `PROTOTYPE CUTTABLE` only where the generated `cad/fuselage_prototype`
manifest says so.  This is a structural prototype, not a production release or
a substitute for the proof programme in [fuselage-proof-plan.md](fuselage-proof-plan.md).
All dimensions are nominal mm in the wing-root-LE aircraft datum.  The CAD and
its typed `fuselage_prototype` configuration are the sole geometry source;
this document records function, material and process requirements and does
not override CAD dimensions.

## Structural classification and load paths

| Group | Classification | Function / load path | Material rule |
| --- | --- | --- | --- |
| Normal station formers, partial nose U-webs, side shear webs, lower keel, battery rail side-members, hatch perimeter rails | **PRIMARY STRUCTURE** | Close the plywood/carbon semi-monocoque, stabilize longerons, transmit distributed body shear and battery loads. | 2-mm birch.
| `FUS-NOSE-INDEX-BLOCK` / `FUS-NOSE-INDEX-DOUBLER`; `FUS-GEAR-DOUBLER-*`, `FUS-GEAR-SPREADER-*`, `FUS-GEAR-CLAMP-LAND`; `FUS-BAT-*-STOP` / `FUS-BAT-STRAP-ANCHOR-*`; `FUS-MOTOR-PLATE` | **PRIMARY STRUCTURE** | Local bearing, clamp reaction, double-shear and concentrated load transfer. | 3-mm birch only; see table below.
| Four 5 x 3 carbon longerons | **PRIMARY STRUCTURE** | Continuous fuselage bending paths.  Plywood webs transfer shear between them. | Actual 5 x 3-mm stock; no centreline-only substitute.
| Motor adapter plate, metal/G10 clamp spreaders, bolts/pins, non-crushing boom liner | **PRIMARY STRUCTURE** where specified by the assembly drawing | Transfer a concentrated reaction; removable items remain replaceable. | Selected material and proof only; a printed version is forbidden as flight structure.
| Hatch lid, light shell, camera bezel, cooling duct/mesh, electronics deck, cable clips, lower skid | **SECONDARY STRUCTURE** or **FAIRING / NON-STRUCTURAL** | Enclosure, service, dirt exclusion, local support, sacrificial protection.  They receive no wing, boom, battery, motor or gear load credit. | Foam/light laminate or print as assigned in the manifest.
| Datum board, boom/tail alignment fixture, propeller disk, calibration coupon, drill guides and dummy pack | **JIG / TOOLING** | Assembly or proof only. | Never fly.

The body is not a foam monocoque.  Its primary paths are: wing interface into
the X=-55/+65 transfer stations, through the longerons and closed central
webs; one-main landing reaction through the X=+65…+200 `FUS-GEAR-*`
double-shear box into both lower longerons and the upper closure web; nose
reaction from the X=-285 index through the lower keel to the X=-55 transfer
station; battery stops and strap anchors into the lower keel and
`FUS-HATCH-RAIL-*`; boom/motor reactions through the separated
X=+285/+365 stations.  A shell, printed part, adhesive-only tube joint, single
former or hatch never closes any of these paths.

## Birch selection and exact justification

| Nominal thickness | Parts / regions | Why this thickness is justified |
| --- | --- | --- |
| 2 mm birch | ordinary formers; partial `N170` rail former; lower keel; left/right side webs; gear-box closure webs; battery cradle/side rails; hatch perimeter rings; longitudinal interlocking members | These are distributed shear, torsion-closure and shape-stabilising members.  Their job is web action and controlled tab-and-slot assembly, not isolated bolt bearing.  Laser-cut char is removed wherever they bond structurally.
| 3 mm birch | `FUS-NOSE-INDEX-BLOCK`/`FUS-NOSE-INDEX-DOUBLER`; `FUS-GEAR-DOUBLER-*`, `FUS-GEAR-SPREADER-*` and `FUS-GEAR-CLAMP-LAND`; `FUS-MOTOR-PLATE`; `FUS-BAT-FWD-STOP`, `FUS-BAT-AFT-STOP` and `FUS-BAT-STRAP-ANCHOR-*` | These parts see concentrated bearing, compression, clamp, bolt/pin or stop reaction. They spread it into 2-mm webs and the carbon longerons. They must not be replaced by printed plastic. The TBD-tube `FUS-BOOM-SADDLE-*` placeholders are 3-mm but explicitly `NOT RELEASED`.

No other primary fuselage plywood part is promoted to 3 mm merely to make the
prototype easier to handle.  The required bearing/net-section coupon and the
representative proof articles determine whether any local doubling is needed.

## Carbon longerons and bonding

Install four pultruded 5 x 3-mm carbon longerons as actual rectangular stock,
with their broad 5-mm face bonded to prepared plywood groove faces.  The CAD
defines their station-by-station location and cut lengths; the planned paths
are deliberately continuous through the wing and main-gear bay:

| Path | Nominal X run | Nominal cut length before fit allowance | Purpose |
| --- | ---: | ---: | --- |
| Lower left / lower right | -475 to +365 at Y=+/-67.5, Z=-70 | 840 mm each, cut 10 mm long for trim | Nose-keel/battery-stop to wing, main gear and boom/motor bending continuity. |
| Upper left / upper right | -170 to +410 at Y=+/-67.5, Z=+62 | 580 mm each, cut 10 mm long for trim | Close the central bending couple from battery/hatch side rails through wing, gear and boom/motor bay. |

Cut stock long, trial-fit dry, then trim only after the datum-board check; do
not introduce a butt joint in `-55 <= X <= +200`.  Any necessary scarf is
outside that high-bending bay, has an overlap of at least 50 mm, and is a
separate coupon/proof subject.  A longeron termination is a tapered plywood
load-transfer region, never a square end against a web.  Carbon bonding faces
are abraded, solvent-cleaned and de-dusted; laser-charred birch faces are
sanded to sound wood.  Clamp pressure must wet the joint without squeezing it
dry.  Isolate carbon from any aluminium spreader/plate by a non-absorbing G10,
glass or polymer barrier and prevent a galvanic water path.

## Battery bay and retention

The bay accepts the P60B dummy/pack envelope **155 x 75 x 28 mm**. Its useful
centre-X range is -387.5 to -332.5 (55 mm): this is the former 50-mm range
extended 5 mm forward, without extending the nose. `FUS-BAT-RAIL-*` provides
six coarse 11-mm indexes; paired primary `FUS-BAT-FINE-CLAMP-*` parts have
55 x 4.2-mm continuous slots, so the `FUS-BAT-AFT-STOP` can lock the exact
measured-CG position between coarse indexes. Final CG uses the measured pack
centre, not a nominal scale mark. The swept pack envelope is X=-465 to -255.
The top hatch clear opening and its CAD removal solid must
enclose that sweep plus connector/service clearance, so removal is vertically
upward after disconnect and requires no wing removal.

Retention is deliberately redundant and never uses hook-and-loop friction,
foam compression, hatch strength or the connector as a load path:

1. A 3-mm birch forward stop takes the full forward proof reaction into the
   lower keel and both lower longerons.
2. A separately attached 3-mm `FUS-BAT-AFT-STOP`, captured by both fine clamps,
   takes the full aft proof reaction at every continuous setting; it is not
   merely a rail-end screw.
3. Two independent 20-mm straps pass through 3-mm anchor plates.  Each full
   strap/anchor path is sized and proofed for the full vertical 44.4-N proof
   reaction; their two paths provide retention redundancy rather than an
   assumed half-load share.
4. 2-mm birch side rails / broad non-compressive cradle locate the pack
   laterally.  Their fastener/adhesive path returns reaction to the keel, not
   the shell.

For a 503-g dummy at the 6-g operational assumption and 1.5 proof multiplier,
the proof reaction is `0.503 * 9.80665 * 6 * 1.5 = 44.4 N` in every principal
direction.  The forward five-millimetre improvement makes the prior exact
24%-MAC battery coordinate (-384.78 mm) physically within rail travel;
post-CAD ledger recomputation remains authoritative.

## Landing gear interfaces

### Removable GFRP main legs

The selected root is a 3-mm birch **double-shear cassette** from X=+65 to
+200: `FUS-GEAR-DOUBLER-*`, `FUS-GEAR-SPREADER-*` and
`FUS-GEAR-CLAMP-LAND` close a 2-mm upper closure web and two 2-mm side shear
webs. The leg is clamped over a long, rounded root land by replaceable metal/G10 spreaders and
through-bolts; it is not retained by a plywood slot, friction alone or printed
cheeks.  The local cassette attaches to both lower longerons and the upper
closure before it meets the secondary shell.  The leg is removable outboard /
downward after the accessible fasteners are removed; replace its sacrificial
leg before disturbing the fuselage box.

The prototype cassette accepts **3.0, 3.5 and 4.0-mm** GFRP laminates. The
3.0-mm specimen fits its nominal land; paired 0.5-mm `FUS-GEAR-SHIM-3P5` or
1.0-mm `FUS-GEAR-SHIM-4P0` PETG/G10 inserts set the 3.5/4.0-mm proof fit.
These are non-primary full-contact, hard inserts trapped by the spreader, not
load-bearing printed wedges. The leg width, root clamp length, hole size/edge distance and
bolt torque are controlled by the CAD drawing and must be checked against the
actual laminate coupon before drilling a leg.  Prove the assembled cassette to
121 N vertical on one main and 35 N each lateral/longitudinal; likely first
failure is leg-root delamination or birch bearing/splitting, not the shell.

### Fixed, non-steerable nose gear

`FUS-NOSE-INDEX-BLOCK` plus the two `FUS-NOSE-INDEX-DOUBLER` parts form a
captured **12-mm keyed root** in the X=-285 3-mm lower-keel box. A mating non-printed metal
strut tang bears on the flat faces of this key; the separate capture bolt only
retains the strut. Consequently yaw torque follows `strut tang -> keyed block
and doubler -> lower-keel web -> lower keel -> lower longerons`, rather than clamp
friction.  The index has manual straight-ahead fitting reference faces, but no
yaw degree of freedom after its capture hardware is tightened.

There is no steering arm, linkage, servo, saver, cable or steering mechanism.
The fork/strut is replaceable and retains the existing 75-mm wheel axle for a
pitch-only nose ski; the root key remains engaged so yaw stays locked.  Test
the real key/root at 60 N vertical and 35 N lateral plus 35 N longitudinal,
then record residual heading and inspect key-face crush, splitting and slip.

## Boom and motor interfaces

Two primary boom stations, X=+285 and X=+365, are exactly 80 mm apart. Each
has a `FUS-BOOM-SADDLE-*` 3-mm placeholder frame, a replaceable compliant
non-conductive saddle/liner and paired captured fasteners.  The two stations
provide longitudinal position and yaw anti-rotation; neither a single bolt nor
adhesive carries primary boom load.  Tightening is controlled by measured
torque after a representative tube/liner coupon establishes the safe clamp
limit.  The clamp must retain a replaceable boom without point-load crushing.

Boom tube OD, wall, laminate and supplier allowables are still unselected in
the typed source; therefore the contact saddle and torque setting are
`NOT RELEASED` even if the fuselage-side frames are cuttable.  Build the boom
coupon before crediting coupled wing/boom bending.  Fixture both boom axes at
Y=+/-230 and the tail reference while bonding; target station coordinates are
within +/-0.5 mm and differential tail incidence is <=0.25 degrees after
proof.

The motor uses the X=+365 structural frame and fixed cross-member with a
replaceable flat plate/adapter.  The plate has two shear keys plus accessible
through-fasteners; its adapter pattern remains provisional for the selected
50-mm-class motor.  No printed plate is flight structure.  The prototype
screen remains 15.1 N axial, 1.26 N m torsion and 0.64 N m inertia bending;
replace this screen with selected-motor measured thrust/torque before release.

## Laser-cut and assembly controls

CAD is nominal: it contains **no kerf compensation**.  Before cutting parts,
measure actual thickness at multiple points and cut the 2-mm and 3-mm tab/slot
calibration coupons in the same orientation/process.  Choose downstream
LightBurn kerf/fit compensation from measured results, retain the coupon, and
do not edit CAD to compensate for one machine.  Reject parts with delamination,
excessive char in a glue land, materially undersized ligament, broken small tab
or an out-of-tolerance slot.

Use tab-and-slot only for registration.  Critical stations include asymmetric
keying so they cannot be reversed; do not hammer a fitted tab into a stressed
slot.  Internal corners receive relief only where a rectangular tab actually
bottoms; all primary bolt/pin edge distances are CAD-checked.  Dry-assemble on
the datum board before adhesive.  The datum board, boom fixture, prop disk,
dummy battery and all printed drill/alignment aids are tooling and excluded
from aircraft mass.
