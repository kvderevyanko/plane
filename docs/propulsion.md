# LR1600 Propulsion & Energy Sizing v1

`scripts/propulsion_sizing.py` is the reproducible requirement model.  It
creates `analysis/propulsion/summary.json` and optional plots; these generated
outputs are not aircraft source of truth.  No motor, ESC, propeller, battery,
cell chemistry, series count, battery capacity, range or endurance is selected
by this study.

## Known

- `config/aircraft.yaml` remains the only editable aircraft source: target
  mass 2400 g, wing area 0.360 m², span 1600 mm and `g=9.80665 m/s²`.
- Existing clean-wing analysis gives MAC about 225.93 mm, clean stall
  34.49 km/h (conservative scenario 37.55 km/h), the efficient wing-only area
  about 55--65 km/h, and the mission TAS range 60--90 km/h.
- The source polars are existing clean XFOIL results in `analysis/aero/`.
  They are used only for wing profile/induced drag.  In particular, the
  previously recorded wing-only drag near 80/90 km/h is not treated as total
  aircraft drag.
- The preliminary stability integration defines a 24--28% MAC design CG band,
  but the all-up measured CG remains unresolved. The motor, ESC and
  flight-battery ledger entries remain TBD rather than being mislabelled as
  measured masses. [Powertrain Architecture v1](powertrain-architecture.md)
  supplies the subsequent 6S, hotel-load and packaging integration.

## Derived model

At each speed and mass, required wing lift gives `CL`.  The script constructs
the existing finite-wing clean curve from the direct polar files, interpolates
profile CD only inside its supported pre-stall branch, then adds
`CDi = CL²/(pi*e*AR)`, with the existing clean-analysis value `e=0.90`.

Full-aircraft uncertainty is explicit rather than hidden in a multiplier:

`D_total = D_wing + D_parasitic`, where
`D_parasitic = 0.5 * rho * V² * CdA`.

`CdA` is an additional dimensional drag area, so it does not require inventing
a fuselage reference area.  The 0.006 / 0.012 / 0.020 m² cases mean,
respectively, a clean future integration, an integration-reference case, and a
deliberately adverse exposed/interference bound.  They exclude wing drag and
are screening assumptions, not measured LR1600 values.  Fuselage, booms, tail,
motor installation and gaps must later replace this sweep with geometry/test
evidence.

For level flight, `T_req = D_total`, `P_aero = D_total*V`; the propulsive chain
is not assumed lossless:

`P_battery,propulsion = P_shaft/(eta_prop*eta_motor*eta_ESC)`.

The model sweeps propeller 0.55/0.65/0.75, motor 0.80/0.87/0.90 and ESC
0.97/0.98/0.99, for total chain efficiency 0.427/0.554/0.668.  These are
design assumptions for screening, never measured hardware efficiencies.

Climb adds `m*g*ROC`: `P_shaft = D_total*V + m*g*ROC`, and
`T_req = D_total + m*g*ROC/V`.  The 2/3/4 m/s cases and a 60 km/h climb TAS
are study cases only.  60 km/h is about 1.60 times the current conservative
2400-g stall estimate; it is not a final climb requirement.

## Cruise requirements at 2400 g

The table is the full sensitivity envelope across CdA and efficiency cases,
with hotel load excluded; add the future measured battery-bus hotel load to
the electrical-power column.

| TAS (km/h) | Cruise thrust (N) | Electrical propulsion power (W) | Central energy-only case (N / W) |
|---:|---:|---:|---:|
| 60 | 2.0--4.4 | 50--172 | 3.04 / 91 |
| 70 | 2.5--5.7 | 72--260 | 3.85 / 135 |
| 80 | 3.1--7.3 | 103--382 | 4.91 / 197 |
| 90 | 3.8--9.2 | 143--538 | 6.13 / 276 |

The central case is only `CdA=0.012 m²` and the central efficiency tuple.  It
is included to make the sweep interpretable, not to nominate a design point.
The strong high-speed growth is chiefly parasite drag; at 90 km/h its central
wing drag is about 1.53 N and additional parasite drag about 4.59 N.

## Climb, takeoff and recovery

At the 60 km/h study speed, 2/3/4 m/s needs 4.84--7.22,
6.26--8.64 and 7.67--10.05 N dynamic thrust respectively.  The corresponding
electrical propulsion intervals are 121--282, 156--337 and 191--393 W.
These include CdA and efficiency sensitivity but exclude hotel load.  A
non-binding 25% integration power margin gives a 60-km/h, 4-m/s adverse study
screening value of about 490 W plus hotel load.

Across the whole intended level-flight range, the current sizing envelope is
50--538 W propulsion-only.  A future power train must demonstrate its actual
continuous thermal rating at the selected voltage and propeller operating
point; the central 25% margin would screen to about 673 W.  This is a
requirement envelope, not a request to select a 673 W component.

Hand launch and ground takeoff cannot share a fabricated static-thrust number.
For hand launch, demonstrate positive excess thrust at the defined release and
transition speed from a measured thrust-versus-airspeed curve.  For ground
takeoff, additionally define runway/run, wheel geometry and rolling
resistance, rotation/liftoff speed, acceleration and obstacle rule:
`T = D + m*a + W*sin(gamma) + mu_r*(W-L)`.  None is currently fixed.  The
dynamic climb figures are useful recovery/go-around requirements, not static
thrust claims.

## Battery and range study

`usable_energy_Wh` means energy deliverable at the battery terminals after the
future reserve/unusable fraction.  It is deliberately not nominal pack Wh and
does not imply chemistry, capacity, S-count or voltage sag.  With no approved
hotel inventory, the generated values set `hotel_load_battery_bus_w = null`;
the following values are therefore explicitly **propulsion-only references**
at the central CdA/efficiency case, not aircraft endurance/range promises.

| Usable energy (Wh) | 60 km/h: h / km | 70 km/h: h / km | 80 km/h: h / km | 90 km/h: h / km |
|---:|---:|---:|---:|---:|
| 100 | 1.09 / 65.6 | 0.74 / 51.8 | 0.51 / 40.6 | 0.36 / 32.6 |
| 150 | 1.64 / 98.4 | 1.11 / 77.7 | 0.76 / 61.0 | 0.54 / 48.8 |
| 200 | 2.19 / 131.2 | 1.48 / 103.5 | 1.02 / 81.3 | 0.72 / 65.1 |
| 250 | 2.73 / 164.0 | 1.85 / 129.4 | 1.27 / 101.6 | 0.90 / 81.4 |

The relation is `endurance = usable_energy/(P_ESC_input + P_hotel)` and
still-air range is `TAS*endurance`.  An illustrative 200 Wh, 70 km/h,
propulsion-only case produces 103.5 km still-air; an outbound 5/8/10/12 m/s
headwind reduces its groundspeed/range to 52/41.2/34/26.8 km/h and
76.9/60.9/50.3/39.6 km.  This applies the existing TAS-minus-headwind concept
and says nothing about return-wind or reserve policy.

The model accepts a future non-negative `hotel_load_w` in W at battery-bus
terminals.  It must already include DC/DC/BEC losses.  Later record separate
FC, GNSS/compass, receiver, telemetry, FPV/VTX, servo-average and other loads,
each with installation state, average/peak rail load, regulator efficiency and
measurement source.  Servo peak/stall is a BEC/rail sizing case, not an
endurance average without duty evidence.  Pack voltage under load,
`V_loaded_min(P, SOC, T)`, is required later to calculate current, ESC input
limits, connectors, wires, fusing and brownout/cutoff behaviour.

## Mass feedback

The model recomputes wing CL, profile and induced drag for 2200/2400/2600/2800
g; the cases represent possible airframe/battery allocation, not changed
targets.  At the same speed, added mass increases required power most at the
low-speed induced-drag end.  At 90 km/h the CdA uncertainty dominates.  No
battery mass is inferred from Wh because energy density and chemistry are TBD;
this keeps the feedback honest until a candidate energy storage system and the
mass ledger can be evaluated together.

For a numerical scale, the sensitivity envelope of electrical propulsion power
(low/high CdA-and-efficiency combinations, hotel excluded) is:

| Mass (g) | 60 km/h (W) | 70 km/h (W) | 80 km/h (W) | 90 km/h (W) |
|---:|---:|---:|---:|---:|
| 2200 | 49--169 | 71--259 | 102--381 | 143--538 |
| 2400 | 50--172 | 72--260 | 103--382 | 143--538 |
| 2600 | 52--175 | 73--261 | 103--382 | 144--539 |
| 2800 | 54--178 | 74--264 | 104--384 | 144--540 |

## Future motor and propeller requirements

Search components against the envelope, not a SKU:

- measured continuous capability covering the selected cruise operating point
  (50--538 W propulsion-only sensitivity envelope, plus measured hotel load);
- measured short-term/thermal capability for the 60-km/h 2--4 m/s climb study
  (121--393 W, or about 490 W with the optional 25% study margin, plus hotel);
- cruise thrust 2.0--9.2 N across the 60--90 km/h drag/efficiency sweep, and
  measured thrust-versus-airspeed sufficient for the selected launch concept;
- propeller efficiency preferably at least 0.65 around the 60--80 km/h
  long-range operating area; motor/ESC efficiency should be demonstrated in
  their operating regime rather than assumed from a catalogue peak;
- propeller pitch speed must cover 60--90 km/h TAS with margin.  Tip speed is
  `pi*diameter*RPM/60`; diameter and RPM must stay below the later chosen noise,
  compressibility, motor-map and clearance constraints.

For long range a two-blade propeller is normally the first aerodynamic option:
less blade profile/interference loss and lower disk loading for a given
diameter generally help cruise efficiency.  A three-blade propeller can be the
integration option when diameter/clearance or required static thrust demands
it, usually with an efficiency penalty to verify in data.  Neither blade count
nor diameter is selected.  Maximum diameter is explicitly TBD until
fuselage/boom/tail clearance is designed.

The allowable mass of the motor/ESC/propeller/battery system is also TBD: the
existing aircraft mass ledger has no resolved subsystem masses, and assigning
one now would create a fictitious CG/mass closure.  Battery placement and mass
must feed the existing CG infrastructure once those measurements exist.

## TBD before hardware selection

- final mission endurance, range, reserve and launch method;
- full-aircraft geometry and validated CdA; propeller clearance;
- measured motor/propeller maps, thermal continuous/peak limits and noise;
- battery chemistry, voltage/S count, usable energy, mass, temperature and
  loaded-voltage/discharge curve;
- hotel-load inventory/duty cycle and all avionics/servo rail and peak data;
- final battery/ESC/motor placement, mass ledger and CG; and
- ESC/BEC, current, wire, connector, fuse and EMI architecture verification.

## Reproduction and checks

```bash
./tools/cad-shell.sh scripts/propulsion_sizing.py
./tools/test.sh
./tools/build.sh
```

The script also writes four inspection plots under `analysis/propulsion/plots/`:
cruise power, endurance/range, mass feedback and headwind sensitivity.  They
are generated visualisations, not source inputs.
