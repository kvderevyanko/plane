# Laser workflow and safety boundary

1. Build and run tests.
2. Inspect the DXF in LibreCAD and the SVG in Inkscape at 100% scale.
3. Transfer only reviewed source files to LightBurn.
4. Set material-specific kerf, layer, speed and power on the production laser.
5. Use the calibration coupon on scrap material before production parts.

This repository contains no machine profile and never changes controller type,
work area, GRBL `$` settings, origin, homing, limits, speed, power, or laser
output. The actual laser is on another machine and has not been detected here.

LightBurn Linux is pinned to the final supported Linux line, 1.7.08. USB/serial
access on a machine connected to a laser normally needs the user in `dialout`
(and sometimes `tty`); that membership must be performed there with local admin
approval and requires a new login session.
