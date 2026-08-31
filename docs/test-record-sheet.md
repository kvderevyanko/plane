# LR1600 physical-test record sheet

Use one block per sample and the same ID in `analysis/materials/measurements.yaml`.

```text
Sample ID: ______________________  Date/time: ______________________
Test family: ____________________  Material / supplier / lot: __________________
Operator: _______________________  Ambient temperature: ______ C
Photo filename(s): ____________________________________________________________
Nominal CAD part: _______________  Actual L x W: __________ x __________ mm
Thickness readings (mm): _____________________________________________________
Carbon tube station / axis (OD, ID, wall, ovality): ___________________________
Joiner rod OD readings / measured tube--rod radial clearance: _________________
Mass before (g): _________________  Mass after cure (if relevant): __________ g
D-box fixture/end-bulkhead mass excluded (g): ______  Complete article mass (g): ______
Scale resolution: ________________  Caliper/micrometer resolution: __________ mm
Fixture / span / arm: _________________________________________________________
Load or torque | dwell | deflection / angle | residual after unload | notes
_______________|_______|____________________|_______________________|______
_______________|_______|____________________|_______________________|______
_______________|_______|____________________|_______________________|______
First slip/damage load: __________ N or N m
Maximum applied load when no failure occurs: __________ N
Mode: [ ] cohesive foam [ ] adhesive [ ] ply delamination [ ] carbon interface
      [ ] split [ ] crush [ ] mixed
Mixed components (at least two family-valid modes): ___________________________
STOP condition seen? __________________________________________________________
Preparation, adhesive, cure/clamp notes: ______________________________________
If projecting glue mass: CAD/assembly bond-area source + areas by family: ______
Raw YAML entry checked: [ ]  SHA-linked summary regenerated: [ ]
```

Record three density IDs per material; for carbon, all 100-mm stations with two
OD/ID values; for D-box, each constituent mass and complete mass. Never replace
an old raw record: create a new sample ID.
