# LR1600 Avionics Inventory and Electrical Layout v1

This is a category-level package and wiring architecture, not a parts list or
a pinout.  Board revision, electrical connector, protocol, RF band and
ArduPilot parameter values remain TBD until hardware selection.  Do not infer
a physical-board pinout from this document.

## Inventory and power domains

| Category | Intended rail | Average / peak estimate | Status |
|---|---|---:|---|
| Flight controller | clean 5 V | 2.0 / 3.5 W | design estimate |
| GNSS + compass | clean 5 V | 0.6 / 1.2 W | design estimate |
| RC receiver | clean 5 V | 0.35 / 0.7 W | design estimate |
| Telemetry radio | regulated radio rail | 0.7 / 1.5 W | design estimate |
| Airspeed sensor | clean 5 V | 0.2 / 0.4 W | design estimate |
| Current/voltage sensor | propulsion bus + signal | 0.1 / 0.2 W | design estimate |
| FPV camera | filtered video rail | 0.8 / 1.2 W | design estimate |
| VTX | filtered video rail | 2.0 / 5.0 W | design estimate |
| Servos, group | dedicated regulated 6 V | 3.0 / 48 W | design estimate |
| Recording/payload | accessory rail | 1.0 / 2.0 W | TBD |

Continuous aircraft hotel-load cases at the battery bus are 7 / 15 / 25 W.
The 48-W servo figure is a short-lived rail transient for regulator and wiring
sizing, not a range model value.  It must be replaced with the selected servo
count, voltage and measured stall/current characteristics.

## Preliminary physical zones

- **Battery / power zone:** battery connector, current sensor, fuse or
  protection decision, ESC and short high-current loop.  Keep the battery-to-
  ESC path short while preserving the battery as the principal movable CG mass.
- **FC zone:** near the aircraft CG, on a rigid vibration-controlled mounting;
  away from ESC switching currents and hot air.
- **GNSS/compass zone:** upper and as far as practical from motor, ESC,
  high-current leads, VTX antenna and magnetic fasteners.  Final separation
  comes from a powered compass-interference survey, not a guessed distance.
- **Receiver / telemetry zone:** forward avionics bay with intentional antenna
  separation and serviceable coax/antenna exits.  Maintain RF separation from
  VTX and propulsion leads.
- **Video zone:** camera in the nose envelope; VTX in a separately ventilated
  zone with an antenna route clear of the pusher propeller disk.  Final VTX
  power level and RF plan are TBD.
- **Pneumatic route:** place the airspeed sensor near the FC and route pitot
  tubing without kinks, compression, leaks, or a water trap.  The external
  probe location stays an airframe-integration TBD.

## Power and wiring architecture

```
6S battery -> protection / current sensor -> ESC -> pusher motor
             |
             +-> dedicated 6 V servo BEC -> servos
             +-> independent clean 5 V DC/DC -> FC, GNSS, RC, airspeed
             +-> filtered video rail -> camera, VTX
```

The drawing is a functional architecture only.  Final fuse, anti-spark,
connector, DC/DC topology, wire gauges and grounding method need the selected
hardware and measured load.  Keep the outgoing and return propulsion conductors
paired/twisted where practical, minimise loop area, and do not route them with
the compass or receiver antenna leads.  Servo returns must not impose voltage
dips on the FC rail.

## EMI, thermal and service constraints

- The ESC requires direct cooling flow and isolation of its switching loop
  from GNSS/compass, receiver and video wiring.
- The motor is an EMI source and an aft thermal source; use short motor phase
  leads and avoid placing sensitive sensors on its immediate mount structure.
- The battery must be retained without cell compression and remain removable
  before the propeller can be powered.  Its connector must be accessible and
  cables positively restrained from the pusher disk.
- VTX cooling must be maintained at its selected transmit power; do not rely
  on a closed foam bay.  Its antenna and the RC/telemetry/GNSS antennas require
  a hardware-specific RF coexistence check.
- All flight-control or failsafe parameters remain unmodified.  Before a
  bench setup, record exact FC revision, power topology, sensor buses,
  assigned outputs, RC-loss action, low-voltage behaviour and GPS/airspeed
  fallback behaviour in a separate pin/resource and failsafe record.

## Required validation before flight hardware is approved

1. Bench-load both 6-V servo and 5-V avionics rails through representative
   servo transient/load cases; measure regulator temperature and FC voltage.
2. Measure pack voltage sag, current, connector/wire temperature and ESC
   temperature at the selected propeller operating points.
3. Conduct powered compass interference and GNSS/RC/telemetry/VTX RF checks
   in the installed layout.
4. Leak-test the pitot route and validate airspeed response.
5. Document exact board pin/resource map and failsafe/recovery behaviour before
   any ArduPilot parameter change or maiden flight.
