# LR1600 — силовая концепция крыла, расчётная валидация

**Статус: preliminary concept validation, не production release.** Номинальная
геометрия, масса и кандидат лонжерона берутся только typed loader-ом
`scripts.config.load_aircraft_config` из `config/aircraft.yaml`. Расчёт и
воспроизводимые графики: `scripts/analyze_wing_structure.py` и
`analysis/structures/`. Generated CAD snapshots не являются входными данными
расчёта. По явному решению о фактической доступности материалов эта работа
исключает недоступные 1.5 mm из typed YAML availability; она не меняет
аэродинамическую геометрию или DXF.

> **Poplar plywood 1.5 mm is not available and must not be used in the current
> LR1600 design assumptions. Available poplar plywood thickness is 2.0 mm.**

## Входные данные и статус нагрузки

Typed config загружает: span 1600 mm, две консоли по 800 mm, root/tip chord
250/200 mm, масса 2400 g, `design_load_factor_g = 4.0`, `g = 9.80665 m/s²`,
кандидат лонжерона carbon tube Ø14/Ø12 mm на 30% хорды. Документация YAML не
классифицирует 4 g как limit или ultimate. В настоящем расчёте это **current
design/limit case**, а не заявленная ultimate-нагрузка. Поэтому:

| Уровень | Определение сейчас |
| --- | --- |
| Design / limit | 4.0 g = 94.144 N полной подъёмной силы, 47.072 N на консоль |
| Safety factor | Не «зашит» в 4 g; показан отдельно как envelope allowable / stress |
| Proof test | 100% от этой распределённой нагрузки; 125% только после утверждения limit/ultimate и процедуры safety review |
| Ultimate / failure | Пока не определён. Не утверждать flight limit или failure margin без паспортов и coupons |

Вертикальный порыв нельзя честно превратить в число без mission/CS-23-like gust
inputs, поэтому 1.25× design lift ниже — только bounded sensitivity, не
сертификационный gust case: root V/M = **58.839 N / 19.977 N·m**. Для узлов
крепления и root проверен отдельный asymmetry screen 70/30 полного design lift
(сохраняет total lift): loaded/unloaded panel root V = **65.900/28.243 N** и
M = **22.374/9.589 N·m**. До mission gust inputs эти значения не являются
flight allowables; boom и servo interface остаются un-sized.

## Распределённая нагрузка и главный лонжерон

На каждой консоли используется нормированное эллиптическое распределение,
а не сосредоточенная сила:

`q(y) = 4 Lpanel /(pi b/2) sqrt(1-(y/(b/2))²)`.

`scripts/analyze_wing_structure.py` численно интегрирует q(y) в shear V(y),
bending moment M(y) и deflection. Получены root V = **47.072 N**, root M =
**15.982 N·m**. CSV и четыре графика сохраняются в `analysis/structures/`.

| Ø14×12 mm | Значение |
| --- | ---: |
| Площадь | 40.841 mm² |
| I | 867.865 mm⁴ |
| Z | 123.981 mm³ |
| Root bending stress | 128.91 MPa |
| Консервативный screening shear | 2.31 MPa |

Ниже — **не свойства купленной трубки**, а консервативные material envelopes
для предварительной проверки. В особенности compression allowable должен быть
подтверждён для конкретной lay-up и направления волокон.

| Envelope | E, GPa | tensile / compressive, MPa | bending SF tension / compression | tip deflection at 4 g |
| --- | ---: | ---: | ---: | ---: |
| Conservative | 70 | 350 / 300 | 2.72 / 2.33 | 38.4 mm |
| Nominal | 110 | 600 / 500 | 4.65 / 3.88 | 24.4 mm |
| High-quality | 140 | 900 / 750 | 6.98 / 5.82 | 19.2 mm |

**Решение по main spar:** оставить Ø14×12 только как provisional baseline:
strength screening проходит даже conservative envelope, но stiffness/proof
test являются ограничивающими. Требования к покупке: OD 14.00 ±0.10 mm,
straightness не хуже 1 mm на 800 mm, измеренный minimum ID ≥11.85 mm после
проверки ovality; E ≥70 GPa, tensile ≥350 MPa, compression ≥300 MPa, shear
≥35 MPa. Предпочтительны continuous преимущественно 0° fibres: паспортная
pultruded труба либо documented wound laminate. Без datasheet и coupon/proof
test эта труба не может считаться утверждённой.

Сравнение на том же root M:

| Вариант | I, mm⁴ | Z, mm³ | Nominal root stress, MPa | Вывод |
| --- | ---: | ---: | ---: | --- |
| Круглая 14×12 | 868 | 124 | 128.9 | Простая покупка, нервюры и ремонт; baseline |
| Прямоугольная 16×8×1 | 431 | 108 | 148.4 | В этой ориентации хуже; не менять на неё |
| 2 × carbon cap 8×1 + web 0.5 | 2881 | 230 | 69.3 | Высокий stiffness/mass потенциал, но bond/web/rib integration и damage tolerance требуют отдельного проекта |

Прогиб — **lower-bound single-spar Euler–Bernoulli** результат: не включает
joiner clearance, socket compliance, D-box/foam shear, local tube ovalization
или adhesive slip. В тестах численная интеграция дополнительно сверяется с
независимой аналитической формулой uniform-load cantilever `wL⁴/(8EI)`.

## Joiner и корневая цепь нагрузки

Рекомендуемый расчётный вариант — **precision solid carbon rod actual
11.50–11.70 mm**, общая длина **600 mm**, insertion **275 mm в каждую
консоль**, контролируемая центральная/support зона 50 mm. Не назначать «Ø12»:
измерить ID каждой основной трубы и OD каждой заготовки; требование к selected
pair — tube min ID ≥11.85 mm, радиальный зазор 0.075–0.175 mm. Это исключает
как заклинивание, так и неуправляемый loose fit.

| Joiner 11.5-mm solid | Значение |
| --- | ---: |
| Area / I / Z | 103.87 mm² / 858.54 mm⁴ / 149.31 mm³ |
| Stress при root M | 107.0 MPa |
| Force couple M/d | 1.390 kN |
| Screening contact bearing, 50-mm prepared liner | 2.42 MPa |

Для контролируемого 50-mm центрального пролёта joiner screening deflection
составляет 0.084 / 0.053 / 0.042 mm (conservative / nominal / high-quality);
bending SF compression — 2.80 / 4.67 / 7.01. Это не заменяет проверку
контактного crushing, который является более вероятным local failure mode.

Критический failure mode — local crushing/delamination thin main tube около
точек контакта, а не nominal rod bending. Каждый moment-couple contact требует
50-mm подготовленного internal G10/CF wear liner и 50-mm external ±45° carbon
hoop sleeve. Measured tube limits: ID **11.85–12.10 mm**, wall **≥0.90 mm**;
rod actual 11.50–11.70 mm. Две longitudinal birch-2 plates на contact должны
иметь ≥50-mm bonded/contact length и ≥30-mm net ligament.

| Socket screen at 15.982 N·m | Stress, MPa | Provisional SF |
| --- | ---: | ---: |
| Carbon contact bearing, 50-mm liner | 2.42 | 6.21 vs assumed 15 MPa |
| Hoop/splitting with external sleeve | 15.44 | 1.62 vs assumed 25 MPa |
| Two birch-2 plate bearing | 6.95 | 2.16 vs assumed 15 MPa |
| Birch net tension, 30-mm ligament | 11.58 | 1.73 vs assumed 20 MPa |
| Two 50×50-mm plate bondlines | 0.278 shear | coupon-required |

These are bounded **assumed-allowable screens, not final factors**. A
representative tube/liner/birch/bond coupon and full-wing proof test must pass;
otherwise the expected failures are hoop split, liner crush or birch net
section. Therefore нельзя полагаться на foam либо на гладкую неподготовленную
sliding tube wall. Силовая цепь должна быть:

`distributed load → closed reinforced D-box/skin → carbon main spar → paired
birch root/socket plates → prepared joiner contact regions → opposite console`.

На каждую консоль назначить **четыре birch-2-mm силовые нервюры**: y =
**0, 50, 250, 300 mm**. В зоне 250/300 mm они обрамляют конец захода joiner
(y=275 mm). Добавить парные 2-mm birch longitudinal shear plates/root-socket
doublers от root через эту зону и full-height spar closure. Birch 3 mm пока
нужна только как малая локальная fastener/crushing plate у окончательного boom
mount, если bolt bearing/net section coupon это подтвердит; она не является
default root rib.

## Нервюры, обшивка и D-box

Обычные нервюры: **foam 5 mm**, номинальный pitch 100 mm. Foam не является
primary load path. Сохранить 100 mm в обычной зоне; поставить дополнительные
силовые stations 50, 250 и 300 mm без замены всех нервюр фанерой. Уменьшить
локальный bay до ≤50 mm около root socket, каждого servo hatch и final boom
mount. У tip допускается 100 mm, но tip rib рекомендована как LW-PLA только
после её weighing/creep coupon (или foam, если она работает лишь как closure).

| Вариант ordinary rib | Mass одной типовой rib, planning | Назначение и ограничения |
| --- | ---: | --- |
| Foam 5 mm | 0.6–1.7 g | Выбор для большинства: лёгкая, легко клеится, но нужна проверка local indentation, moisture и сохранения Clark Y |
| Poplar plywood 2 mm | 3.6–4.3 g | Только moderate-load hatch rails/formers и templates; лучше compression/holes, но тяжелее, requires sealed edge |
| LW-PLA | Не заявлять до weighing | Tip/servo geometry/alignment features; 3 perimeter/walls, nominal 0.45-mm line width, 2.0-mm rib body, 10–15% gyroid только где нужен, layers normal to rib plane. Проверить anisotropy, heat, creep и interlayer failure; не primary path |

Foam лучше всего по массе и удобно ремонтируется вставкой/накладкой, но его
edge/crush resistance, влагостойкость и точное удержание Clark Y зависят от
реального листа и sealing. Poplar 2 mm проще держит holes и cable channels,
переносит умеренное local compression и хорошо ремонтируется, но требует
герметизации торцов и существенно тяжелее; не применять его вместо birch в
boom/root load path. LW-PLA позволяет интегрировать cable channels и сложную
servo geometry, однако изготовление медленнее лазерной foam rib, а высокая
температура, foaming density, creep и межслойная прочность оставляют его
непригодным для primary loads до coupon. Эти ограничения применяются и к tip
rib: printed вариант допустим лишь как non-primary closure.

**D-box:** foam-only замкнутая 3-mm оболочка не проходит как validated torsion
structure. Screening использует worst observed cruise `|CM|=0.0839` из
Re300k realistic-model rows `CL=0.13…0.30`, плюс 1-g elliptical lift,
перенесённую консервативно с c/4 на spar axis 30%c. Foam-only tip twist:
39.2°, 61.6°, 74.8°, 105.5° at 70/90/100/120 km/h. Reinforced triangular-cell
proxy при effective G=100/250/300 MPa даёт 3.14/1.26/1.05°, 4.92/1.97/1.64°,
5.99/2.39/2.00°, 8.44/3.38/2.81°. Требование concept gate: measured effective
G **≥300 MPa**, root GJ **≥22.8 N·m²**, tip twist ≤2° at 100 km/h and ≤3° at
120 km/h. Это не flutter calculation:
здесь нет control reversal, aeroelastic coupling или adhesive compliance.
Нужен continuous closed LE-to-main-spar cell, 2-mm birch closure web и
continuous documented ±45° carbon/glass reinforcement on skins. Масса bias
laminate+resin 35–75 g уже включена в budget. Точный lay-up определяется
coupon-ами; без него 120-km/h case не разрешать.

## Boom, servo и клеи

Окончательная boom length, section, attach station, fasteners и interface
loads не выбираются этой работой: boom attachment **un-sized**, не получает
ложных SF. После фиксации этих inputs для каждого mount нужны минимум две
birch-2 ribs, straddling mount, и birch-2 plates, которые передают clamp/shear
на main spar и closed D-box с fore/aft spacing против rotation/slip. Foam —
только form. Poplar 2 mm приемлем как secondary fairing/former, не critical
load path. Birch 3 mm — только local bolted crushing/bearing doubler после
расчёта конкретного fastener.

Серва: rear/false spar должен перейти через два bays; poplar-2 можно применить
как hatch rails, birch-2 — под servo screws и передачу нагрузки на ribs/spar;
LW-PLA — только locating/hatch geometry. Servo model, screw pattern и opening
пока не утверждены.

| Соединение | Требование к классу клея | Контроль |
| --- | --- | --- |
| Foam–foam | лёгкий foam-safe PU/contact adhesive, не растворяющий foam | peel/shear coupon, контроль массы клея |
| Foam–plywood | foam-safe PU/epoxy with compatible primer | coupon на actual foam; не считать full foam strength |
| Carbon–birch | structural toughened epoxy, abraded/degreased carbon | lap/shear coupon; maintain bondline and fillet |
| Plywood–plywood | structural epoxy or tested aliphatic/PVA where dry | lap/shear coupon |

Лазерный обугленный торец в силовом стыке очистить до sound wood, слегка
зашкурить/обеспылить; kerf compensation принадлежит manufacturing stage, не
CAD source. Adhesive budget в анализе: 35–80 g на full wing.

## Mass budget и обязательные physical coupons

Current planning estimate full assembly: **522–836 g**, или **21.8–34.8%**
target aircraft mass; одна консоль без joiner 211–368 g, joiner ~99.7 g.
Сюда входят обе 3-mm skin surfaces (65–173 g), foam ribs (9–24 g), both main
spars (104.6 g), root/boom/**continuous D-box closure** birch (106–132 g),
required bias laminate+resin (35–75 g), secondary poplar (11–13 g), adhesives,
two servo placeholders и wiring. Это диапазон, не BOM: фактическая foam,
LW-PLA, adhesive uptake, laminate areal weight и net part area должны заменить
planning estimate. До этого структура не может утверждаться как meeting mass
architecture.

Минимальная программа samples перед CAD:

| Coupon | Размер / изготовление | Измерить и простой test | Как использовать |
| --- | --- | --- | --- |
| Foam 3 / 5 | 100×100 mm, **5** шт каждого | thickness in 5 points (0.1 mm), mass 0.1 g; 3-point bend on 80-mm span; 10-mm ball indentation at 10 N / 10 N·min⁻¹ | density, skin/rib mass and indentation limit |
| Poplar 2, birch 2, birch 3 | 50×200 mm, 5 strips/grade | mass/area, thickness, grain; 3-point bend 150-mm span, then 6-mm bearing hole to defined failure | density/E range and local mount choice |
| LW-PLA typical rib | 1:1 short representative rib, stated print settings | mass 0.1 g, warp; 24-h 50°C creep under 5-N fixture, layer-direction bend at 10 N·min⁻¹ | permitted non-primary use and mass |
| Foam–foam | 25×100 overlap, 5 samples | mass glue, peel/shear at 10 mm·min⁻¹; record cohesive vs adhesive failure | foam-safe adhesive screening |
| Foam–poplar and foam–birch | same overlap, actual surface prep | failure load/rate/location | validate skin/rib bond process |
| Carbon–birch | 25×100 lap, sand/degrease carbon | shear at 10 mm·min⁻¹, inspect post-failure | joiner/socket bond choice |
| Joiner socket | actual tube + 50-mm liner/hoop + two birch plates, 3 specimens | apply moment-couple to 1.25× design equivalent; inspect crush, hoop split, plate net section and bond | required closeout of provisional socket SF |
| D-box torsion | 300-mm representative closed bay | torque vs twist up to 120-km/h equivalent, inspect seam; calculate GJ | replace assumed G and approve 100/120-km/h envelope |

Record sample dimensions to 0.1 mm, mass to 0.1 g, temperature/humidity,
adhesive batch/cure and failure mode. Material density must be measured, never
inferred as an exact value from this document.

## Safe proof test

Fixture the root socket in a rigid stand with exclusion zone and a transparent
shield; nobody stands in the bending plane. Support the wing in its installed
dihedral attitude. Invert the wing if gravity bags are used, and put a broad
spreader pad (not a point load on foam) at y=80, 240, 400, 560, 720 mm. At
100% design load, the calculated load per console is respectively **11.906,
11.412, 10.350, 8.504, 4.899 N**: hanging masses **1.214, 1.164, 1.055,
0.867, 0.500 kg**. Multiply every zone by the current step factor; do not use
a single tip weight. Include representative joiner, root plates and D-box
closure; do not proof a foam-only mock-up as a wing.

At 25%, 50%, 75%, 100% of 47.072 N per panel: load symmetrically, dwell 60 s,
measure tip deflection and root/joiner displacement, photograph the spar,
socket, glue lines and D-box. Unload after each step and measure residual.
Each pad must bridge a chordwise 80-mm-wide stiff spreader from LE D-box to
rear support, with compliant foam protection, so the test does not create an
unrepresentative local skin dent. Mark and record load versus tip deflection:
the lower-bound bare-spar prediction is 19–38 mm at 100% (depending on E), so
any sudden slope drop or measured deflection >40 mm is a STOP pending review,
not a value to average away.

**PASS:** no crack/delamination/slip, no audible fibre failure, no local tube
crush, no fastener rotation, no >10% incremental stiffness loss, and residual
tip displacement ≤1 mm or 5% of peak (whichever is smaller). **STOP/FAIL:**
visible crack, white carbon damage, debond, tube ovalization, sudden stiffness
drop, residual above limit, or any uncontrolled load shift. A 125% proof
margin is deliberately not set until the project classifies 4 g as limit and
validates a safe failure margin.

## Open physical measurements and release gate

Before production CAD: foam density/modulus/indentation; plywood grade,
density, grain and bearing strength; actual carbon OD/ID/ovality/straightness,
E and compression allowable; joiner fit; adhesive joint strength; LW-PLA
density/creep; D-box torque/twist. Expected early failure modes are D-box seam
shear/twist, joiner socket crushing/delamination, then compression failure of
an unverified carbon tube. There are no production-ready DXF files from this
work. Independent review is required after this complete diff and before any
release-to-manufacture decision.
