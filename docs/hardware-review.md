# Independent review — hardware baseline v1

Review scope: evidence quality, ratings, battery model/protection, mass/CG,
and layout/removal honesty. Reviewer findings were dispositioned as follows.

| Finding | Disposition |
|---|---|
| Current X=0 ±30 mm tray cannot reach 24–28% MAC. | Accepted blocker. No new tray/hatch geometry is recorded; solver range and explicit no-closure output added. |
| 220.05-g central fuselage residual masks structural uncertainty. | Accepted. Low/central/high residual is now 389.96/220.05/50.14 g, so mass closure remains blocked. |
| CG documentation did not match generated calculation. | Fixed: current tray values are 166.15/173.95/181.75 mm. |
| Motor check implied evidence-closed capability. | Fixed: only partial KV/current screen passes; original mass envelope fails and 6S+APC operating point/continuous rating remain unvalidated. |
| Fixed-21-V sag calculation was not self-consistent. | Fixed with a cell-only constant-power root: 685 W at 21.6 V/102 mOhm gives 38.83 A, 17.64 V, 19.42 A/cell at 50% SOC. It increases the need for low-SOC/cold bench validation. |
| Prop map, FMEA, rail/servo authority, actual removal/collision are incomplete. | Accepted as procurement/fuselage gates. The analysis now labels prop data as a UIUC screening method and includes a three-motor shortlist; no false clearance, removal, hinge-moment or rail-thermal pass is claimed. |

Remaining high findings are therefore open, not waived: motor-prop pusher bench
map, APC RPM limit, ESC LVC/thermal behavior, pack build/sag/fuse test, FC
external-rail connection verification, rail-load/servo-hinge analysis,
compass/RF survey, real motor hub/adapter/wiring collision, and battery
retention/removal proof. The M10-5883 availability/EOL state must be checked at
procurement; its selected-preliminary status is not an availability guarantee.
