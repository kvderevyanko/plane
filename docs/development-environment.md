# Development environment

## Project-local tools

| Tool | Version | Location / launch |
| --- | --- | --- |
| CadQuery | 2.8.0 | `.tools/conda/lr1600-cad`; `./tools/cad-shell.sh` |
| Python | 3.12 | project-local CadQuery environment |
| NumPy, SciPy, Matplotlib, pandas, PyYAML, ezdxf, Shapely, svgwrite, pytest | conda-forge | specified in `environment/environment.yml` |
| LightBurn | 1.7.08 | `.tools/apps/LightBurn-Linux64-v1.7.08.AppImage`; `./tools/lightburn.sh` |
| LibreCAD | 2.2.1.5 | `.tools/apps/LibreCAD-v2.2.1.5-x86_64.AppImage`; `./tools/librecad.sh` |
| FreeCAD | 1.1.3 target | official AppImage download attempted but rejected on SHA-256 mismatch; not installed |

The project uses a local prefix rather than system Python. It is created from
`environment/environment.yml` by Miniforge/mamba; no `conda init` or global
`pip` is used. To rebuild it, use the command in `environment/README.md`.

`build/` and `.tools/` are ignored by Git. They are reproducible or optional;
all source, configuration and documentation are committed.

## System applications

The existing Ubuntu Inkscape 1.1.2 is available at `/usr/bin/inkscape` and was
smoke-tested for SVG-to-PNG export. It is older than the current upstream 1.4.4
Snap. It has deliberately not been replaced because the repository rule keeps
new application files inside this project. If an explicitly approved system
installation becomes desirable, use the verified `Inkscape Project` Snap, not a
third-party PPA.

No global FreeCAD/LibreCAD installation was added. Portable AppImages avoid
changes under `/usr`, `/opt`, home application folders, or desktop menus. In
this environment AppImages require `--appimage-extract-and-run` because FUSE
mounting is unavailable; project launchers handle it.

LightBurn documents 1.7.08 as the final Linux line and supports Ubuntu 22.04.
The project-local AppImage SHA-256 is
`206a25a876439083df73831ff0822fb0af0c5f9cd481b1d6b2abf22ef324ab05`.

## Commands

```bash
./tools/build.sh
./tools/test.sh
./tools/librecad.sh build/dxf/calibration_coupon.dxf
./tools/lightburn.sh
```

Update the CAD environment by recreating the ignored prefix from
`environment/environment.yml`. Update portable applications only from their
official release pages, record version and checksum here, then rerun smoke
tests.

## Known limits

- No laser is attached on this machine; no machine profile or serial settings
  were created.
- Serial-group membership is intentionally unchanged; make it on the actual
  laser workstation and log out/in afterwards.
- CQ-editor 0.7.0 and FreeCAD 1.1.3 are not installed: their large official
  downloads were incomplete/corrupted in the restricted command session and
  were removed after validation. Do not modify the working CadQuery environment
  to make a GUI run. FreeCAD remains the preferred STEP viewer once its official
  AppImage has been successfully verified.
