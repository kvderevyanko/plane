# LR1600 Powertrain Structural Interfaces v1

**Status: preliminary design screen; not hardware selection, production CAD or
release-to-manufacture.**  The reproducible calculation is
[`scripts/powertrain_structure.py`](../scripts/powertrain_structure.py), which
writes [`analysis/powertrain/structure_summary.json`](../analysis/powertrain/structure_summary.json).
It turns existing propulsion and packaging study cases into load-interface and
proof requirements. It does not select a battery, motor, ESC, fastener,
adhesive, carbon tube or mount material.

## Inputs retained from the aircraft source of truth

| Parameter | Value |
| --- | ---: |
| Target mass | 2400 g |
| Aircraft design load factor | 4 g |
| Gravity | 9.80665 m/s² |
| Tail arm | 650 mm |
| Boom axes | Y = ±230 mm, Z = 0 |
| Boom center spacing | 460 mm |
| Existing boom requirement | measured EI ≥125 N·m²; GJ ≥105 N·m² |

The currently screened Ø20×18 mm tube remains an **unselected conditional
geometry example**. It is not a motor mount, nor proof that its local clamp or
insert region can accept propulsion loads.

## Battery tray and retention

The packaging energy convention uses 220 Wh/kg nominal pack energy and a 0.80
usable-energy fraction, rounded to 570/850/1140/1420 g for the
100/150/200/250 Wh study cases. They are explicitly not mass-ledger entries,
selected packs or final chemistry claims. The typed 4-g aircraft context
produces 22.36/33.34/44.72/55.70 N of inertial load in one prescribed
direction.

For packaging retention only, the analysis adds a transparent **6-g
landing/ejection study case** and 1.5 proof factor. This is an assumption,
not a validated crash spectrum. The largest 1420-g envelope therefore requires
83.55 N operational retention and **125.33 N proof load per principal
direction**. With two symmetric primary hard-stops, the nominal mathematical
share is 62.66 N per stop; it must not be treated as redundancy, since a single
failed stop may not allow an escape path.

| Usable-energy study | Study mass | 4-g load | 6-g retention load | Proof load / direction |
| ---: | ---: | ---: | ---: | ---: |
| 100 Wh | 570 g | 22.36 N | 33.54 N | 50.31 N |
| 150 Wh | 850 g | 33.34 N | 50.01 N | 75.02 N |
| 200 Wh | 1140 g | 44.72 N | 67.08 N | 100.62 N |
| 250 Wh | 1420 g | 55.70 N | 83.55 N | 125.33 N |

The future tray must have a full-area, non-compressive cradle below the pack;
longitudinal hard-stops and straps/secondary retention must react the inertia,
not the cells. It needs indexed positions across the existing 60-mm CG-adjustment
study, positive end stops, independent anti-ejection retention, protected
connector exit and inspection/removal without wing removal where the future
wing attachment permits it. Foam skin, a hatch, hook-and-loop alone, a wire
harness and battery shrink-wrap are not primary restraint paths.

Expected failures are rail/stop pull-out, plywood bearing crushing at an
insert, latch/strap opening, pack abrasion or puncture from a poorly supported
tray, and thermal creep of printed retention parts. Laser-charred birch at a
structural bond must be cleaned to sound wood, abraded and dust-free before
bonding. No foam is credited as a structural restraint.

### Battery proof article

Proof a representative tray, rails, stops, latch and the actual airframe
attachments with a dimensionally representative **inert dummy**, never a live
Li-ion/LiPo pack. Apply the calculated proof load through a broad cradle in
each of +X, -X, +Z, -Z, +Y and -Y separately. Verify no latch release or
meaningful migration, permanent set, cracking, delamination, insert movement,
rail slip or connector interference; then repeat removal/reinstallation. This
is not a crashworthiness claim: selected-pack vulnerability, thermal behavior
and an actual landing/crash spectrum remain TBD.

## Pusher motor interface

The current propulsion model provides a 10.05-N high-CdA 60-km/h / 4-m/s
**dynamic** thrust study and electrical integration screens of 490 W and
670 W. With stated 0.87 motor and 0.98 ESC efficiency assumptions, those
become 417.8/571.2 W shaft power. At a conservative low 6500-rpm point their
steady shaft reaction torque is 0.614/0.839 N·m. The corresponding 1.5 proof
screens are **15.08 N axial** and **0.921/1.259 N·m torque**.

| Electrical screen | Shaft screen | RPM screen | Shaft torque | Proof torque |
| ---: | ---: | ---: | ---: | ---: |
| 490 W | 417.8 W | 6500 rpm | 0.614 N·m | 0.921 N·m |
| 670 W | 571.2 W | 6500 rpm | 0.839 N·m | 1.259 N·m |

For a separate inertial screen, unselected 120/180/220-g motor masses at a
60-mm mount-CG offset produce 0.282/0.423/0.517 N·m bending at 4 g, and
0.423/0.635/0.776 N·m at the proof factor. These are layout study cases, not
mass estimates. The selected motor's actual mass and CG offset must replace
them.

The motor cross-member must send axial thrust, shaft reaction torque, motor
inertial bending and off-axis loads into both booms and/or the primary
fuselage structure. Use paired shear features/webs for anti-rotation; a single
printed tab, adhesive-only joint, thin unsupported plywood tongue or foam is
not an adequate primary torque path. After selecting the motor, check its real
bolt circle/shaft adapter, fastener bearing, net section, insert pull-out,
adhesive peel and local carbon crushing. Keep a serviceable cooling path and
secure high-current cables against vibration/chafe.

Expected motor-interface failures include fastener bearing or pull-out, local
carbon crushing/splitting, cross-member torsion, boom-clamp slip, adhesive
peel, fatigue/resonance from rotating unbalance, and thermal creep/delamination
of printed/bonded elements.

### Motor-interface proof article

Proof a representative cross-member, boom/fuselage attachments,
fasteners/inserts and cooling geometry. Apply axial load along the prop axis,
torque through a calibrated arm, and transverse motor-CG load at the selected
offset separately. After proof, inspect for permanent alignment change,
fastener motion, cracks, delamination and clamp slip, then re-check prop-disk
and tail/boom clearance.

The 10.05-N value is not static thrust for an eventual propeller or launch
case. The selected propeller map, launch method, motor mass, prop plane,
axis-Z, mount geometry and dynamic vibration can require larger loads. These
must be established before release.

## Open structural gates

- selected pack mass, dimensions, allowed support pressure and maker's
  retention instructions;
- selected motor mass, bolt pattern, CG offset, propeller static thrust and
  torque map, balance/vibration data;
- propeller plane, motor axis Z, cross-member and primary fuselage load path;
- actual materials, adhesive/fastener allowables, local bearing/net-section
  coupons and representative proof results; and
- landing/crash acceleration spectrum, thermal environment and wire/connector
  retention details.

Reproduce with:

```bash
./tools/cad-shell.sh scripts/powertrain_structure.py
pytest -q tests/test_powertrain_structure.py
```
