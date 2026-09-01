# LR1600 ground operations and structural architecture v2

**Status:** preliminary engineering screen, not production CAD, material specification,
flight release or certification. It does not change the wing. Coordinates are
root-wing-leading-edge datum in mm.

## Recommendation

Adopt removable tricycle gear: two 90-mm soft/pneumatic main wheels, one 70-mm
nose wheel, two independently replaceable GFRP/epoxy spring legs, and a sprung
nose strut with positive steering stops. Main wheel contact line: **X=120--125**
(52--57 mm aft of 25%-MAC CG X=68.52); track 330--350 mm, centres
Y=+/-165--175.

The rough-field preference is a **13-in pusher** with motor axis **Z=+50** above
the current wing datum. A 14-in prop is feasible only with 13-mm taller gear
and revised prop-to-boom proof; it is not preferred. A low Z=0 pusher with
90-mm wheels cannot satisfy the dynamic clearance requirement.

Planning allocation: **177 g wheel configuration**, **205 g ski configuration**.
The complete stronger fuselage group must be **365 g**, not the former 220-g
residual.

## Bounded loads and proof

The source-of-truth mass is 2.400 kg, so W=23.54 N. These are bounded
hardpoint screens; they are not a claim of certification or a replacement for
the existing 4-g flight design case.

| Case | Operational reaction | Proof requirement |
| --- | ---: | ---: |
| Normal 2-g landing, 90% on two mains | 21 N/main | 32 N vertical/main |
| Rough 3.5-g landing, 85% on mains | 35 N/main | 53 N vertical/main |
| One-main rut/asymmetry, full 3.5 g | 82 N | **110 N vertical at one main** |
| 20--25-mm taxi obstacle, 2.5-g one-main screen | 59 N | 88 N vertical/main |
| Nose-first landing, 3 g and 40% nose share | 28 N | **60 N vertical at nose** |
| Ground-loop/steering side load | 12 N lateral | **35 N lateral and longitudinal** |

Proof the actual wheel, axle, leg, bracket and fuselage bay in each direction,
not an isolated plywood plate. Inspect permanent set, local bearing, bond
peel/delamination, bolt slip, alignment and steering play. Expected first
failures are birch bearing/splitting, leg-root yield/delamination, axle bending,
then local carbon crushing. Foam, printed parts and hatches get no primary load
credit. [FAA AC 43.13-1B](https://www.faa.gov/documentlibrary/media/advisory_circular/ac_43.13-1b_w-chg1.pdf)
is only a general workmanship/inspection reference, not an approval basis.

## Architecture and seasonal interface

| Architecture | Result |
| --- | --- |
| Formed spring steel | Repairable/resilient but mass and root-bend fatigue govern; fallback pending supplier data. |
| 7075 plate | Reject as spring: low elastic travel and permanent-set/fatigue risk. |
| UD GFRP/epoxy spring | **Preferred:** elastic, impact-tolerant, electrically isolated, replaceable; needs laminate data and proof. |
| Carbon-only spring | Reject: brittle impact failure/poor damage visibility. |

Each main bracket is a 3-mm birch double-shear gear box with two transverse
bulkheads, a 2-mm birch shear web, and uninterrupted carbon longerons above and
below. Use a G10/aluminium load-spreader if needed, but through-bolt it into
the box; never support it on foam/single plywood. Round slots, isolate Al/CF,
and sand laser-charred structural bond faces to sound wood. Do not fix laminate
thickness or fastener geometry without material data and 110-N proof.

The same two main and one nose hardpoints serve seasons:

* Summer: 90-mm mains and a 70-mm nose wheel.
* Winter: remove wheels; pivot each ski about the retained axle with bush,
  tip-up strap/spring and positive nose-down stop. Target +20-deg tip-up and
  <=5-deg nose-down. The nose ski uses its retained nose axle/strut.
* Through-pin plus secondary clip retains all modules; printed parts are never
  primary axle, stop or latch.

| Installed group | Mass (g) |
| --- | ---: |
| Main wheels, axles/bearings | 54 |
| Nose wheel, axle/bearing | 18 |
| Main legs/brackets | 58 |
| Nose strut/fork/stops/steering | 35 |
| Pins, guards, fasteners | 12 |
| **Wheel gear** | **177** |
| Main skis | 70 |
| Nose ski | 22 |
| Ski pivots/bushes/bias/limit hardware | 29 |
| Retained legs/nose strut/fasteners | 84 |
| **Ski gear** | **205** |

Skis must be thin plywood/foam or foam-core/light-skin laminates with local
birch pivot doublers, not solid thick birch. Abrasion/mositure sealing and
snow/pivot tests are gates.

## Dynamic pusher clearance

Use the lowest rotating tip, never a static level CAD floor. Explicit proposal:
prop plane X=430, main contact X=123, tail-low rotation/touchdown=8 deg,
compression=15 mm, rut/stone=20 mm, build/wear=5 mm, retained dynamic tip
clearance=60 mm.

The aft distance is 307 mm and tail-low loss is 307 sin(8 deg)=42.7 mm.
Required static tip clearance is:

```text
60 + 42.7 + 15 + 20 + 5 = 142.7 mm.
```

The master-layout gate is:

```text
Z_axis_static - (X_prop - X_main) sin(theta) - rut - compression
    >= R_prop + C_dynamic.
```

| Configuration | Ground Z | Static | Compressed level | Compressed + 8-deg tail-low | Full rough screen |
| --- | ---: | ---: | ---: | ---: | ---: |
| 13 in, proposed | -258 | 143 mm | 128 mm | 85 mm | **60 mm** |
| 14 in, taller required gear | -271 | 143 mm | 128 mm | 85 mm | **60 mm** |
| 14 in on 13-in gear | -258 | 130 mm | 115 mm | 72 mm | **47 mm: reject** |

At motor Z=+50 and ground Z=-258, a 90-mm wheel puts the main axle at about
Z=-213; if its lower fuselage rail is Z=-55, the free leg is about 158 mm.
The 14-in version needs 171 mm. For 460-mm boom spacing/20-mm OD/30-mm radial
screen, 13 in leaves 30.3-mm prop-to-boom margin; 14 in leaves only 17.7 mm.
The 12.7-mm diameter benefit is useful but not a cure. Measure the final
tyre, spring travel, pylon and 10-deg sensitivity before accepting clearance.

## Fuselage group

| Item | Mass (g) | Function |
| --- | ---: | --- |
| Foam/laminated shell and abrasion skin | 48 | enclosure, not gear structure |
| 2-mm birch formers, keel, shear webs | 62 | shape/shear transfer |
| Carbon longerons/local wraps | 34 | bridge gear, wing, boom paths |
| 3-mm birch gear box, wing/boom/motor doublers | 72 | concentrated bearing/clamp loads |
| Battery tray, rails, hatch/latch/stops | 59 | restrained non-compressive pack |
| Servo/equipment/camera trays | 25 | serviceable central systems |
| Adhesive, inserts, fasteners, chafe, margin | 65 | real installation mass |
| **Complete group** | **365** | strong reusable fuselage |

Use 2-mm birch for webs/formers, 3-mm only for local hardpoints. The shell is
not structural landing reinforcement. Produce calibration coupons and use
measured kerf only at manufacture, never in nominal CAD.

## Forward tail actuation

Retain two independent rudder servos. Avionics selection: elevator KST X08H V5
8.0 g plus two KST X08H Plus V5 rudders 9.6 g each, all at **X=110**. This
retains independent trim/partial yaw authority without a cross-shaft.

Use three independent direct 3-mm OD/1-mm ID carbon pushrods: elevator 0.61 m,
rudders 0.65 m each; M2 ends and guides at <=200-mm unsupported spacing. Route
each branch outside battery removal volume. Guided rods beat long Bowdens for
neutral repeatability, inspection and low thermal hysteresis.

| Item | Mass (g) | Centroid X | Moment (g mm) |
| --- | ---: | ---: | ---: |
| Carbon tubes | 19.2 | 405 | 7,776 |
| Threaded ends/clevises | 8.0 | 405 | 3,240 |
| Control horns/backing plates | 7.0 | 700 | 4,900 |
| Guides/retainers/chafe sleeves | 8.0 | 410 | 3,280 |
| Central servo cradle | 7.0 | 110 | 770 |
| **Tail linkage excluding servos** | **49.2** | **406** | **19,966** |
| Three forward servos | 27.2 | 110 | 2,992 |
| **Forward tail actuation** | **76.4** | **301** | **22,958** |

The current tail-mounted three servos are 77.8 g at X=718.5: **55,893 g mm**.
The full new actuation removes **32,935 g mm** versus this exact current
servo-only baseline; with a provisional 503-g P60B pack, this equals **65.5 mm
aft battery shift** (32,935/503). Do not invent unknown old linkage credit.

At the preliminary 100-km/h aero screen, elevator/rudder hinge moments are
0.00858/0.0327 N m. With 10-mm horns, force is 0.858/3.27 N; 3x aero proof is
2.57/9.81 N. A 3/1-mm tube has I=3.93 mm4; at E=70 GPa, pin-ended 200-mm
unsupported length gives Euler Pcr=67.8 N, 6.9x rudder proof. This is a
buckling screen only: proof each installed route to 20 N in tension/compression
after cold/wet/grit exposure. Require <=0.5-deg surface free play, i.e.
<=0.10-mm combined linear play at a 12-mm horn.

## CAD gates

1. Proof complete representative gear bay to 110-N main/60-N nose vertical
   plus 35-N side/longitudinal requirements.
2. Use a dummy disk at full compression, 20-mm rut and 8-deg tail-low pitch:
   measure >=60-mm tip clearance.
3. Proof ski pivots/stops and all tail routes; measure free play.
4. Enter measured gear/fuselage/linkage masses and centroids, then re-solve
   no-ballast 25%-MAC battery location.

Detailed skin CAD is blocked until high-motor geometry, battery removal, gear
proof, real fuselage mass and CG agree.

## Traceability

* [config/aircraft.yaml](../config/aircraft.yaml) and
  [config/hardware.yaml](../config/hardware.yaml): coordinate system,
  preliminary prop/motor datum and old tail servo locations.
* [booms.md](booms.md): conditional boom and radial prop/boom screen.
* [powertrain-structure.md](powertrain-structure.md): proof/load-path practice.
* Current rebaseline aero screen: preliminary 100-km/h hinge moments above;
  bench validation is mandatory before actuation release.

