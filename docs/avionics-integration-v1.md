# LR1600 avionics, cooling and forward-controls integration v1

**Status:** preliminary packaging contract for the fuselage architecture.  It
uses the root-wing-leading-edge datum, with `+X` aft, `+Y` right and `+Z` up.
It is neither a wiring pinout nor an ArduPilot parameter file; exact FC board
revision and manufacturer documentation remain mandatory before wiring.

This document supersedes only the *physical-placement* assumptions for the
old tail-mounted Hitec servos.  The electrical direction, P60B pack study,
rail isolation and validation gates in
[electrical-rebaseline.md](electrical-rebaseline.md) remain applicable.

## Packaging stations and mass inputs

The following are centre-of-mass targets, in mm.  They are intentionally
specific enough for the next fuselage CAD study, while retaining a 10-mm
local adjustment allowance for brackets, hatches and cable exits.  No item is
credited as measured.

| Item | X | Y | Z | Mass (g) | Installation requirement |
|---|---:|---:|---:|---:|---|
| KST X08H V5 aileron servo, left/right | 135 | -450 / +450 | 0 | 8.0 each | Remains in the wing; direct short pushrod. |
| KST X08H V5 elevator servo | 110 | 0 | -15 | 8.0 | Removable central servo deck, output axis transverse. |
| KST X08H Plus V5 rudder servo, left | 110 | -32 | -15 | 9.6 | Independent output and independent pull--pull loop. |
| KST X08H Plus V5 rudder servo, right | 110 | +32 | -15 | 9.6 | Independent output and independent pull--pull loop. |
| Flight controller, isolated assembly | 125 | 0 | +15 | 30.0 | On rigid local shelf with controlled soft isolation; not on the gear plate. |
| Airspeed sensor | 150 | 0 | +15 | 4.0 | Same removable electronics shelf; pressure ports face aft/up and tubing is strain-relieved. |
| ELRS receiver | 95 | +48 | +20 | 4.6 | Serviceable side shelf; two antenna elements exit at 90 degrees. |
| SiK telemetry radio | 165 | -48 | +20 | 23.5 | Separate port-side antenna exit; regional band remains a procurement gate. |
| GNSS/compass | -105 | 0 | +95 | 9.0 | Non-ferrous upper mast or removable upper-shell pad. |
| FPV camera | -215 | 0 | +5 | 5.0 | Recessed nose cassette behind sacrificial bumper/window. |
| Optional Full-HD camera + isolated mount | -175 | 0 | +8 | 25--60 | Separate removable nose cassette; use its weighed mass in the CG ledger. |
| VTX | 250 | -48 | +20 | 8.7 | Port aft-side ventilated cassette; direct-bus filtered branch. |
| ESC (Skywalker 60A V2 envelope) | 285 | +42 | +5 | 68.0 | Starboard aft-side cooling duct, with short motor phase leads. |
| Servo DC/DC | 210 | +35 | 0 | 19.0 | Accessible power shelf; dedicated 6-V return trunk. |
| Logic 5-V DC/DC | 185 | +35 | 0 | 15.0 design estimate | Same shelf but separate clean output/return from servo rail. |
| Fuse, anti-spark/main disconnect and current sensor | 220 | 0 | 0 | 22.0 design estimate | Directly accessible after hatch opening; no discharge-path BMS. |

The five selected servos total **43.2 g** at `Xcg = 119.3 mm`, `Ycg = 0`,
`Zcg = -9.4 mm`.  This replaces the old 121.6-g Hitec five-servo set and its
tail locations; the old components/locations must not remain in any mass
ledger.

The first P60B pack must be entered as its weighed complete value; the current
study input is **503 g**, protected block **70.2 x 64.7 x 43.1 mm**, cell axes
along X.  Its rail position is deliberately owned by the CG closure, not by
the avionics layout.  Reserve a protected cable exit at the aft, lower-right
corner of the moving tray so that all pack positions leave at least 20 mm to
the tray/hatch edge and cannot pull on the connector.

## Forward-tail actuation

All three tail servos sit on a removable 2-mm birch-plywood servo deck carried
between structural fuselage frames; the deck itself is secondary and the
frames/longerons are primary.  Elevator and rudder outputs remain separate in
both mechanics and FC output assignment.  A removed hatch must expose servo
horn screws, output connectors, tensioners and the first guide without
removing the wing or battery.

| Route | Preliminary architecture | Length / supports | Mass allocation and mass centroid |
|---|---|---|---|
| Elevator | 3.0 x 1.0-mm carbon tube, M2 threaded end fittings, horn ball links; no flexible Bowden as the primary compression member. | Nominal centreline length 610 mm from `X=110` to tail; guide at <=150-mm unsupported spacing, with one axial-expansion/slip allowance at the aft guide. | 12 g at `X=415 mm`, including tube, end fittings, guides and horn hardware. |
| Left rudder | Own 0.45-mm 7x7 stainless closed-loop pull--pull cable, PTFE-lined fuselage transition and non-compressive boom guide clips. | About 720-mm one-way route (servo to boom transition then fin), so 1.44 m cable per rudder; guides <=150 mm, bend radius >=25 mm; tensioner at accessible tail horn. | 8 g at `X=414 mm`, including cable, liners, tensioner, exits and horn hardware. |
| Right rudder | Identical but physically independent route. | Same as left; no cross-coupling or shared bellcrank. | 8 g at `X=414 mm`. |

Thus the **forward-tail mechanical linkage allocation is 28 g at `X=414.4
mm`**.  Aileron pushrods, horns and wing-local installation are a separate
**12 g at `X=135 mm`** allocation.  The complete five-surface mechanical
linkage allocation is consequently **40 g at `X=330.6 mm`**.  Servo extension
leads, receiver leads and connectors belong to the wiring allocation, not to
these figures; reserve **10 g at `X=185 mm`** for control-specific leads only
if the master wiring item has not already absorbed them.

The 3-mm tube has an approximate pinned-column Euler load of 68 N at a 200-mm
free length (using 70-GPa carbon axial modulus), but only about 30--40 N of
control compression should be credited until the actual tube, guides and horn
geometry are tested.  The <=150-mm elevator guide pitch provides a sensible
preliminary margin.  Guides must locate laterally without crushing the tube;
test for no perceptible lost motion after thermal cycling, water/dust exposure
and 1000 full-control cycles.  Cable pull--pull is selected over a long
rudder-pushrod because it remains in tension, is tolerant of the boom route,
and has externally inspectable/tensionable failure points.  Its tension and
friction must be checked at both summer and winter temperatures.

## Electrical segregation and harness contract

Functional topology is:

```text
P60B pack -> fuse -> anti-spark/main disconnect -> current sensor -> ESC -> motor
                 |-> 6-V servo DC/DC -> five servos
                 |-> isolated clean 5-V DC/DC -> FC, GNSS, RX, telemetry, airspeed
                 `-> filtered direct-6S video branch -> FPV camera, VTX
```

- Battery-to-ESC positive and negative must be paired/twisted from tray exit
  to ESC, with no separately wandering return. The reserved route is about
  **674 mm one-way**. It therefore uses **4.0-mm2 silicone copper** and a
  voltage-qualified **680--1000-uF low-ESR capacitor at the ESC input**;
  final capacitance follows the selected ESC manual and a bench ripple test.
  With 4.3 mOhm/m representative copper resistance, the 1.348-m loop screens
  at 5.8 mOhm: about 0.20 V / 7.1 W at 35 A and 0.26 V / 11.8 W at 45 A.
  Measure installed resistance, connector temperature and ripple; do not
  infer a continuous-current approval from this screen.
- Keep motor phase wires <=120 mm from ESC to motor where packaging permits;
  twist the three phases.  Keep both phase and battery-current loops out of
  the GNSS mast, receiver antenna and video-signal routes.
- Run the clean 5-V output and I2C/UART loom on the upper centre/port chase;
  run servo 6-V and PWM as a paired trunk on the centre-lower chase.  The FC
  is the signal reference point: servo return current must return to the 6-V
  regulator, not through the FC's 5-V ground trace.
- Use locking connectors, chafe sleeves where a harness crosses a former, and
  a service loop only in low-current signal leads.  No high-current lead or
  antenna may be able to enter the propeller disk after a latch or tie fails.

Required geometric keep-outs, to be verified by powered testing rather than
treated as a guarantee:

| Sensitive item | Required preliminary keep-out |
|---|---|
| GNSS/compass at `(-105, 0, +95)` | At least 100 mm from motor, ESC, power leads/current sensor, VTX and ferrous landing-gear/motor/boom hardware; keep its mast and screws non-ferrous. |
| ELRS diversity antenna elements | Two 65-mm active elements at 90 degrees, with >=80 mm from VTX antenna and >=50 mm from high-current or motor phase wires.  Keep both outside carbon shielding where possible. |
| VTX antenna | Port aft-side exit, clear of propeller disk and >=100 mm from ELRS active elements; use 400 mW or less until the installed legal/RF/thermal check passes. |
| Airspeed tubing | One continuous supported run from probe to sensor; no radius <20 mm, no pinch under hatch, and no low-point water trap.  Leak-test after every wing/fuselage service event. |

Neither the H743-WING V3 PWM mapping nor the UART/I2C labels in legacy
documents are a permission to wire by assumption.  Before wiring, capture
the exact board revision/manual, then make a pin/resource record for the five
PWM outputs, CRSF, GNSS, telemetry, airspeed, current/voltage sensing,
battery monitor scaling, and all RC/GPS/airspeed/low-energy failsafe actions.

## Deliberate cooling architecture

The proposed openings are side-mounted above the wheel-spray and grass line;
they are not belly scoops.  Each has an internal 45-degree water/drip baffle
and 1.5--2-mm removable plastic mesh only where tests show that mesh pressure
loss does not compromise component temperatures.

| Circuit | Inlet | Outlet | Requirement |
|---|---|---|---|
| ESC / motor | Starboard side at `X=235..263`, `Z=+12..+32`; clear area >=330 mm2. | Starboard/aft at `X=315..345`, `Z=+18..+45`; clear area >=450 mm2. | A sealed local duct forces flow over the ESC heat spreader and then vents beside, not into, the motor mount.  Motor receives external propwash; its mount remains open for inspection. |
| VTX / video | Port side at `X=205..225`, `Z=+20..+35`; clear area >=180 mm2. | Port/aft at `X=270..295`, `Z=+22..+45`; clear area >=250 mm2. | Keep VTX in a removable metal-free cassette, thermally coupled to a small external plate if needed. |
| Battery / regulator | High, baffled forward-side inlet at `X=-445..-415`, clear area >=220 mm2. | Upper-side outlet immediately aft of tray at `X=-245..-225`, clear area >=300 mm2. | Flow crosses the protected pack/tray without direct dust blast. Do not use the battery bay as the ESC exhaust path. |

The outlet areas exceed inlet areas to tolerate duct and mesh losses.  Exact
temperatures, not opening area alone, decide acceptance: record ESC, motor,
pack, VTX and regulator temperatures at installed cruise, climb and short
adverse-power points.  A direct grass/water path to the battery, disconnect,
FC or VTX is unacceptable.

## Service and validation gates

The top hatch should expose battery latch/disconnect, fuse, both regulators,
FC, airspeed sensor, forward servos and their linkage exits.  A separate aft
side hatch exposes ESC/VTX and their ducts.  GNSS mast, camera cassette,
receiver/telemetry antenna bases and motor mount are individually removable;
routine service must not disturb FC orientation or battery rail indexing.

Before production fuselage CAD or flight release, pass all of the following:

1. Weigh all components and their brackets/lead extensions; replace the
   estimates above in the unified ledger and recompute all battery/CG cases.
2. Servo-load the actual elevator and each rudder linkage at 6 V, including
   hot/cold/dust/wet routing.  Demonstrate no binding, no visible backlash,
   rail >=5.7 V at the furthest servo, no regulator limiting and no FC reset.
3. Bench-map the installed motor/13x10 propeller, measured power leads,
   input capacitor and ducting. Confirm the Skywalker 60A V2 installation
   stays inside its documented current/thermal limits with margin; do not
   substitute a lower-current ESC without a new thermal and ripple assessment.
4. Conduct powered compass interference, GNSS lock, ELRS range, telemetry
   and video coexistence checks with motor running, VTX powered, all landing
   gear installed and servos exercised.  Change the placement or select a
   compass-less GNSS variant if the survey fails.
5. Leak-test the airspeed route and bench-validate documented ArduPilot
   response to loss of RC, GPS, airspeed and usable battery energy before any
   maiden parameter changes.
