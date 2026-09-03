# LR1600 Landing Gear and Ski Architecture v1

**Status:** preliminary rough-field structural screen at 2,600-g MTOW, not certification or an approval of an unmeasured spring laminate. Coordinates use the wing-root-LE datum.

## Selected wheel gear

Select a removable tricycle system: two individually replaceable **GFRP/epoxy flat-spring main legs**, 105-mm soft/pneumatic mains, and a 75-mm soft/pneumatic nose wheel on a sprung steel steering strut with positive mechanical stops. GFRP is the current preferred leg: compliant, impact-tolerant, electrically isolated and replaceable. Its laminate section, fatigue behaviour and fastener detail require supplier data/coupons and proof.

Spring-steel wire is a supplier-dependent fallback but can bend at its root. 7075 plate is rejected as a spring (poor elastic-travel/fatigue margin); carbon-only spring legs are rejected for brittle impact failure/hidden damage. Printed parts are fairings, retainers or drill templates only, never axles, spring roots, steering stops or primary latches.

| Geometry | Value | Result |
|---|---:|---|
| Main contact | X=+125, Y=+/-175 | 49.7--58.7 mm aft of 24--28% MAC CG |
| Main wheel | 105-mm diameter | 2.5-mm radius gain closes rough-clearance margin without tall legs |
| Nose contact | X=-250 | 375-mm wheelbase |
| Nose wheel | 75-mm diameter | avoids digging without heavy nose box |
| Track | 350 mm | practical lateral stability |
| Gear hardpoint | Z=-60 | tied into lower longerons/closed gear box |
| Main compression screen | 18 mm | bounded installation case, not measured travel |

At Xcg=68.52 (25% MAC) nose reaction is 15.1% of W. Across 24--28% MAC it is 15.7--13.3%, leaving useful steering load without a nose-heavy grass airframe. With the current design-ledger CG height of about 260 mm above ground, the CG passes the main-contact vertical at about 10.8--12.7 deg tail-up (12.3 deg nominal); the 8-deg rotation/landing screen is inside this limit. Forward pivot about the nose wheel screens about 51 deg, although braking remains grip-limited.

## Loads and proof

At 2.600 kg, W=**25.50 N**. A 1.35 proof multiplier is applied except the deliberately rounded side/longitudinal proof. No credit is taken for foam, skin, printed parts or a second fastener after first-fastener failure.

| Case | Operational reaction | Installed-interface proof | Driver |
|---|---:|---:|---|
| Normal 2-g, 90% main share | 22.95 N/main | 31 N vertical/main | repeated spring travel |
| Rough 3.5-g, 85% main share | 37.93 N/main | 52 N vertical/main | hard grass arrival |
| One-main rut, all 3.5 g | 89.24 N | **121 N vertical one main** | gear box/leg root |
| 20--25-mm taxi obstacle, 2.5 g | 63.74 N/main | 86 N vertical/main | axle/leg impact |
| Nose-first, 3 g, 40% nose share | 30.60 N | 42 N calculated; **60 N robust proof** | nose box/fork |
| Ground-loop/side strike | 12.75 N lateral | **35 N lateral and 35 N longitudinal** | web shear/steering stop |

The 121-N one-main vertical case governs. Proof the actual leg, axle, bracket, lower longerons, upper closure web and fasteners together. Inspect for permanent set, bearing crush/splitting, bond peel/delamination, bolt slip, axle bend and alignment change. Expected first failures are leg-root delamination/yield, plywood bearing/splitting and axle bending; foam shell failure is intentionally non-critical.

Each main leg enters the 3-mm-birch double-shear box at X=+65/+130/+200. Two 2-mm side shear webs close it; uninterrupted carbon longerons run above/below. A prepared G10/aluminium spreader is allowed only through-bolted into the box and electrically isolated from carbon. The nose bearing tube is captured by a 3-mm lower-keel box spanning X=-285/-170/-55. Round slots; prove bearing/net ligaments before selecting bolt size/laminate thickness/torque.

| Summer removable group | Mass g |
|---|---:|
| Two 105-mm mains, tyres, axles/bearings | 74 |
| 75-mm nose wheel, axle/bearing | 21 |
| GFRP legs/removable brackets | 58 |
| Nose strut/fork/steering/stops | 37 |
| Pins, guards, incremental fasteners | 12 |
| **Complete wheel gear** | **202** |

The structural gear box belongs to the fuselage 398-g group; it is not duplicated in 202 g.

## 13-in pusher clearance

Preferred 13x10 radius=165.1 mm. Motor axis Z=+50, prop plane X=+430, main contact X=+125; a 105-mm main wheel gives 2.5-mm more static clearance than the former 100-mm case. Use the lowest rotating tip, not level CAD floor.

| Case | Tip clearance |
|---|---:|
| Static level | 157.4 mm |
| Both mains compressed 18 mm | 139.4 mm |
| Compressed plus 8-deg tail-low (305 sin 8 deg loss) | 96.9 mm |
| One-main compression/roll sensitivity (additional 5 mm) | 91.9 mm |
| Full rough: one-main screen + 20-mm rut/stone + 5-mm wear/build | **66.9 mm** |

This exceeds the 65-mm practical goal by about 2 mm without an excessively tall/heavy leg. The corrected 100-mm case is 64.4 mm because it must deduct one-wheel roll sensitivity as well as rut and wear; it meets the 60-mm minimum goal but misses the preferred 65-mm margin. A 90-mm main is below the minimum screen. A 14-in prop loses another 12.7 mm to about 54.2 mm and remains a secondary integration case needing new geometry and boom/prop proof.

## Winter skis

The two retained main axle/leg brackets and the nose-strut axle are the only seasonal interfaces. Each main ski pivots on the retained axle through a metal bush, has a forward tip-up strap/spring and aft positive nose-down stop. The nose ski uses the retained nose axle. Set approximately +20-deg tip-up and <=5-deg nose-down; prove compressed-ski anti-digging and prop clearance. A through-pin plus independent safety clip retains every ski.

| Winter group, same fuselage hardpoints | Mass g |
|---|---:|
| Retained legs/nose strut/fasteners | 107 |
| Two sealed foam-core/light-laminate main skis, birch pivot doublers | 76 |
| Nose ski | 25 |
| Bushes, pivots, straps/springs/stops | 30 |
| **Complete ski configuration** | **238** |

Skis are sealed foam-core/light-laminate articles, never solid thick plywood. Wet freeze/thaw, grit-pivot, retention and anti-digging tests remain release gates.

## Gates

1. Obtain laminate/fastener data and proof main box/leg to 121 N vertical plus 35 N side/longitudinal.
2. Proof nose system to 60 N vertical and 35 N side/longitudinal; inspect steering stops/cable clearance.
3. Measure loaded wheel radius/compression/prop plane; validate with dummy disk over a 20-mm obstacle.
4. Proof ski pivot/stops and verify no dig at full compression.
