# Laser workflow and safety boundary

1. Build and run tests.
2. Inspect the DXF in LibreCAD and the SVG in Inkscape at 100% scale.
3. Transfer only reviewed source files to LightBurn.
4. Set material-specific kerf, layer, speed and power on the production laser.
5. Use the calibration coupon on scrap material before production parts.

## Local machine reference: ZBAITU M81-FF80-EAIR

The local production/test machine is a ZBAITU M81-FF80-EAIR. Its configured
LightBurn device bed must remain **940 × 620 mm**. These limits are a machine
and production-workflow reference only: they are not LR1600 aircraft parameters
and must not be copied into or used to modify CAD geometry or
`config/aircraft.yaml`.

The laser head requires a mandatory **50 mm clearance from every bed edge**.
With the conventional lower-left machine origin, the permitted nesting/cut
envelope is therefore **840 × 520 mm**:

- X = 50..890 mm
- Y = 50..570 mm

Keep the device bed at 940 × 620 mm in LightBurn; apply the smaller envelope
when arranging or validating jobs. Do not treat the outer bed edge as usable
for cuts or engraving.

The project launcher is `./tools/lightburn.sh`; it starts the local portable
binary at `.tools/LightBurn/LightBurn`.

### Installed laser module

The installed module is identified as **80W-C80-EAIR** (origin: China), with a
450 nm laser, TTL control and air assist. Its “80 W” label is a product
designation/marking only; it is **not** a confirmed optical-output rating and
must not be used as a verified power value for process settings. The module
information does not change the 940 × 620 mm bed, the 50 mm edge clearance, or
the 840 × 520 mm safe envelope above.

This repository does not manage controller type, GRBL `$` settings, origin,
homing, firmware limits, speed, power, or laser output. Those settings remain
machine-local and must be reviewed at the laser before production.

USB/serial access on a machine connected to a laser normally needs the user in `dialout`
(and sometimes `tty`); that membership must be performed there with local admin
approval and requires a new login session.
