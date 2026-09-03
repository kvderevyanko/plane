# LR1600 preliminary CG closure v1

> Superseded for the active airframe by
> [`cg-integration-v2.md`](cg-integration-v2.md). This preserves the rejected
> P30B/X=0 study only; it is not a current layout or mass source.

Result: **blocked before fuselage CAD**. The concrete 6S2P battery makes the
previous X=0 with ±30-mm tray demonstrably unsuitable; no ballast is introduced.

Central ledger with the remaining 220.05-g fuselage group granted a favourable
X=-100-mm centroid gives:

| Target | CG X from root-wing LE | Required pack X | Inside current -30…+30 tray? |
|---|---:|---:|---|
| 24% MAC | 66.26 mm | -414.19 mm | No |
| 25% MAC | 68.52 mm | -405.50 mm | No |
| 26% MAC | 70.78 mm | -396.81 mm | No |
| 28% MAC | 75.30 mm | -379.43 mm | No |

Changing the future fuselage-group centroid from -200 to 0 mm moves central
25%-MAC answer from -370.23 to -440.76 mm. It cannot be silently assigned a
moment merely to pass CG.

At current tray -30/0/+30 mm, the favourable screen yields about
166.15/173.95/181.75-mm CG: well aft of 24–28% MAC. The 624-g battery changes
aircraft CG by 0.260 mm per mm translation; 60-mm travel can span a 34.76-mm
design-CG band once correctly centred, but its X location is wrong.

Do not write a new tray coordinate into `aircraft.yaml` yet. Current central
solver sensitivity spans approximately X=-450…-344 mm, but wing/tail/fuselage
moments must be acquired before that screening result becomes a packaging
reservation. Actual candidate pack envelope is
215 x 84 x 30 mm; a 235 x 104 x 45-mm hatch is dimensional minimum only,
**not** a passed removal-path check because external fuselage/hatch geometry
does not exist.

The aerodynamic first-flight 25%-MAC marker remains preliminary. It is not
reachable in this mass/layout configuration; no first-flight CG release or
external fuselage geometry may be frozen from this study.
