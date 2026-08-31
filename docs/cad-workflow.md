# CAD workflow

`config/aircraft.yaml` → `scripts/config.py` (typed validation) → Python/CadQuery source → STEP/DXF/SVG/STL in `build/`
→ disposable previews in `generated/previews/` → visual inspection in FreeCAD/Inkscape/LibreCAD → automated checks → LightBurn
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

## Visual inspection

### OCP CAD Viewer in VS Code

The workspace recommends the official **OCP CAD Viewer** extension
(`bernhard-42.ocp-cad-viewer`) and selects the project-local interpreter
`.tools/conda/lr1600-cad/bin/python`. Its Python companion is
`ocp-vscode==4.0.1`; it is installed with pip into that same project-local
environment, not system Python. The environment definition lists the optional
package so a fresh local environment can reproduce the setup.

Open [cad/ocp_viewer_example.py](../cad/ocp_viewer_example.py) in VS Code and
run it with the selected interpreter. It calls `ocp_vscode.show()` for the
existing calibration coupon only; it does not create or modify geometry. The
viewer is for interactive inspection, not a source of truth or a production
exporter. If the extension is missing locally, install the workspace
recommendation from VS Code's Extensions view and then select the project
interpreter before using the OCP CAD Viewer sidebar.

### Static local preview gallery

`./tools/build.sh` also makes the following reproducible, ignored artifacts:

- isometric, top and side PNG views of the current CadQuery calibration model;
- copies of the current generated wing plan, root-rib and tip-rib SVG drawings;
- `generated/previews/index.html`, a static, local-browser gallery.

To update and open the gallery, use `./tools/preview.sh`. In headless CI or a
terminal smoke-test use `./tools/preview.sh --no-open`. Preview files are
one-way build outputs: no generator reads them, and they must never be edited
or used as engineering input.

### Other local viewers

Open DXF files in LibreCAD with `./tools/librecad.sh build/dxf/calibration_coupon.dxf`
(or any generated rib DXF). Open SVG output in Inkscape, e.g.
`inkscape generated/rib_00_root.svg`. FreeCAD remains suitable for STEP/STL
inspection via `./tools/freecad.sh build/step/calibration_coupon.step`.
