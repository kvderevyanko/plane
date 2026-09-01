# LR1600 Battery & Payload Packaging v1

`scripts/packaging_study.py` is a reproducible internal-volume and CG-motion
study.  It writes `analysis/packaging/summary.json`.  Neither file creates an
external fuselage shape, a battery, a motor, nor a hardware selection.

## Known

- The coordinate datum is root-wing leading edge, with +X aft; the design CG
  band is 66.26--75.30 mm (24--28% MAC) and the preliminary first-flight
  marker is 68.52 mm (25% MAC).
- Wing and twin-boom geometry remain unchanged.  A central pusher propeller
  plane and motor axis have not yet been selected.
- The mass ledger has no resolved battery or non-battery aircraft mass/moment.
  Therefore an actual aircraft CG, or a guaranteed battery X window, cannot
  be claimed by this study.

## Packaging study cases

The 100/150/200/250 Wh cases reserve simple removable-pack boxes of,
respectively, 150x55x42, 190x65x45, 230x70x50 and 270x75x55 mm. Their
central 570/850/1140/1420 g mass cases derive from the same explicit 80%
usable fraction and 220 Wh/kg nominal-pack screening assumption used in the
powertrain study. They are not mass-ledger data or battery designs. The
consistent Li-ion mass bounds are 521--625 g at 100 Wh usable and 781--938 g
at 150 Wh usable; the boxes still must be replaced by measured selected-pack
dimensions. Accordingly 100 Wh is the mass-compatible preliminary baseline.
150 Wh is a conditional stretch option only after the complete non-battery
mass/moment closes at the 2400-g target. The 200/250 Wh rows are endurance and
packaging sensitivity cases, not selected fuselage requirements.

A 60-mm tray adjustment study (-30 to +30 mm about nominal) changes aircraft
CG by `m_battery / m_total * travel`; at the 2400-g target mass its ±30-mm end
positions produce ±7.13/±10.63/±14.25/±17.75 mm shifts for the four cases
(twice those values peak-to-peak). This is sufficient in magnitude to tune
the 9.04-mm design band, but it does **not**
prove that the required X location exists: that calculation needs the resolved
non-battery mass and X moment.  The solver is provided as
`battery_x_for_target_cg_mm()`; ballast is deliberately absent from it.

`analysis/packaging/summary.json` also contains an explicit independent
non-battery sensitivity grid: 1400/1600/1800/2000 g at X=50/75/100 mm, for
each battery study case.  Each row reports the battery X required for forward,
first-flight and aft CG targets and explicitly reports its resulting estimated
configuration mass.  These are not LR1600 mass estimates; their purpose is to
make the dependence on the still-unresolved non-battery moment visible.
Downstream integration must supply `non_battery_mass_g`, `non_battery_x_mm`,
battery `mass_g`, and actual tray X limits to the same solver, then label the
result **estimated configuration CG** until every ledger item is known.

## Internal payload envelope — no external skin

The selected 100--150 Wh packaging envelope (not the 200/250 Wh sensitivity
boxes) plus 5-mm lateral/vertical clearance, 15-mm end clearance and 60-mm
adjustment travel requires at least:

| Parameter | Study envelope |
|---|---:|
| Internal width | 120 mm |
| Internal height | 90 mm |
| Battery bay length | 280 mm |
| Useful internal length | 580 mm |
| Battery adjustment travel | 60 mm |

The useful length is a zoning sum of an 85-mm FPV/nose bay, 150-mm avionics
service bay, 280-mm battery bay and a 65-mm wing-attachment exclusion zone.
It is not a prescribed fuselage length or outer aerodynamic form.

## Tray/retention interface

The future tray needs indexed positions across at least 60 mm, a positive
mechanical stop and secondary retention, a non-compressive strap/cradle,
accessible connector, protected high-current cable exit, and removal without
wing removal where the future attach geometry permits it.  Its proof load,
hatch, material and external structure are TBD.

## Placement constraints

- Battery is the principal movable mass near the CG region.
- ESC needs cooling and a short high-current path to the pusher motor, while
  its wiring remains away from the compass.
- FC belongs near CG on vibration isolation; GNSS/compass must be remote from
  motor/ESC/high-current wiring.  Receiver antennas and VTX need separation,
  while VTX needs thermal airflow.
- Typed preliminary motor/propeller/ESC positions provide a packaging view;
  their airflow, final cable routes, hardware dimensions and installation
  clearances still require validation.

## Reproduction

```bash
./tools/cad-shell.sh scripts/packaging_study.py
pytest -q tests/test_packaging_study.py
```
