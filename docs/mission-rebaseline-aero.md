# LR1600 — mission rebaseline: aero input v2

## Status, datum and method

**Status: preliminary engineering decision / CAD-gate input; not a flight or procurement release.**  Geometry is unchanged.  Datum is root-wing LE, +X aft; all lengths are mm, mass is g and energy is Wh.  Typed geometry in `config/aircraft.yaml` gives S=0.360 m², span=1.600 m, taper=0.800, AR=7.111, MAC=`WingConfig.mean_aerodynamic_chord_mm`=225.926 mm; preliminary 25 % MAC is x=68.52 mm.

Existing reproducible Clark-Y/XFOIL work in [aerodynamics.md](aerodynamics.md) gives a 2,400-g clean stall of 34.49 km/h and conservative installation scenario 37.55 km/h.  A 50-km/h cruise calculation below is therefore not approval to operate at 50 km/h in gusts or from rough ground.

The existing `scripts/propulsion_sizing.py` central case is used explicitly: ISA SL, 2,300--2,400 g, unmeasured full-aircraft CdA=0.012 m², eta_prop/motor/ESC=0.65/0.87/0.98, and battery-bus hotel load 15 W.  It produces 76.3/89.1/105.4/125.3/149.7 W at 50/55/60/65/70 km/h TAS for 2,300 g.  At 60 km/h, 3 m/s ROC is 232.5 W (11.1 A at 21 V); 4 m/s is 277 W (13.2 A).  The retained broad adverse screen is 505 W including hotel (24 A at 21 V), short-duration only.

The energy cases include a 90-s, 3-m/s climb increment (3.05 Wh) plus 1 Wh taxi/takeoff.  They define 60 km as **total planned still-air route**, not a one-way 60-km leg.  A one-way 60-km out-and-return requirement is TBD and cannot be inferred from this mass class.

## Practical range policy and energy decision

Recommended design intent: **80 km still-air fresh-pack capability at 60 km/h TAS**, yielding approximately 20 km (25 % route) reserve after a 60-km mission; dispatch must additionally tolerate 10 % capacity ageing.  A 5 m/s headwind gives 42 km/h groundspeed and increases 60-km transit time/energy by 43 %; 8 m/s gives 31.2 km/h and +92 %.  Thus no fixed pack makes 60 km wind-independent: wind/alternate/reserve must be a go/no-go calculation.

| Fresh usable Wh | Still-air range after climb/taxi: 50 / 60 km/h TAS | 60-km mission conclusion | Complete-pack direction and mass |
|---|---:|---|---|
| 80 (75--85 class) | 49.8 / 43.2 km | Reject. | 6S1P P50B ≈450--465 g; light but not mission-capable. |
| 95 (90--100 class) | 59.6 / 51.8 km | Reject: no usable reserve even in low-speed calm case. | 6S1P high-energy 21700 ≈450--475 g. |
| 115 (105--120 class) | 72.7 / 63.2 km | Conditional only: roughly 3 km residual at 60 km/h, eliminated by ageing/wind. | 6S2P energy 18650 ≈625--660 g if its current/sag proof passes. |
| **150 (recommended dispatch capability)** | 95.6 / 83.1 km | Fresh reserve ≈23 km at 60 km/h; after 10 % ageing still ≈75 km. | High-power 6S2P 21700 ≈925--950 g complete. |

**Decision conflict:** a practical wind-resilient 60-km mission requires about **150 Wh fresh usable**, but a conventional 6S Li-ion pack that safely supplies it adds roughly 300 g over the current 624-g P30B pack.  It cannot currently support <=2,400 g.  Servo/motor mass reduction does not change this arithmetic.  A 115--120 Wh pack supports only a deliberately calm-air mission near the low end of the operating-speed range.

## Battery propulsion screen

[Molicel P50B manufacturer data](https://www.molicel.com/cn/wp-content/uploads/4.TR%E7%B0%A1%E6%98%93%E8%A6%8F%E6%A0%BC_INR21700P50B_1.1_Product-Data-Sheet-of-INR-21700-P50B-80122.pdf): 5.0 Ah, 3.6 V, 18 Wh, 71 g maximum, DCIR 12.8 mOhm at 50 % SOC and 60-A continuous only to an 80 °C cutoff.  Complete-pack estimates include busbars/strips, insulation, balance lead, main leads, connector and fuse/disconnect allowance.

| Architecture | Nominal Wh / cells / cell mass | Complete mass | Current per cell at 60-km/h cruise / 4-m/s central climb / 505-W screen | 50 %-SOC cell sag | Disposition |
|---|---:|---:|---:|---:|---|
| Existing P30B 6S2P | 129.6 / 12 / 564 g max | 624 g | 2.5 / 6.6 / 12 A | old source 17 mOhm: 0.20 V at 12 A | Electrically robust; old 103.68 Wh usable is inadequate. |
| P50B 6S1P | 108 / 6 / 426 g max | 450--465 g | 5.0 / 13.2 / 24 A | 0.064 / 0.169 / 0.307 V per cell | Best light/high-power choice, but 80--86 Wh dispatch energy fails mission. |
| P50B 6S2P | 216 / 12 / 852 g max | 925--950 g | 2.5 / 6.6 / 12 A | half 1P sag | Electrically/thermally strong and can be dispatch-limited to 150 Wh, but breaks mass closure. |
| Energy 18650 6S2P | 151--156 / 12 / ≈576 g | 625--660 g | 2.5 / 6.6 / 12 A | TBD from selected data sheet | Only plausible 115--120 Wh mass class; reject if aged/cold curve or continuous-current rating fails 24-A screen. |

No in-line propulsion-disconnecting BMS is assumed; use a fuse/disconnect plus safe balance-charge scheme.  Weld resistance, cold/aged voltage sag and thermal rise remain mandatory pack tests.

## Motor / propeller decision

Cruise needs only 91/135 W propulsion-only at 60/70 km/h central conditions; central 60-km/h 4-m/s climb needs ≈262 W propulsion-only.  Demonstrate at least 16--17 A at 21 V with 25 % central climb margin, while retaining the 24-A broad screen pending CdA and prop-map evidence.

| Candidate | Primary evidence | Assessment | Decision |
|---|---|---|---|
| KDE4215XF-465, 195 g, 465 KV | Existing [KDE product data](https://www.kdedirect.com/products/kde4215xf-465): 62 A/1,375 W only for 180 s with cooling. | KV is suitable; 25--75 g over desired range; no 6S/APC14x10 pusher forward-flight map. | Reference/fallback, not proof of continuous installation. |
| T-Motor MN4014-400 KV, 150 g bare / 171 g with leads | [Manufacturer data](https://store.tmotor.com/product/mn4014-kv400-motor-navigator-type.html): 67 mOhm, 4--8S, 30-A max and 6S 15x5 static data. | Saves 45 g and 17,775 g mm aft moment against KDE at x=395 (28.5 mm of old 624-g battery travel).  13x10 pusher map/thermal data are absent. | **Preferred bench candidate**, not procurement release. |
| T-Motor AT3520 550 KV, 218 g | [Manufacturer data](https://uav-en.tmotor.com/2019/Motors_0226/217.html): 31 mOhm, 4--6S; shown APC13x6.5 point. | Credible source but over mass target and evidence is low-pitch. | Reject. |

Current exact provisional aero choice is **APC 13x10E two-blade pusher plus bench-qualified MN4014-400 KV**, KDE retained as fallback.  APC 13x10E is documented as a two-blade electric propeller [here](https://www.towerhobbies.com/product/electric-propeller-13-x-10e/APC13010E.html).  At 13x10, no-slip pitch-speed RPM is 5,282--7,972 rpm for 70--90 km/h.  Do not select the MN4014 until pusher-bench tests demonstrate RPM, current, thrust-versus-airspeed and installed temperatures at fresh/50 %/low SOC.

## Hinge moments and servo input

Use `H=q*S_control*cbar_control*Ch`, the standard relation also stated by [NASA CP-2279](https://ntrs.nasa.gov/api/citations/19840003961/downloads/19840003961.pdf).  Exact `Ch` is TBD: existing wing polars are not flapped-control hinge data.  This is a transparent screen: sealed plain surfaces, 20° deflection, 100 km/h TAS/ISA q=472.6 Pa, |Ch|=0.20 aileron/elevator and 0.25 each rudder.

| Surface | Area / mean movable chord | Hinge moment | 10-mm horn force | 6-V rated-servo minimum |
|---|---:|---:|---:|---:|
| Each aileron | 0.0240 m² / 48 mm | 0.0204 N m = 0.208 kgf cm | 2.04 N | 0.94 kgf cm |
| Elevator | 0.0252 m² / 36 mm | 0.00858 N m = 0.0875 kgf cm | 0.858 N | 0.39 kgf cm |
| Each rudder | 0.00798 m² / 34.7 mm | 0.0327 N m = 0.334 kgf cm | 3.27 N | 1.50 kgf cm |

Minima include 10-mm control/8-mm servo horn ratio, friction 1.2 and safety factor 3.  Qualification targets are 2.0 kgf cm (each aileron/elevator) and 2.5 kgf cm (each rudder), no slower than 0.15 s/60° at 6 V, metal gears, bearing-supported output and demonstrated centering/backlash.

Recommended allocation: three 8-g **KST X08H** (two ailerons/elevator; official 6-V 2.2 kgf cm, 0.15 s/60°, metal gears/coreless/2BB [data sheet](https://www.f3x.de/media/pdf/c7/c8/b8/KST-X08H-V5-Datenblatt.pdf)) plus two **Savox SH-0255MG+** (rudders; official 3.9 kgf cm, 0.13 s/60°, 15.8 g, metal gear/2BB, 1.4-A 6-V stall current [manufacturer](https://savox-servo.com/en/product/SH-0255MGplus/)).  Five servos are 55.6 g versus 121.6 g old D85MG/HS-7245MH: −66 g.  This retains two independent rudder servos.

Place tail servos at x≈110, not x≈718.5.  Servo-only aft moment drops from 77.8*718.5 to 39.6*110 = **51,543 g mm**, equivalent to 82.6 mm battery shift for the old 624-g pack (114.5 mm for 450-g 6S1P).  This excludes real central linkage mass; structures must close carbon-pushrod/Bowden/pull-pull mass, guides, stiffness and backlash.

## Rough-field 13 versus 14 in integration

This is a separate condition from the passed boom disk clearance.  With initial 65-mm dynamic tip margin, 14 in needs axis height >=177.8+65=242.8 mm above local ground at worst attitude; 13 in needs 230.1 mm (only 12.7 mm saved).  If prop x≈430, main x≈100 and tail-down rotation/touchdown is 10°, the aft pusher loses (430-100)sin10°=57 mm.  Adding 20 mm compression/rut requires about **320 mm static axis height for 14 in** or **307 mm for 13 in**.

Mandatory CAD check: `z_axis_static - (x_prop-x_main)sin(theta) - compression - rut >= R_prop + C_dynamic`.  Check level static, full compression, rotation, touchdown and one-wheel/rut.  Provisional integration choice is **13x10, study motor axis +50 mm, 80--100-mm mains and >=65-mm dynamic clearance**.  A 14-in prop is only a fallback if the real axis/gear geometry passes without a tall/heavy gear penalty.

## CAD gate

Mass reduction 2,400→2,200 g only changes central 60-km/h bus power 106.5→104.4 W and cannot make an 85-Wh pack a 150-Wh mission pack.  Before detailed fuselage CAD, make an explicit system decision: (a) accept calm-air ≈115--120 Wh/60-km conditional mission; (b) retain practical 60 km and prove a ≈150-Wh, <=2,400-g ledger; or (c) change a mission constraint by explicit engineering decision.  Bench-test the exact prop/motor/ESC/pack (SOC and temperature sweep) and obtain flapped-section or direct hinge-load data before production release.  No new typed field is introduced here; downstream code uses `WingConfig.mean_aerodynamic_chord_mm` and `config/aircraft.yaml` only.
