# LR1600 hardware baseline v1

> Superseded for active fuselage/gear integration by
> [`config/hardware.yaml`](../config/hardware.yaml) and
> [`cg-integration-v2.md`](cg-integration-v2.md). This retained document is
> historical evidence for the rejected 14-in/KDE/P30B branch, not a current
> component selection or mass source.

Status: selected preliminary hardware, **not** a procurement release. Aircraft
requirements remain in `config/aircraft.yaml`; exact commercial facts, masses
and installation envelopes have one versioned source: `config/hardware.yaml`.
Every commercial source was retrieved on 2026-09-01.

## Propulsion

| Item | Preliminary selection | Evidence and disposition |
|---|---|---|
| Propeller | APC LP14010E / 14x10E Thin Electric, two blade, 34.02 g | [APC](https://www.apcprop.com/product/14x10e/) gives geometry, mass and hub. [UIUC Volume 4](https://m-selig.ae.illinois.edu/props/volume-4/propDB-volume-4.html) provides Ct/Cp/efficiency data. |
| Fallback prop | APC13010E / 13x10E | [Horizon/APC listing](https://www.horizonhobby.com/product/electric-propeller-13-x-10e/APC13010E.html); lower-clearance fallback, but less convincing 90-km/h forward-flight screen. Not in the mass baseline. |
| Motor | KDE Direct KDE4215XF-465 | [Manufacturer](https://www.kdedirect.com/products/kde4215xf-465): 465 KV, 4–6S LiHV, 195 g bare, 48.2 x 36 mm, 62 A / 1375 W for 180 s with >=5 mph cooling. |
| ESC | Hobbywing Skywalker 60A V2 / 30216101 | [Official manual](https://www.hobbywing.com/en/uploads/file/20250930/64b726be7a56c9f415385f77683cdc46.pdf): 3–6S, 60 A continuous, 80 A peak, 68 g, 73 x 30 x 12 mm. Integral 5-V BEC is unused. |

The APC 14x10E central forward-flight screen is about
4.5/4.9/5.58/6.27 krpm at 60/70/80/90 km/h. Pitch speed is
68.6/74.7/85.0/95.5 km/h and tip speed 83.8/91.2/103.9/116.6 m/s. These are
kinematics, not a safe-RPM approval. The 490/670-W electrical screen uses a
static-coefficient proxy around 6.6/7.33 krpm and 26/32 N only.

KDE has no manufacturer map for a 6S APC14x10E pusher combination. Before
purchase or flight, bench-test current, RPM, thrust and motor/ESC temperature
in the installed pusher geometry; capture the current APC RPM limit too. True
pusher installation has APC lettering facing aircraft front and a positively
retained, nutted adapter. Motor reversal cannot correct a prop mounted with
the wrong airfoil face.

The 14-inch disk remains in the 460-mm boom-spacing screen; 15 inch remains
excluded from baseline until a new geometry/dynamic-clearance analysis.

## Battery and protection

Selected preliminary cell is [Molicel INR-18650-P30B](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-18650-P30B-80111-1.pdf), not a marketplace cell. A 6S2P pack gives:

| Quantity | Value |
|---|---:|
| Typical nominal / 80%-usable energy | 129.6 / 103.68 Wh |
| Complete pack estimate | 624 g = 564 g cells maximum + 60 g construction allowance |
| 685-W screening load at 21 V | 32.62 A pack / 16.31 A per cell |
| Documented cell continuous limit | 30 A to 80 °C cutoff |
| First-order 50%-SOC cell-only sag | 0.277 V/cell; 1.66 V/6S |

The documented 17-mOhm DCIR is used only for the 50%-SOC cell calculation;
low-SOC, temperature, ageing, busbar and connector effects need a pack
load/sag/temperature test. 6S3P is a 150-Wh stretch (194.4 Wh typical,
155.5 Wh at 80%, roughly 926 g with construction allowance) and remains a
mass-risk alternative.

Architecture is balance-charge/monitoring-only with thermal sensing; there is
**no power-path BMS between pack and ESC**. A BMS transient disconnect is a
single-point propulsion loss. The future flight path is pack positive → fuse →
anti-spark/main disconnect → current sensor → ESC plus independent regulators.
Exact fuse, anti-spark connector, BMS and time-current validation remain TBD.
The [Littelfuse MEGA family](https://www.littelfuse.com/assetdocs/littelfuse-datasheet-mega-32v?assetguid=9fe0cd60-17bf-4fd7-b18d-977d32179af9) is a family reference, not a selected fuse.

## Controls and avionics

Baseline control count is two aileron, one elevator and two rudder servos:
four Hitec [D85MG](https://hitecrcd.com/d85mg-micro-32-bit-metal-gear-servo/)
at 21.9 g, 4.3 kgf-cm and 2.15-A stall each, plus Hitec
[HS-7245MH](https://hitecrcd.com/hs-7245mh-high-voltage-high-torque-metal-gear-coreless-mini-servo/)
at 34 g, 5.2 kgf-cm and 1.6-A stall. Aggregate hard stall is 10.2 A / 61.2 W
at 6 V: an electrical transient, not an average-power claim. Hinge-moment and
load-path validation are still required.

Dedicated 6 V is [Pololu D24V150F6](https://www.pololu.com/product/2882),
thermal-dependent 15 A nominal / 32-A instantaneous. Clean 5 V is
[Pololu D24V90F5](https://www.pololu.com/product/2866), thermal-dependent
4–8 A. Both need installed thermal validation; neither ESC BEC nor FC BEC
replaces the separated-rail design.

| Function | Preliminary selection |
|---|---|
| FC | Matek H743-WING V3, [manual](https://www.mateksys.com/downloads/H743-WING_Manual.pdf), 30 g; H743 WING family is [ArduPilot supported](https://ardupilot.ardupilot.org/plane/docs/common-autopilots.html). |
| GNSS/compass | Matek [M10-5883](https://www.mateksys.com/?portfolio=M10-5883), 9 g; keep >=100 mm from power/ESC/motor/ferrous parts; M10-L4-3100 fallback after failed compass survey. |
| RC | RadioMaster [RP3 Diversity ELRS](https://www.radiomasterrc.com/products/rp3-expresslrs-2-4ghz-nano-receiver), CRSF UART, 4.6 g. |
| Telemetry | Holybro [SiK V3](https://holybro.com/products/sik-telemetry-radio-v3), 23.5 g; legal 433/915 band TBD. |
| Airspeed | Matek ASPD-DLVR, 4 g; [compatibility source](https://www.mateksys.com/?page_id=7637), primary manual still required. |
| FPV | RunCam [Phoenix 2 Nano](https://www.runcam.com/download/Phoenix2-Nano/Phoenix_2_Nano_Manual_EN.pdf), 5 g; TBS [Unify Pro32 HV](https://www.team-blacksheep.com/media/files/tbs-unify-pro32-manual.pdf), 8.7 g. |

Hotel-load envelope is 7-W low, **16-W nominal** (hardware-backed design
estimate, not measurement) and 25-W high. GNSS/compass stays out of the
motor/ESC/high-current/VTX zones, receiver antennas are orthogonal and clear
of VTX, and VTX requires airflow plus legal setting. Provisional interfaces:
GNSS UART2 + I2C1, SiK UART7, CRSF UART6, airspeed I2C2; confirm the purchased
board revision before configuration.

## Gates remaining

- Motor–propeller pusher bench map, installed cooling and mount proof.
- Pack sag/temperature, fuse time-current, connector and anti-spark validation.
- Servo hinge moments, regulator transient/thermal test and linkage mass.
- Compass/RF survey, range, VTX legality/cooling and primary airspeed manual.
- Mass moments and actual battery/hatch geometry; current tray does not close CG.
