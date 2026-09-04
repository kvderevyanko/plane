# LR1600 fuselage prototype v1: avionics and service contract

**Status:** prototype-integration requirement. This document assigns
installation requirements to the fuselage CAD; it does not select an FC
revision, a connector family, an ArduPilot pinout, or flight parameters. All
coordinates use the root-wing-leading-edge datum, in mm, with `+X` aft,
`+Y` right and `+Z` up. Primary CAD must retain the primary/secondary
classification stated here: an equipment tray, printed guide, camera cassette,
duct, mesh and hatch lid are **SECONDARY STRUCTURE**. They must not close a
wing, boom, motor, battery or landing-gear load path.

The physical component-envelope source is `config/aircraft.yaml`; the
commercial hardware/mass ledger is `config/hardware.yaml`. This document must
not become a second editable coordinate or mass source. The P60B prototype
pack contract is 503 g and 155 x 75 x 28 mm. Historical 70.2 x 64.7 x
43.1-mm cell-block figures are comparison-study values, not valid battery-tray
or removal geometry.

## Required removable modules and service faces

| Module | CAD provision | Service acceptance for prototype |
|---|---|---|
| P60B tray and dummy | Primary tray, stops, rails and restraint interfaces; dummy is **JIG / TOOLING**. | With wing installed, make the system safe, disconnect, release retention and lift the dummy vertically without contact with an FC, servo horn, wiring or a structural member. The CAD check shall retain the whole `155 x 75 x 28` pack swept volume plus the actual cable sweep—not a centreline only. |
| Central electronics shelf | Removable **SECONDARY STRUCTURE** shelf between primary frames; four-screw or equivalent repeatable mount. | FC, airspeed sensor and output connectors can be removed without wing removal and without changing the FC orientation datum. FC is not mounted on a gear plate or a flexible shell. |
| Tail servo deck | 2-mm-birch removable **SECONDARY STRUCTURE** deck carried by primary frames. | Elevator and both rudder servos at the typed `X=110` stations have screw, horn, connector and first-guide access from the upper service opening. Replacing one servo cannot disturb either other rudder loop. |
| ESC / VTX cassettes | Separate ventilated **SECONDARY STRUCTURE** side cassettes. | ESC or VTX is removable from its own side opening; the operation does not require removing the battery rail, FC shelf or motor base. |
| FPV and HD cassettes | Break-away printed or light-composite **FAIRING / NON-STRUCTURAL** modules. | FPV camera at its typed nose zone is replaceable from the front/bottom service face. The optional HD cassette has a separate real attachment and must not share an FPV retention screw or become an impact load path. |
| GNSS, antennas and Pitot | Non-ferrous upper pad/mast plus replaceable guides. | GNSS pad, receiver/telemetry antenna bases and Pitot tube can be inspected/replaced without opening a high-current cable clamp. |

The battery proof must use the real 503-g inert dummy, with its intended
connector and lead surrogate. A hatch projection that fits the bare block is
not a removal pass. The check has three positions: rail forward limit, exact
25%-MAC index and rail aft limit. Record the rail positions from the typed
prototype source after its requested forward extension is implemented.

### Battery cable and hatch clearance resolution

Prototype v1 uses a **230 x 125-mm clear opening**. A centred 75-mm pack then
has 25 mm lateral projected clearance at each side, satisfying the 20-mm
cable/tray-edge allowance before rail or rim intrusions. The CAD removal
solid must still prove that this full clearance remains at the actual cable
exit; do not hide a local reduction in a printed bezel, foam shell or harness
loop. The old 230 x 110-mm reservation is superseded and must not be cited for
this prototype.

## Harness corridors and physical segregation

These corridors are allocation volumes, not primary structure and not an
authority to infer FC pins. CAD shall model every crossing through plywood as
a rounded, grommet-capable hole or an accessible edge clip; no harness may be
captured behind a bonded primary web.

| Corridor | Location / direction | Carries | Required separation and retention |
|---|---|---|---|
| High current | Starboard, lower side; pack exit to disconnect/current sensor/ESC, then motor. | Twisted paired battery leads; short twisted three-phase motor leads. | Pair positive/negative from tray to ESC; phase leads target <=120 mm. Keep outside GNSS/compass, ELRS active elements, video signal and servo signal corridors. Tie at both sides of each structural penetration; no free wire can enter the propeller disk. |
| Clean signal | Upper centre/port chase. | 5-V logic, GNSS, CRSF, telemetry, I2C/UART and Pitot-sensor lead. | No shared clamp or return with propulsion or servo-current wiring. Use service loops only on low-current leads. |
| Controls | Centre-lower chase, physically independent from both rudder cable paths. | 6-V/PWM trunk and elevator-servo lead. | Paired power/return to each load; servo return returns to the 6-V regulator, not through the FC logic ground trace. |
| RF/video | Port side, with individual antenna exits. | Filtered direct-bus video, camera lead, VTX coax, receiver and telemetry antenna supports. | VTX antenna >=100 mm from ELRS active elements; ELRS active elements >=50 mm from high-current/phase wiring and outside carbon shielding where practical. |
| Pneumatic | Upper protected centre run. | One continuous Pitot tube to the airspeed sensor. | Bend radius >=20 mm; no hatch pinch, no low-point water trap and no shared hole with high-current wiring. |

GNSS/compass remains at the typed upper-forward zone and requires at least
100 mm from motor, ESC, high-current loop/current sensor, VTX and ferrous
gear/motor/boom hardware. The non-ferrous mast and its fasteners are part of
that requirement. A powered installed compass survey, not CAD distance alone,
is the acceptance evidence.

## Cooling and contamination control

The prototype reserves three independent, baffled flow paths. Inlets are side
or upper-side openings above the wheel spray/grass line; they are not belly
scoops. Each removable 1.5--2-mm mesh screen and 45-degree drip baffle is
**SECONDARY STRUCTURE** and must be removable for cleaning.

| Circuit | Inlet / outlet reservation | CAD acceptance |
|---|---|---|
| ESC/motor | Starboard inlet `X=235..263`, `Z=+12..+32`, free area >=330 mm2; outlet `X=315..345`, `Z=+18..+45`, >=450 mm2. | Local duct forces air over the ESC heat spreader then out beside the motor interface. Motor is externally propwash-cooled. Battery bay is not the ESC exhaust. |
| VTX/video | Port inlet `X=205..225`, `Z=+20..+35`, >=180 mm2; outlet `X=270..295`, `Z=+22..+45`, >=250 mm2. | Removable metal-free VTX cassette; no sealed foam pocket. |
| Battery/regulators | High baffled forward-side inlet `X=-445..-415`, >=220 mm2; upper-side outlet aft of tray `X=-245..-225`, >=300 mm2. | Flow crosses the protected tray but has no direct dirt/water path to pack, disconnect, FC or regulator. |

Outlet free area is at least inlet free area after baffles/mesh. The final
acceptance is logged temperatures of ESC, motor, pack, VTX and regulators at
installed cruise, climb and the short adverse-power point—not the nominal
opening area.

## Controls, RF and camera details

The elevator uses the 3.0 x 1.0-mm CFRP pushrod with guides at no more than
150-mm unsupported spacing. Each guide laterally locates without clamping the
rod axially; the aft guide supplies the thermal/assembly slip allowance.
Rudder-left and rudder-right remain independent 0.45-mm closed pull--pull
loops: individual PTFE transitions, exit guides, tail tensioners and no
crossing/shared bellcrank. Minimum bend radius is 25 mm. The service opening
must expose both tensioners and each first guide, and a failed/detached loop
must not be able to foul the other loop.

The FPV camera is a protected, recessed, replaceable nose cassette. A
separate HD cassette in its reserved forward zone is optional payload only;
its 25--60-g actual installed mass must be entered in the ledger before
flight. Neither camera housing, lens window nor printed mount supports the
nose gear, skid, battery box or outer shell.

## Prototype test record required before flight configuration

1. Dummy-pack service trial and six-direction 44.4-N battery-retention proof:
   forward/aft stops, vertical restraint and lateral restraint each sustain
   the full proof load independently. Recheck all three removal positions.
2. Five-servo 6-V transient/thermal test through actual linkages. Require
   >=5.7 V at the furthest servo, no regulator limiting and no FC reset.
3. Leak-test Pitot tubing after every fuselage/wing service event; operate it
   through the full hatch/tray motion and inspect for a kink or water trap.
4. Powered compass, GNSS, ELRS, telemetry and video coexistence/range survey
   with motor running, VTX powered, servos exercised and landing gear fitted.
5. Bench-test ESC/motor/13x10 installation with the actual long power pair,
   capacitor, duct and cable clamps. Inspect ripple, heat, connector rise and
   wiring motion; validate temperatures rather than treating routing as proof.
6. Before any ArduPilot change, make a board-revision-specific pin/resource
   and failsafe record: PWM outputs, CRSF, GNSS, telemetry, airspeed,
   battery-monitor scaling, RC loss, GPS loss, airspeed loss and low-energy
   recovery behaviour. This prototype provides no approval to infer pinout or
   modify a physical flight controller.

Passing a CAD collision check means only that the reserved volumes do not
overlap. The physical tests above, actual hardware mass/CG measurement and
the independent prototype review remain release gates.
