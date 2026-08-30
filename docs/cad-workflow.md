# CAD workflow

`config/aircraft.yaml` → `scripts/config.py` (typed validation) → Python/CadQuery source → STEP/DXF/SVG/STL in `build/`
→ visual inspection in FreeCAD/Inkscape/LibreCAD → automated checks → LightBurn
→ laser.

`config/aircraft.yaml` is the sole editable source of truth for aircraft
parameters. Generators and build scripts must obtain it through
`scripts/config.py`; `build/` and `generated/` are derived artifacts only.

All source geometry and exports use millimetres. DXF uses `$INSUNITS = 4` and
layer `CUT`; SVG explicitly specifies physical `mm` width and height. Kerf is
not part of CAD source — configure it only for the particular material and
laser at the manufacturing stage.

Run `./tools/build.sh` and `./tools/test.sh` before review. The calibration
coupon is a mandatory first import/measurement check for any new workstation.
