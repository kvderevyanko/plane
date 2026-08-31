# Development environment

## Project-local tools

| Tool | Version | Location / launch |
| --- | --- | --- |
| CadQuery | 2.8.0 | `.tools/conda/lr1600-cad`; `./tools/cad-shell.sh` |
| Python | 3.12 | project-local CadQuery environment |
| NumPy, SciPy, Matplotlib, pandas, PyYAML, ezdxf, Shapely, svgwrite, pytest | conda-forge | specified in `environment/environment.yml` |
| LightBurn | local portable package | `.tools/LightBurn/LightBurn`; `./tools/lightburn.sh` |
| LibreCAD | 2.2.1.5 | `.tools/apps/LibreCAD-v2.2.1.5-x86_64.AppImage`; `./tools/librecad.sh` |
| FreeCAD | 1.1.3 target | official AppImage download attempted but rejected on SHA-256 mismatch; not installed |
| XFOIL | 6.99.dfsg+1-3 (amd64) | `.tools/apps/xfoil/usr/bin/xfoil`; `bash ./tools/bootstrap-xfoil.sh` |

The project uses a local prefix rather than system Python. It is created from
`environment/environment.yml` by Miniforge/mamba; no `conda init` or global
`pip` is used. To rebuild it, use the command in `environment/README.md`.

`build/` and `.tools/` are ignored by Git. They are reproducible or optional;
all source, configuration and documentation are committed.

XFOIL is bootstrapped without root or system-package changes from Debian's
[`xfoil_6.99.dfsg+1-3_amd64.deb`](https://deb.debian.org/debian/pool/main/x/xfoil/xfoil_6.99.dfsg+1-3_amd64.deb); the script validates SHA-256
`8bd7d984111901e76f5466c31f30fc12fa8de283ed39a24d9a80f43b1440b6d1` before
extracting only under `.tools/apps/xfoil`. It is intentionally amd64/Debian
package specific. Run `bash ./tools/bootstrap-xfoil.sh` on a fresh checkout.

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

- The local machine reference is the ZBAITU M81-FF80-EAIR. Its LightBurn bed
  is 940 × 620 mm; the mandatory 50 mm edge clearance leaves an 840 × 520 mm
  safe nesting/cut envelope (X=50..890 mm, Y=50..570 mm) with a conventional
  lower-left origin. See `docs/laser-workflow.md`.
- Documenting the local machine does not imply a serial/controller connection:
  no controller configuration or serial settings are managed by this repository.
- Serial-group membership is intentionally unchanged; make it on the actual
  laser workstation and log out/in afterwards.
- CQ-editor 0.7.0 and FreeCAD 1.1.3 are not installed: their large official
  downloads were incomplete/corrupted in the restricted command session and
  were removed after validation. Do not modify the working CadQuery environment
  to make a GUI run. FreeCAD remains the preferred STEP viewer once its official
  AppImage has been successfully verified.
