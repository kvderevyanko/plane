# LR1600 mass budget v1

This is an estimated configuration ledger, not measured aircraft mass. Hardware
masses are read only from `config/hardware.yaml`; `aircraft.yaml` does not copy
commercial masses.

| Group | Central estimate (g) | Status |
|---|---:|---|
| Wing structure including joiner | 591.25 | Design estimate; 464.1–718.4 g range |
| Boom pair | 120.28 | Conditional estimate; 112.52–128.04 g |
| Empennage structure | 115 | Design estimate; 80–150 g sensitivity |
| Motor, propeller, ESC, mount | 337.02 | Datasheet except 40-g mount estimate |
| 6S2P P30B pack | 624 | 564-g cells plus 60-g construction estimate |
| Five servos and linkage/install allowance | 188.6 | Servo datasheets plus 45-g estimate |
| FC, GNSS, RC, telemetry, airspeed, camera, VTX, regulators | 118.8 | Mostly datasheet |
| Sensor/fuse/disconnect, wiring/connectors/fasteners | 107 | Design estimate |
| **Resolved non-fuselage subtotal** | **2,179.95** | Estimated only |

At the 2,400-g target, **220.05 g** remains for the complete fuselage group:
shell/frame, battery tray, hatch, boom attachments, protection/skid and
unmodelled installation hardware. This is a hard next-step constraint, not a
selected fuselage mass or proof that a 220-g structure is feasible.

The reproducible structural low/central/high screen leaves 389.96 / 220.05 /
50.14 g respectively. The 50.14-g high case is plainly not an adequate
fuselage allowance. KDE is ledgered at its 195-g bare mass; the 85-g harness
estimate explicitly includes its supplied leads/bullets and must be measured to
avoid either omission or double count.

This is a material mass-closure blocker: range and unmeasured wing/tail moments
can consume the residual. No target-mass change is implied. The 99.7-g joiner
remains inside wing structure. Placeholder wing servos and their installation
allowance were removed before selected aileron servos and unified linkage
allowance were added.

Before external-fuselage CAD, measure or calculate wing/tail mass centroids,
selected boom-tube mass, pack, linkages, wiring, attachment and mount masses.
Until then this is estimated configuration mass, never final measured CG.
