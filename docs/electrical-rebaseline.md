# LR1600 electrical, battery and servo rebaseline v2

> Historical comparison only. The active preliminary packaging branch is P60B
> 6S1P as defined in [`config/hardware.yaml`](../config/hardware.yaml); do not
> reuse the P30B mass or X-position in current CG work.

Status: preliminary engineering decision for the mission rebaseline; it is not
a procurement or flight release.  Coordinates use the root-wing-LE datum and
`+X` aft.  This document does not alter wing geometry or prescribe an FC
pinout.

## Decision summary

Use a **custom 6S1P Molicel INR-21700-P60B pack** (six genuine cells,
nominal 129.6 Wh) as the mass-closure baseline, with **103.7 Wh at an 80%
mission-energy limit**.  The selected P60B data sheet is 6.0 Ah / 21.6 Wh,
75 g maximum, 12.8 mOhm DCIR at 50% SOC and 60 A continuous with a 90 C cell
cutoff.  The current manufacturer product page calls the current 6-Ah family
`P60C`; procurement must match the actual cell marking, manufacturer data
sheet and authorised distributor lot rather than treating P60B and P60C as
interchangeable names.

This is the only single-parallel architecture evaluated that preserves the old
P30B pack's nominal energy while removing roughly 120 g.  It is therefore the
right *architecture* for the 2.4-kg mass objective.  It is not evidence that
the 60-km mission is closed: with the previous central 60-km/h model
(`91.5 W` propulsion + `15 W` hotel), 103.7 Wh is only 58.4 km before a
climb, reserve or ageing allowance.  The coupled aero/propeller result must
demonstrate an average battery-bus load no greater than about 85 W for a
75-km still-air capability, or the aircraft cannot claim a 60-km practical
mission with reserve at this mass.

The electrically credible fallback is the existing **P30B 6S2P**, not a
smaller P50B pack: it has the same nominal/80%-usable energy but weighs about
624 g in the established ledger.  A 6S2P P45B can supply ample energy, but is
about 885 g complete and is incompatible with the 2.4-kg aircraft objective.

For controls, retain two independent rudder servos.  Use **KST X08H V5** for
each aileron and the elevator (8.0 g, 2.2 kgf cm at 6 V), and the stronger
**KST X08H Plus V5** for each rudder (about 9.6 g, 3.9 kgf cm at 6 V).  Place
the elevator and two rudder servos at preliminary `X=110 mm`, in the central
fuselage/wing-CG bay.  This selection is conditional on the final linkage
stiffness and a measured servo-current test; KST did not publish a stall
current in the source used here.

The preferred ESC is **Hobbywing FlyFun 40A V5**, 44 g, 3--6S, 40 A
continuous/60 A peak.  It replaces the 68-g Skywalker 60A V2 only if the
selected motor--propeller installed bench map remains at or below 32 A
continuous and 40 A short peak including temperature margin.  Its BEC is not
the primary aircraft supply; the independently regulated 5-V logic and 6-V
servo rails remain mandatory.

## Mission energy definition and range gate

`Usable Wh` below means energy deliberately released from a full pack down to
the conservative operating limit.  It already reserves approximately 20% of
nominal energy for the low-SOC knee, ageing, voltage sag and go-around
judgement.  It is not a promise that every pack can deliver its nameplate
capacity at a given load.

For a mission of distance `D`, true airspeed `V`, and average battery-bus
power `Pavg`, the energy check is:

```text
E_mission = Pavg * D / V + E_takeoff_climb + E_contingency
```

The required still-air capability is deliberately higher than 60 km.  A
reasonable rebaseline is **75 km calculated still-air capability at the
planned endurance cruise**: it leaves roughly 20% distance/energy margin for
a 60-km nominal mission before considering a major headwind.  A headwind is
not a fixed "reserve percentage": at 60 km/h TAS a 5 m/s headwind changes a
60-km leg from 1.00 h to 1.43 h.  It must be flight-planned from measured
power and forecast wind, with a turn-back/divert decision before the energy
reserve is consumed.

The numerical gate for the P60B baseline is `103.7 Wh / 1.25 h = 83 W`
before separately budgeted climb energy, or about 85 W only when climb is
included in the measured mission average.  The previous 106.5-W central
screen fails this test; a lower drag/propulsion-power result must be shown,
not assumed.  At 106.5 W, the three study energy bands give:

| Usable energy band | Endurance | still-air distance at 60 km/h | 60-km mission disposition |
|---|---:|---:|---|
| 75--85 Wh | 0.70--0.80 h | 42--48 km | Insufficient |
| 90--100 Wh | 0.85--0.94 h | 51--56 km | Insufficient; no reserve |
| 105--120 Wh | 0.99--1.13 h | 59--68 km | Barely reaches 60 km at lower end; still not a practical reserve case |

These are intentionally conservative use of the existing model, not a new
range calculation.  They show why no battery is sized merely by equating 60
km to nameplate Wh.  Flight-release energy uses measured installed cruise,
climb, pack-voltage and hotel-load data plus a pack-specific degradation test.

## Cell and pack comparison

All packs are welded-cell designs.  Dimensions are protected-cell-block
envelopes before the removable tray clearance, not fuselage CAD.  Complete
mass includes cell maximum mass plus: copper/nickel busbars, fishpaper/Kapton
and heat-shrink, 7-wire balance lead, 12-AWG main leads and connector,
temperature sensor, fuse/protection allowance and strain relief.  The exact
construction allowance must be weighed on the first pack.

Load points use 21.0 V for the system screen: `5.1 A` central 60-km/h cruise,
`16.5 A` 4-m/s climb with integration margin, `24 A` adverse short screen.
The legacy 670-W propulsion screen plus hotel is `32.7 A`; it is explicitly
not permitted as sustained P60B operation until thermal proof.  Sag is a
first-order 50%-SOC cell-only calculation, before interconnect/wire/connector
loss, using `6 * I * R_pack_cell`.

| Candidate | topology, nominal / usable Wh | cell / complete mass | protected block (L x W x H, mm) | current per cell: cruise / climb / short | 50%-SOC sag: cruise / climb / short | disposition |
|---|---|---:|---|---|---|---|
| A: Molicel INR-18650-P30B | 6S2P; 129.6 / 103.7 Wh | established 624 g | 215 x 84 x 30 | 2.55 / 8.25 / 12.0 A | 0.26 / 0.84 / 1.22 V | Proven two-parallel current margin; too heavy for robust fuselage + gear closure. |
| B: Molicel INR-21700-P50B | 6S1P; 108.0 / 86.4 Wh | 426 g cells + 45 g = **471 g** | 70.2 x 64.7 x 43.1 | 5.1 / 16.5 / 24.0 A | 0.39 / 1.27 / 1.84 V | Excellent power cell, but the 86-Wh band cannot support the stated mission. |
| C: Molicel INR-21700-P60B | 6S1P; 129.6 / 103.7 Wh | 450 g cells + 53 g = **503 g** | 70.2 x 64.7 x 43.1 | 5.1 / 16.5 / 24.0 A | 0.39 / 1.27 / 1.84 V | **Preferred conditional baseline:** same energy as A, 121 g less mass. |
| C alternative: Molicel INR-21700-P45B | 6S1P; 97.2 / 77.8 Wh | 420 g cells + 45 g = **465 g** | 70.2 x 64.7 x 43.1 | 5.1 / 16.5 / 24.0 A | 0.46 / 1.49 / 2.16 V | Current capable, but energy insufficient. |
| C stretch: Molicel INR-21700-P45B | 6S2P; 194.4 / 155.5 Wh | 840 g cells + 45 g = **885 g** | 140.3 x 64.7 x 43.1 | 2.55 / 8.25 / 12.0 A | 0.23 / 0.74 / 1.08 V | Energy capable but categorically fails the mass architecture. |

### Source and safety interpretation

- The [P60B manufacturer data sheet](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P60B_80145.pdf)
  lists 6.0 Ah, 21.6 Wh, 75-g maximum mass, 12.8-mOhm DCIR and 60-A
  continuous discharge with 90 C cut-off.  Its [current product page](https://www.molicel.com/product/inr-21700-p60c/)
  lists the related P60C 6-Ah/100-A family.  That naming/availability change
  is a procurement gate, not licence to substitute a random 6-Ah 21700.
- The [P50B data sheet](https://www.molicel.com/wp-content/uploads/4.TR%E7%B0%A1%E6%98%93%E8%A6%8F_INR21700P50B_1.1_Product-Data-Sheet-of-INR-21700-P50B-80122.pdf)
  lists 5.0 Ah, 60 A continuous at 80 C, 12.8 mOhm and 71-g maximum mass.
- The [P45B data sheet](https://www.molicel.com/wp-content/uploads/INR21700P45B_1.4_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf)
  lists 4.5 Ah, 45 A continuous at 80 C, 15 mOhm and 70-g maximum mass.
- The existing P30B selection and 624-g complete-pack estimate are retained
  as the A comparison datum from `config/hardware.yaml`.  The Molicel
  [P30B safety data](https://www.molicel.com/wp-content/uploads/FSSF00062AL-Molicel-Prototype-Rechargeable-Li-ion-Cells-EMT2-ONLY-P30BP50BP22S-1.pdf)
  identifies 3.0 Ah / 10.8 Wh and 46.3 g per cell.

At normal cruise the P60B is lightly loaded.  A 16.5-A climb is a real
thermal case (about 21 W total cell resistance heat at the cited DCIR), and a
24-A screen is short-duration only (about 44 W).  Pack temperature must be
logged at 100%, 50% and chosen low-SOC limits at warm and cold ambient.  Do
not run to the manufacturer 3.0-V cutoff in normal flight; establish the
ArduPilot battery warning/return reserve from measured *loaded* per-cell
voltage and delivered Wh.  Do not charge below the manufacturer temperature
limit.  A certified balance charger, cell matching, welded coupons and a
post-weld capacity/internal-resistance check are mandatory.

Protection architecture is:

```text
pack -> serviceable fuse -> anti-spark / main disconnect -> current sensor -> ESC
     -> dedicated 6-V servo DC/DC
     -> independent clean 5-V logic DC/DC
     -> filtered direct-bus video branch
```

There is no discharge-path BMS between pack and ESC: an unvalidated BMS
disconnect is a single-point loss of propulsion.  Cell balancing/monitoring,
temperature sensing, a physical fuse and an accessible main disconnect are
required.  Size the fuse from the measured start/transient curve, not merely
the ESC label; initially screen a 40-A time-delay DC-rated fuse, then prove
that it survives the legitimate short peak and clears the selected wire fault.

## Servo loads, selection and 6-V rail

The aero hinge-moment screen at 100 km/h and 20-degree deflection gave rated
output minima at 6 V of 0.94 kgf cm aileron, 0.39 kgf cm elevator and 1.50
kgf cm per rudder after its stated horn, safety and linkage factors.  To avoid
using a calculation with uncertain coefficients as a component rating, the
qualification requirement is 2.0 kgf cm for aileron/elevator and 2.5 kgf cm
for each rudder.

| surface | selected servo | rated torque / speed at 6 V | mass | decision |
|---|---|---|---:|---|
| 2 ailerons | KST X08H V5 | 2.2 kgf cm / 0.15 s per 60 deg | 8.0 g each | Clears 2.0 requirement with modest margin; direct short wing linkage required. |
| elevator | KST X08H V5 | 2.2 kgf cm / 0.15 s per 60 deg | 8.0 g | Clears 2.0 requirement; forward servo needs a stiff, low-backlash route. |
| 2 rudders | KST X08H Plus V5 | 3.9 kgf cm / 0.15 s per 60 deg | about 9.6 g each | Clears 2.5 requirement; retain independent outputs and trims. |

The [KST X08H V5 data sheet](https://www.f3x.de/media/pdf/c7/c8/b8/KST-X08H-V5-Datenblatt.pdf)
documents its 8-g, coreless, metal-geared, dual-bearing construction and the
6-V torque/speed.  The [KST comparison table](https://www.kennedycomposites.com/servos.htm)
documents the X08H Plus V5 6-V torque/speed/mass values; supplier identity and
current KST data sheet must be checked at purchase.  The selected family is
not an untraceable MG90S derivative.

New servo mass is about **43.2 g** versus 121.6 g for the five old selected
servos: a 78.4-g reduction before linkage changes.  Current data for these
KST servos do not state locked-rotor draw.  It would be unsafe to manufacture
a BEC claim by scaling their torque.  Retain the Pololu D24V150F6 6-V
regulator (15-A thermal-dependent, 32-A instantaneous specification) and
qualify it with five actual servos, measured at a mechanically representative
stall/load.  Acceptance is no FC brownout, rail >=5.7 V at the furthest servo,
no regulator current limit, and stable regulator/lead temperatures.  Initial
bench screen: at least 10 A transient for 1 s and 5 A for 60 s; replace those
screens with observed worst-case values.

The old Hitec set had documented aggregate locked current 10.2 A; that number
must not be copied to the new servos.  The 5-V logic rail remains separated
from servo return current.  The existing Pololu D24V90F5 clean 5-V regulator
is adequate only after the actual FC/GNSS/RX/telemetry/airspeed load and VTX
power branch are measured.

## ESC and electrical placement

| ESC | 6S current / mass / size | evidence and disposition |
|---|---|---|
| **Hobbywing FlyFun 40A V5** | 40 A continuous, 60 A peak; 44 g; 47 x 28 x 14 mm | [Official manual](https://www.hobbywing.com/en/uploads/file/20221015/12f49cbe05185401b0773cfe8f019dce.pdf). Preferred after an installed motor/prop map proves <=32-A continuous, <=40-A peak and cooling. Its 8-A/20-A BEC is deliberately not the aircraft primary BEC. |
| Hobbywing Platinum 60A V4 | 60/80 A; 49 g; 48 x 30 x 15.5 mm | [Official product page](https://www.hobbywing.com/en/products/platinum-60a-v473.html). A better 60-A fallback than the old 68-g Skywalker when the bench map exceeds the 40-A selection; data/RPM logging capability is useful, but supply status must be confirmed. |
| Existing Skywalker 60A V2 | 60/80 A; 68 g; 73 x 30 x 12 mm | Current comparison baseline. Retain only if it is already owned and bench data/cooling justify its 19--24-g mass penalty. |

Place the selected ESC in a ventilated aft-side fuselage bay close enough to
the motor that phase wires are short, but not in the same field as GNSS or the
compass.  Pair/twist battery positive and negative leads; use at least the
existing 2.5-mm2 copper screen for a 0.5-m one-way power run and route it away
from receiver antennas, compass cable and video signal cable.  Keep the
current sensor in this short high-current loop.  Capacitor requirement follows
actual battery-lead length and ESC manual; do not lengthen a lead in CAD and
assume the ESC input capacitors are sufficient.

Preliminary placements, subject to master-layout packaging:

- battery: movable forward-fuselage tray, cell axes along `X`, never retained
  by crushing cells; connector and removal path accessible with prop disabled;
- FC: `X` near 110--130 mm on rigid vibration isolation, not on a landing-gear
  load plate;
- elevator and two rudder servos: `X=110 mm`; separate serviceable linkage
  exits, independent PWM outputs and no shared mechanical synchroniser;
- GNSS/compass: upper forward mast/upper shell, initially `X=-90 mm`, and at
  least the vendor 100-mm power separation.  It must also be surveyed with
  motor, ESC, VTX and steering/gear hardware energised; magnetic landing-gear
  hardware may require a non-compass GNSS variant;
- receiver: central forward side bay, diversity antennas orthogonal and clear
  of high-current conductors and VTX antenna; telemetry antenna has its own
  separated route;
- VTX: ventilated side/aft bay on its own filtered direct-bus branch, antenna
  clear of pusher disk and well separated from GNSS/RX; do not use a 1-W mode
  until legal/RF/thermal tests pass;
- airspeed sensor: close to FC on clean 5 V; use continuous, supported pitot
  tubing with no kink, pinch, leak or low-point water trap.

Before any physical wiring or ArduPilot change, record the purchased H743-WING
revision and its official manual pin/resource map.  Then document PWM outputs,
UART/I2C ownership, battery monitor calibration and RC/GPS/airspeed/low-energy
failsafe actions in a dedicated record.  No pinout is inferred here.

## Required electrical gates

1. Authenticate six P60B/P60C cells; match capacity/IR; weld and tensile-test
   coupon tabs; weigh the completed pack and repeat capacity/voltage-sag test.
2. Installed pusher bench map: current, RPM, thrust, ESC/motor/pack
   temperature at cruise, 4-m/s climb and the short adverse screen.  It must
   prove the FlyFun 40-A selection and the battery current/time limits.
3. Servo rail transient/thermal test with all five selected servos and actual
   linkage; independently load the 5-V rail.  Record voltage at FC and tail
   servos.
4. Powered compass survey and GNSS/ELRS/telemetry/VTX coexistence/range test
   with motor at representative throttle and landing gear installed.
5. Establish loaded-voltage/Wh warnings from measured pack data; validate the
   exact ArduPilot recovery behavior on the bench before configuration change
   or maiden.
