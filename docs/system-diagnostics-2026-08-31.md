# Initial system diagnostics

Collected before new installations on 2026-08-31.

| Item | Result |
| --- | --- |
| OS | Ubuntu 22.04.5 LTS |
| Architecture / kernel | x86_64 / 6.8.0-136-generic |
| Desktop / session | Ubuntu GNOME / X11 |
| Free space on `/home` | 55 GB (88% used) |
| apt / Flatpak / Snap | apt present / Flatpak absent / Snap present |
| System Python / pip | 3.10.12 / 22.0.2 |
| Git / curl / wget | 2.34.1 / 7.81.0 / 1.21.2 |
| gcc / g++ / CMake | 11.4.0 / 11.4.0 / 3.22.1 |
| Existing Inkscape | 1.1.2 (Ubuntu package) |
| Existing FreeCAD / LibreCAD / LightBurn | not found before project-local setup |
| Existing Miniforge | `/home/kirill/miniforge3`, conda 26.5.3, mamba 2.5.0 |
| Existing `lr1600-cad` | CadQuery 2.8.0 and required libraries; a new Python 3.12 project-local prefix is also provisioned |
| FUSE | `libfuse2` is installed, but `fusermount` is unavailable; AppImages run through extraction mode |
| Serial access | no `/dev/ttyUSB*` or `/dev/ttyACM*`; user was not in `dialout` or `tty` at time of check |

No laser device or controller was configured, moved, queried, or activated.
