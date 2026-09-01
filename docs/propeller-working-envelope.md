# LR1600 propeller working envelope v1

This is a preliminary aerodynamic and kinematic requirement study.  It does
not select a commercial propeller, motor, battery, ESC or blade count.  The
reproducible calculation is `scripts/propeller_envelope.py`; its generated
output is `analysis/powertrain/propeller_envelope.json`.

## Known inputs

- The aircraft source of truth is `config/aircraft.yaml`: target mass is
  2400 g; boom axes are Y = +/-230 mm and Z = 0 in the root-wing-LE datum.
- The previous 3-D radial clearance screen uses Ø20 mm booms and 30 mm
  manufacturing/deflection clearance.  At 460 mm center spacing, study disks
  through 14 inch clear; 15 inch does not.
- `scripts/propulsion_sizing.py` supplies aircraft thrust demand from the
  existing wing polar plus an explicit full-aircraft CdA sweep.  It is not a
  propeller map.  Across 60--90 km/h its level-flight requirement is about
  2.0--9.2 N, and the 60 km/h / 4 m/s high-CdA climb study is about 10.1 N.

## Method and assumptions

Pitch speed is the no-slip geometric relation
`V_pitch = pitch * RPM`; it must exceed 90 km/h TAS to retain useful advance
margin, but it is not an assertion of actual flight speed or thrust.  The
screen therefore asks for a 103.5--121.5 km/h geometric pitch speed (15--35%
above 90 km/h).  Rotational tip speed is `pi * D * RPM / 60`; the listed study
points remain about Mach 0.36--0.47 at ISA speed of sound.  Noise, helical tip
Mach, blade section and acoustic limits are still TBD.

Disk loading is only `T_required / disk_area`: it shows why a larger propeller
is aerodynamically attractive at the same aircraft requirement, but makes no
induced-loss or static-thrust prediction.  The radial clearance calculation is
`sqrt(Y_boom^2 + Z_boom^2) - (R_prop + R_boom + clearance)`.

## Working envelope

| Study diameter | RPM screen | Pitch study (in) | Tip speed (m/s) | 60--90 km/h required-thrust disk loading (N/m²) | Clearance screen |
|---:|---:|---:|---:|---:|---|
| 12 in | 8,500--10,000 | 7 / 8 / 9 | 136--160 | 28--126 | passes; fallback/higher-RPM |
| 13 in | 7,200--9,000 | 8 / 9 / 10 | 124--156 | 24--107 | passes; preferred study |
| 14 in | 6,500--8,200 | 9 / 10 / 11 | 121--153 | 20--93 | passes; preferred study |

The preliminary aerodynamic preference is **13--14 inch**.  It reduces disk
loading relative to 12 inch while retaining the current boom geometry.  A
14-inch disk has only approximately 12 mm remaining margin in the stated
screen, so it is a preferred envelope rather than an integration release.
15 inch remains outside the baseline.

The narrower preliminary geometry envelope for later integration is **13--14
inch diameter and 9--10 inch geometric pitch**.  The following
throttle-dependent no-slip RPM schedule corresponds to the 15--35% pitch
speed margin at each TAS; it is a requirement envelope, not a command-RPM
schedule or a motor/propeller selection.

| TAS (km/h) | 9-inch pitch RPM | 10-inch pitch RPM |
|---:|---:|---:|
| 60 | 5,031--5,906 | 4,528--5,315 |
| 70 | 5,869--6,890 | 5,282--6,201 |
| 80 | 6,707--7,874 | 6,037--7,087 |
| 90 | 7,546--8,858 | 6,791--7,972 |

The 13-inch top-speed screen is 7,200--9,000 RPM; the 14-inch screen is
6,500--8,200 RPM.  These are compatible pitch/RPM regions, not prescriptions
for a model number.

## Motor implications, not a motor selection

Existing central aerodynamic propulsive-power requirements are 75 W at 70
km/h and 109 W at 80 km/h. With the explicit 0.65 propeller-efficiency screen,
the corresponding motor shaft powers are 115 W and 168 W. At approximately
6,500--8,000 RPM that corresponds to about 0.15--0.23 N m shaft torque.
Treating the 490 W and 670 W electrical
integration screens with explicit 0.98 ESC and 0.87 motor efficiency yields
approximately 418 W and 571 W motor-shaft power; at 6,500 RPM these require
approximately 0.61 and 0.84 N m respectively.  Motor continuous and burst
ratings need verification at their actual cooling and loaded RPM, not against
catalogue maximum watts.

For the 13--14 inch RPM envelope, a purely kinematic loaded-voltage screen
(`RPM_loaded = 0.75--0.85 * Kv * V_loaded`) gives approximately:

| Architecture study | Loaded bus voltage | Implied no-load Kv for 13--14 in screen |
|---|---:|---:|
| 6S | 21 V | 365--570 RPM/V |
| 4S | 14 V | 545--860 RPM/V |

This does not by itself select 6S, because prop torque, motor resistance,
current, mass, ESC limits, cell sag and thermal performance also matter.  It
does show that 4S moves the same large-prop RPM envelope toward higher Kv and
therefore needs a more careful current/motor-map check.

## Required next evidence

- measured thrust, RPM, electrical input and efficiency against 60--90 km/h
  airspeed for the candidate prop/motor system;
- battery loaded-voltage curve and thermal current limit;
- installed prop plane, boom Z offset, local boom deflection, spinner/mount
  and tail/elevator clearance; and
- blade count, noise, shaft/adaptor and motor cooling constraints.

Run the study with:

```bash
./tools/cad-shell.sh scripts/propeller_envelope.py
```
