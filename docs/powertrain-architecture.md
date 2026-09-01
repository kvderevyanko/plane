# LR1600 Powertrain Architecture, Battery & Avionics Packaging v1

`scripts/powertrain_architecture.py` is a reproducible architecture and
energy-screening model.  It writes `analysis/powertrain/summary.json` and
three inspection plots.  It does not select a motor, ESC, propeller, battery,
cell, connector, BEC or any commercial SKU.  `config/aircraft.yaml` remains
the sole editable aircraft source of truth; this document proposes only a
future typed-configuration contract after integration of the packaging study.

## Known

- Target aircraft mass is 2400 g.  The prior propulsion model has a central
  electrical propulsion reference of 135 W at 70 km/h and 197 W at 80 km/h;
  these are central CdA/efficiency cases, not measured flight powers.
- The existing requirement study uses 490 W as the adverse 4 m/s-climb
  integration screen and 670 W as a broader propulsion-only screen.  This
  study adds its nominal 15 W hotel estimate when calculating bus current.
- Twin-boom spacing is 460 mm.  The preceding clearance work admits 12--14 in
  study disks; 15 in does not fit the baseline geometry without a change.

## Design assumptions

- 4S uses 14.0 V and 6S uses 21.0 V as conservative loaded-voltage screen
  inputs.  Their fully charged voltages are 16.8 and 25.2 V.  These are not a
  pack discharge curve: selected cells must provide `V(SOC, I, T)`.
- Bus hotel low/nominal/high cases are 7 / 15 / 25 W at the battery terminals.
  They include estimated DC/DC loss, but no measured hardware consumption.
- The power lead study uses 0.5 m one way, 2 mOhm connector-pair resistance,
  copper resistivity 0.01724 ohm-mm²/m and a 2% wire-only loss target.
- Usable energy is 80% of nominal stored pack energy.  This is a reserve and
  unusable-energy study assumption, not a flight reserve policy.

## 4S versus 6S

At equal electrical power, 6S reduces current; it therefore reduces I²R lead
and connector heat, and enables the lower-KV motor region normally useful for
the existing 12--14 in pusher study.  This is not a claim that more series
cells are always better: 6S needs a 25.2-V-charged ESC and appropriate BEC/DC
converters, whereas 4S can use lower-voltage hardware.

| Case (includes 15 W nominal hotel) | Bus power | 4S current at 14.0 V | 6S current at 21.0 V |
|---|---:|---:|---:|
| 70 km/h central cruise | 150 W | 10.7 A | 7.2 A |
| 80 km/h central cruise | 212 W | 15.1 A | 10.1 A |
| 490 W climb integration screen | 505 W | 36.1 A | 24.1 A |
| 670 W broader screen | 685 W | 48.9 A | 32.6 A |

At the final broad screen, a 0.5-m one-way pair needs about 3.0 mm² copper
on 4S or 1.3 mm² on 6S to hold wire-only loss at 2%.  With a conservative
2.5-mm² study lead, losses are about 16.5 W (4S) and 7.3 W (6S), respectively;
connector-pair heat adds about 4.8 W and 2.1 W.  Harness length, temperature,
connectors and actual current must replace this screen before wire selection.

### Preliminary architecture direction

Use a **6S propulsion bus as an initial design assumption**, not a hardware
selection.  It makes the 670 W screen roughly 33 A instead of 49 A, giving a
meaningful margin in wiring, connector heating and Li-ion parallel-count
choices.  4S remains a fallback if actual motor/propeller mapping or packaging
evidence overturns this benefit.

## Propulsion motor and ESC requirements

The preferred propeller geometry and motor-map analysis remain separate from
this electrical calculation.  Electrical integration constrains their search:

- motor/propeller must demonstrate the 12--14 in clearance-compatible
  operating point, 60--90 km/h pitch-speed coverage and the propulsion study's
  actual thrust-versus-airspeed requirement;
- with a 6S bus, validate a lower-KV motor operating region rather than a
  catalogue maximum-W number; RPM, torque, shaft pattern and thermal map are
  still TBD;
- request at least 35 A measured installed continuous current capability and
  45 A short burst capability at 6S, with verified margin above 25.2 V;
- ESC cooling is a packaging requirement: it needs direct ram/ducted airflow,
  a short high-current route and a thermal demonstration at its installed
  location.  Telemetry is desirable for current, voltage, RPM/temperature if
  hardware supports it, but its protocol is TBD;
- active/freewheel control may reduce part-load ESC loss where supported; it
  is not assumed.  Prop braking must remain disabled unless its effect on a
  pusher installation, motor heating and recovery modes is tested.

Do not use an ESC BEC as the aircraft's assumed avionics supply.  Use a
dedicated 6-V servo regulator (provisionally at least 10 A continuous / 15 A
transient, pending servo count and measured stall currents) and an independent
clean regulated 5-V avionics rail.  This separates servo transients from FC,
GNSS, receiver and airspeed power.

## Hotel load and endurance sensitivity

The 7 / 15 / 25 W cases are **battery-bus continuous** design estimates.  The
servo group adds a separate provisional 48-W peak on its 6-V rail, which is a
BEC/transient test input and must not be counted as continuous endurance load
without a duty-cycle measurement.

At the central 70-km/h propulsion reference, the following are still-air
screening values, not promised endurance or range:

| Usable energy | Low 7 W: h / km | Nominal 15 W: h / km | High 25 W: h / km |
|---:|---:|---:|---:|
| 100 Wh | 0.70 / 49.2 | 0.67 / 46.6 | 0.62 / 43.7 |
| 150 Wh | 1.05 / 73.8 | 1.00 / 69.9 | 0.94 / 65.5 |
| 200 Wh | 1.41 / 98.5 | 1.33 / 93.2 | 1.25 / 87.4 |
| 250 Wh | 1.76 / 123.1 | 1.66 / 116.5 | 1.56 / 109.2 |

The generated result also includes all 60/70/80/90 km/h and low/nominal/high
combinations.  It uses `endurance = usable_Wh / (P_propulsion + P_hotel)`.
The previous propulsion model remains the authoritative place for its drag,
efficiency and headwind sensitivity assumptions.

## Li-ion versus LiPo battery direction

The study uses nominal **pack** specific-energy bands of 200--240 Wh/kg for
Li-ion and 150--190 Wh/kg for LiPo, then applies the common 80% usable-energy
assumption.  Thus a 200-Wh usable study system represents 250 Wh nominal and
roughly 1040--1250 g Li-ion or 1320--1670 g LiPo.  These are packaging/mass
study ranges, not actual pack masses.

| Usable energy | Li-ion estimated pack mass | LiPo estimated pack mass |
|---:|---:|---:|
| 100 Wh | 521--625 g | 658--833 g |
| 150 Wh | 781--938 g | 987--1250 g |
| 200 Wh | 1042--1250 g | 1316--1667 g |
| 250 Wh | 1302--1563 g | 1645--2083 g |

**Li-ion is the preliminary long-range direction**, conditional on data for
the actual cells, series/parallel grouping, low-SOC voltage sag and thermal
rise.  The 685-W broad screen is 2.3--5.8C at 250--100 Wh usable, respectively;
cell and parallel-count ratings must substantiate it.  **LiPo is the fallback**
when a suitably packaged Li-ion system cannot meet peak-current, sag or
temperature requirements.  Neither chemistry nor capacity has been selected.

## Typed source-of-truth assumptions adopted by integration

The integration has added the following preliminary assumptions to
`config/aircraft.yaml`.  They are requirements/envelopes, not selected
hardware or measured performance:

```yaml
propulsion:
  status: initial_design_assumption
  nominal_series_count: 6
  propeller: {diameter_min_mm: 330.2, diameter_max_mm: 355.6, pitch_min_mm: 228.6, pitch_max_mm: 254.0}
  motor: {kv_min_rpm_per_v: 365.0, kv_max_rpm_per_v: 570.0, continuous_current_a: 35.0, peak_current_a: 45.0}
electrical:
  propulsion_bus_nominal_voltage_v: 22.2
  propulsion_bus_loaded_min_voltage_v: 21.0
  avionics_logic_rail_v: 5.0
  servo_rail_v: 6.0
  hotel_load_low_w: 7.0
  hotel_load_nominal_w: 15.0
  hotel_load_high_w: 25.0
battery:
  chemistry_direction: li_ion_preliminary  # conditional on sag/thermal data
  usable_energy_preferred_min_wh: 100.0
  usable_energy_preferred_max_wh: 150.0
  mass_min_g: 520.0
  mass_max_g: 940.0
```

The source config separately carries a 100--150 Wh preferred packaging range
and 520--940 g conditional Li-ion mass envelope. The 100 Wh baseline maps to
521--625 g and the 150 Wh stretch case maps to 781--938 g using the explicit
80% usable fraction and 200--240 Wh/kg nominal-pack screen. That mass range
must not be treated as a procurement mass or a closed 2400-g mass budget; the
100 Wh case is the baseline and 150 Wh awaits mass/moment closure. The larger
200/250 Wh rows remain energy sensitivity cases rather than selected fuselage
requirements.

## TBD before hardware selection

- motor KV/RPM/torque map, propeller pitch/blade count and measured static and
  forward-flight thrust;
- selected cells/pack architecture, mass, dimensions, sag, thermal behaviour,
  BMS/protection, connector and charge policy;
- actual servo count, rail voltage, average/stall current, and BEC test data;
- exact FC/GNSS/RX/telemetry/VTX models, pin/resource map, radio frequencies
  and antenna geometry;
- final wiring lengths, conductor temperature rating, fuse/anti-spark choice,
  ESC/motor cooling, EMI/compass survey and installation tests;
- battery position range and resulting estimated configuration CG.

## Reproduction

```bash
./tools/cad-shell.sh scripts/powertrain_architecture.py
./tools/test.sh
```
