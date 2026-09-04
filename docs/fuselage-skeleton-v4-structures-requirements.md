# LR1600 Fuselage Skeleton & Longeron Convergence v4 — structural contract

**Scope:** dry-fit CAD gate for the plywood/carbon basic skeleton only. This is not a release of the complete fuselage, gear, battery installation, motor installation, or boom clamps. It retains the v3 mass topology and the station set in `config/aircraft.yaml`; it does not give credit to the foam shell, tooling, or any later subsystem.

The active assembly is the two lower keel/shear webs, two side shear webs, eight transverse formers at X = -285, -170, -55, +65, +130, +200, +285 and +365 mm, any hatch rail strictly needed to avoid an open skeleton, and four actual 5 x 3-mm carbon longerons. Every listed plywood body shall be a placed extrusion of the exact kerf-free profile exported to DXF. A CAD construction box, a face-only placeholder, or a generic mate record cannot satisfy this contract.

## Datum and stock convention

Aircraft coordinates are X aft, Y starboard, Z up. The current 5 x 3-mm stock orientation is fixed for this pass:

| Stock dimension | Aircraft direction | Nominal extent |
| --- | --- | ---: |
| length | X | lower: -475…+365; upper: -170…+410 mm |
| 5-mm face | Y | 5.0 mm |
| 3-mm face | Z | 3.0 mm |

Thus a longeron feature may not silently rotate the stock to 3 mm in Y and 5 mm in Z. CAD shall expose the final solid cross-section at every support. Nominal saddle/slot sizes equal nominal stock and sheet thickness; laser-fit clearance is established only by the existing material/kerf coupon at CAM.

## Required Method-A build sequence

The following is the only accepted sequence for this subsystem. The CAD validator must test the stated translation for each moving instance against the already-installed active solids at a sufficient set of intermediate poses. The final pose may contact only the feature-specific contacts named in its joint records.

| Step | Moving instances | Nominal insertion | Required final condition |
| --- | --- | --- | --- |
| A1 | `FUS-LONGERON-LOWER-L/R` | locate on datum jig; no skeleton present | Straight, continuous lower stock at final Y/Z datum. |
| A2 | each transverse former | descend in -Z onto/open around lower stock | Each lower notch admits its already-installed rail without forcing it; former remains removable before web closure. |
| A3 | `FUS-KEEL-L/R` | continuous +X threading from forward of their final X start | Each web passes every intended former feature without cutting through, bending, or moving a former. |
| A4 | `FUS-SIDE-L/R` | continuous +X threading from forward of their final X start | Each side web passes only its intended former features; the upper route remains unclosed. |
| A5 | `FUS-LONGERON-UPPER-L/R` | continuous +X translation from forward of X=-170 | Each rail traverses every aligned, top-open frame notch and reaches X=+410 as one uncut length. |
| A6 | only necessary hatch/closure rails | declared direction after A5 | No closure traps either upper rail before its full insertion. |

Equivalent paths are permissible only if they preserve A1–A6's key facts: lower rails precede surrounding plywood; complete upper rails enter after formers/webs; no rail is inserted through a closed captive hole. A start pose shall be outside every final active primary solid by at least the moving part's full cross-section. Report the number and spacing of sampled poses and the minimum non-permitted clearance; sampled final contacts do not count as a clearance failure when the named contact is geometrically correct.

## Longeron support and bond contract

Every support is an actual cut feature on an actual placed plywood instance, with a unique ID. A valid support record has:

- longeron instance ID and actual cross-section at the support;
- plywood instance ID and feature ID;
- support type (`lower_open_notch`, `upper_open_notch`, `web_land`, or `bonded_face`), world X interval, and whether it is critical;
- the contact faces, their contact length and width, calculated nominal bond area, and a no-overlap fit result; and
- the assembly step at which it is engaged and the compatible insertion axis.

### Lower pair

Because lower longerons are installed first, transverse-former features must be **bottom-open U notches** (or an equally open edge saddle) that can be descended over the rail in A2. A closed 5 x 3-mm rectangle is forbidden. The lower keel/webs subsequently threaded in A3 shall provide continuous real bond faces/support lands along their overlap with each lower rail. The final model must not represent a rail simply intersecting the web volume: a rail surface must meet a declared, non-overlapping plywood support face.

### Upper pair

Because upper longerons enter in A5, every former they traverse must have a **top-open** 5-mm-Y by 3-mm-Z edge notch/saddle. Its open mouth must remain clear throughout the +X insertion path; no laterally offset notch, closed hole, tab, crossbar, hatch rail, or adjacent web can obstruct the swept 5 x 3-mm prism. The side web must supply a declared continuous upper-edge land and/or a declared continuous vertical bond face. The former notches locate the rail; the side web land carries the distributed web-to-longeron bond. Their geometry must touch the carbon without CSG penetration other than the feature-specific bonded-face tolerance.

For either pair, the nominal local plywood ligament from a notch root to the nearest free edge/window shall be at least one sheet thickness plus 3 mm, and shall be reported at every station. Where the former carries a high-load continuity bay (+65…+200 gear, -55…+65 wing-transfer, +285…+365 boom/motor), the corresponding notch root must retain at least 6 mm of continuous plywood in the load-carrying frame rail; a window may not terminate at that root. These are geometry/handling minima, not a substitute for proof or material allowables. A smaller ligament is a v4 skeleton blocker unless a dedicated local structural analysis and a revised prototype proof plan are supplied.

### Continuity requirements

The machine report shall sort supports by X and calculate unsupported intervals between their *contact intervals*, rather than claim a continuous land from a part name. Acceptance is:

- maximum unsupported gap <=10 mm outside critical bays;
- zero unsupported gap in X=-55…+65, +65…+200, and +285…+365 mm;
- no square-ended support/bond interruption inside a critical bay; and
- no discontinuity at a former caused by a window, slot, or different local placement.

The lower paths must be covered through X=-475…+365 and upper paths through X=-170…+410. End regions may taper only outside critical bays and must state remaining bond/contact length. No strength allowable is to be inferred until existing carbon-to-prepared-birch coupons have been tested. Expected first failures remain bond peel at an unprepared charred edge, plywood splitting at a notch root, or local carbon crush from an overly narrow caul—not global carbon tensile failure.

## Former-to-web joint contract

The active baseline contains **30** former/web through-joints if current web extents are retained:

- eight formers x two lower keel/webs = 16 joints;
- seven formers at X=-170…+365 x two side webs = 14 joints.

`FUS-FMR-X-285` has no side-web joint while present side webs start at X=-170; this absence must be explicitly recorded, not represented by an orphan feature. If CAD changes a web extent, it must update this expected joint count and explain the structural consequence.

Each of these 30 joints requires one exact instance-level record containing:

1. joint ID, tab-bearing instance/feature and slot-bearing instance/feature;
2. joint type, structural purpose, nominal web thickness and receiver-slot narrow dimension;
3. final world centreline/face coordinates and tolerance used;
4. declared insertion direction and assembly step;
5. remaining ligament on both members; and
6. exactly bounded permitted tab engagement/contact volume.

The continuous web may furnish a locally named through-tab at a station, but the CAD profile must contain distinguishable geometry for that feature; the label `perimeter-tab` alone is not sufficient. The former slot must be the specific profile cutout at the same world Y/Z location. In particular, a local 2-mm slot dimension does not establish mating until placed web and former feature centres/planes agree in world coordinates.

For a 2-mm web, the slot narrow dimension is 2.0 mm nominal. A 3-mm former may receive that same 2-mm web: former thickness is along X and does not change web/slot mating thickness. Tabs and slots are registration and shear transfer only after prepared bonded faces are present; do not credit an isolated thin tongue as a primary load path. No tab may terminate at a window corner or leave zero-width material. Every actual tab and slot participates in exactly one active joint, except a separately labelled jig-only feature; there must be zero duplicate counterparts and zero active orphan features.

## Collision and dry-assembly gate

The active-v4 collision set is restricted to placed formers, placed keel and side webs, active hatch/closure rails if any, and four carbon solids. Gear, nose, battery, wing, motor and boom items must be excluded by explicit subsystem filtering, not by whitelisting their collisions.

For each final or intermediate pose, classify contact only by a narrow feature-level permission:

- a named tab/slot engagement;
- a named carbon saddle/bond face;
- a named plywood bonded lap/butt face; or
- a named datum-jig contact during A1 only.

Whole-part-pair permissions are prohibited. All other active primary-primary intersections greater than 0.01 mm3 fail. The report must list both IDs, pose/step, intersection volume, and either contact ID or `UNEXPLAINED`. Acceptance total is **zero** `UNEXPLAINED` intersections. Face contact with zero volume is acceptable only if named in the contact record.

The results must include a machine-readable manifest and readable report with 30-joint accounting; each longeron support/bond interval and gap; all six Method-A paths; and collision classifications. It shall also export diagnostic views of full skeleton, one lower notch, one upper notch, one former/web joint, and any failed collision.

## Prototype-cuttable rule for v4

A skeleton part may be labelled **`PROTOTYPE CUTTABLE — SKELETON SUBSYSTEM ONLY`** only when its own profile/STEP identity, placed feature mates, ligaments, insertion path, and active collision checks pass. This grants only a first dry-fit/proof skeleton article. It does not release complete fuselage or change authoritative 398-g aircraft ledger.

Before adhesive is mixed, retain existing kerf calibration coupon and pass sacrificial 5 x 3-mm stock through all four real routes. Remove laser char to sound birch on every structural bond face, abrade/de-dust carbon, and record actual adhesive/cure procedure. Failed fit is corrected in CAM kerf settings or nominal source geometry as appropriate; it is never corrected by filing an untracked primary feature.
