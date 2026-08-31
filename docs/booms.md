# LR1600 — предварительная прочностная интеграция twin-boom

**Статус: preliminary design / design estimate, не release-to-manufacture.**
Расчёт [scripts/boom_sizing.py](../scripts/boom_sizing.py) читает единственный source of truth — [`config/aircraft.yaml`](../config/aircraft.yaml) через typed loader. [analysis/booms/summary.json](../analysis/booms/summary.json) и график являются downstream-анализом. Они не дают права выбирать покупную трубу, выпускать DXF крепления или записывать массу как `known`.

## Выбранная интеграционная геометрия

| Параметр | Значение | Статус |
| --- | ---: | --- |
| Плечо от AC крыла до AC хвоста | 650 mm | `initial_design_assumption` |
| Оси двух балок | Y = ±230 mm, Z = 0 | `initial_design_assumption` |
| Межосевое расстояние балок | 460 mm | `initial_design_assumption` |
| Горизонтальное оперение | 0.0630 m² | input stability model |
| Два киля суммарно | 0.053169 m² | input stability model |
| Масса / расчётный context | 2400 g / 4 g | known typed config |

650 mm — unsupported screening length от wing hardpoint до хвостового узла. Реальная осевая линия, local fairing, длина вставки, моторная плоскость и пропеллер пока **TBD**. Модель не кредитует жёсткость стабилизатора: две балки проверены как независимые fixed-free консоли, консервативно для differential deflection.

## Нагрузки и допущения

Это не flight allowable и не сертификатный gust/yaw spectrum, а прозрачный preliminary screen: `q = ½ρV²`, `Fh = q Sh CLh`, `Mroot = F L`, `δtip = F L³ / (3 E I)`, `θ = T L / (G J)`.

| Case на 90 km/h, ISA | Результат |
| --- | ---: |
| Dynamic pressure | 382.8 Pa |
| H-tail aerodynamic screen, `CL = 1.20` | 28.94 N total |
| Empennage inertia, 0.150 kg design estimate at 4 g | 5.88 N total |
| Combined vertical load | 17.41 N per boom |
| Fin side-load screen, `CY = 1.0`, 1.5 asymmetry | 15.27 N per boom |
| Fin side-load eccentricity / torsion | 90 mm / 1.374 N·m |
| Handling/landing sensitivity | 20 N point load per boom |

0.150 kg empennage mass, `CLh`, fin force coefficient, 1.5 yaw multiplier and 20 N handling load — **design assumptions**, не измеренные свойства LR1600. Они заменяются validated tail loads, actual empennage mass и mission/landing spectrum. Пена не считается силовым элементом.

Для масштаба `analysis/booms/summary.json` также сохраняет неиспользованные как governing reference cases: H-tail 19.29 N при `CLh=0.80` и 16.48 N при простом planform-scaled aircraft 4-g load. Ни один из них не объявляется истинным распределением нагрузки; текущий 28.94-N `CLh=1.20` case — консервативный screen до появления tail-profile/incidence и control-load данных.

Для условного geometry screen приняты `E=70 GPa`, `G=25 GPa`, compression screen 300 MPa. Это **не** консервативные generic свойства неизвестной трубы: нужны datasheet, fibre architecture, measured OD/ID/ovality/mass-per-m, measured `EI/GJ` и representative coupon/proof evidence.

## Candidate section envelope

Все варианты — круглые 1-mm nominal-wall carbon tubes, **не SKU**. Масса — density sweep 1450–1650 kg/m³ для двух отрезков по 650 mm; без inserts, mount, проводки, fairing, клея и empennage.

| Candidate | EI @70 GPa | GJ @25 GPa | Stress at 13.0 N·m | δ combined vertical | Twist | Pair tube mass estimate | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ø16×14 mm | 93.2 N·m² | 66.6 N·m² | 78.1 MPa | 17.1 mm | 0.77° | 88.8–101.1 g | fails pitch/torsion screen |
| Ø18×16 mm | 135.5 N·m² | 96.8 N·m² | 60.4 MPa | 11.8 mm | 0.53° | 100.7–114.6 g | fails 0.5° torsion screen |
| Ø20×18 mm | 189.1 N·m² | 135.0 N·m² | 48.1 MPa | 8.4 mm | 0.38° | 112.5–128.0 g | conditional minimum screen |

Requirement per boom is measured **EI ≥125 N·m²**, **GJ ≥105 N·m²**, with common pitch ≤2° at the limit screen, ≤0.5° at normal 1g proxy, differential pitch ≤0.25° for a 10% EI mismatch, and torsional twist ≤0.5°. Ø20×18 mm is the conditional minimum geometry example under the stated assumed E/G; this does **not** select a tube. Ø16×14 and Ø18×16 fail the angular/torsional screen.

The 10% EI-mismatch screen gives **differential longitudinal pitch** 0.173° for Ø18×16 and 0.124° for Ø20×18; the separately reported translation across supports is tail roll/dihedral distortion, not incidence. Common tail pitch at the limit screen is 1.56° / 1.11° and its normal-1g proxy 0.39° / 0.28°. Handling deflection is 13.5 / 9.7 mm. Fixed-free Euler axial screens 791 / 1104 N greatly exceed these transverse loads, so global Euler buckling is not driver; this is not a claim about imperfect tube, joint eccentricity or local crushing.

Expected primary failure before global beam bending is **wing hardpoint/bond failure or local carbon crushing/splitting at clamp/insert**. Differential deflection can de-trim the stabilizer. A representative mounted article must receive distributed/representative tail loads, not an uncontrolled point load, and measure relative boom movement/permanent set. Laser-charred birch edges in structural joints require cleaning to sound wood, abrading and dust removal.

## Pusher propeller radial-clearance screen

No propeller is selected. The check at prop plane is `sqrt((spacing / 2)² + z_offset²) > Rprop + Rboom + clearance`; it is not `spacing > diameter`. At `z_offset = 0`, 20-mm boom OD and 30-mm manufacturing/deflection clearance:

| Study prop diameter | Minimum boom CL spacing | 460-mm baseline |
| --- | ---: | --- |
| 10 in / 254.0 mm | >334.0 mm | clears |
| 12 in / 304.8 mm | >384.8 mm | clears |
| 14 in / 355.6 mm | >435.6 mm | clears |
| 15 in / 381.0 mm | >461.0 mm | not a no-penalty fit |

Thus 10–14 in are compatible only in this z=0 screen. A 15-in disk needs geometry change or a validated relative Z solution; actual prop plane, boom deflection and attachment must be integrated first.

## Wing attachment interface requirements

Wing is not redesigned. One hardpoint per panel lies around `Y = ±230 mm`; exact `X` must join local main-spar and closed D-box load path, never foam/skin/single rib. Requirements:

- Transfer vertical, lateral and torsional loads through paired birch-2 ribs straddling mount plus birch-2 longitudinal plates into main spar and closed D-box. Foam is form only. Birch-3 is only local fastener bearing/crushing doubler after actual hole/net-section coupon.
- Use two longitudinal load stations with target ≥60 mm fore/aft separation, or substantiated equivalent clamp/sleeve, for positive anti-rotation and replaceable boom interface. A single foam-supported bolt is prohibited.
- Fixture both tube axes and stabilizer incidence during bond. Inspect straightness, clamp slip and relative tip deflection before/after proof load; screened target is ≤0.25° differential incidence.
- No bolt size, adhesive allowable, root attach X or production DXF before pusher/fuselage geometry, local bearing/net-section coupon and representative proof fixture.

## Open items / next gates

- actual carbon tube datasheet, fibre direction, section and mass;
- pusher prop plane, boom Z offset and dynamic clearance;
- elevator manoeuvre, gust, yaw and landing tail loads;
- wing hardpoint X, clamp/fastener path and coupons; and
- full estimated/measured mass ledger and final weighed CG.

Until resolved, tube mass is `design_estimate`, never a `known` ledger mass; CG remains incomplete/estimated rather than final measured aircraft CG.
