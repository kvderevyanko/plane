# Аэродинамика LR1600: верификация Clark Y

`config/aircraft.yaml` — единственный редактируемый source of truth. Этот документ — читаемый snapshot; воспроизводимые результаты находятся в `analysis/aero/summary.json`, `analysis/aero/raw/`, `analysis/aero/parsed/` и `analysis/aero/plots/`. Они не являются входом генератора.

## Загруженная конфигурация

Typed loader `scripts.config.load_aircraft_config` загрузил: span **1600 mm**, root/tip chord **250 / 200 mm**, площадь **0.360 m²**, MAC **225.926 mm**, Clark Y, washout **−1.5°**, target mass **2400 g**, design load factor **4.0 g**. Базовая атмосфера ISA sea-level: ρ=1.225 kg/m³, μ=1.789×10⁻⁵ Pa·s. Re по MAC для 35/50/70/100 km/h: **150403 / 214862 / 300807 / 429724**.

## Метод и исходные данные

Координаты `data/airfoils/clarky.dat` получены без ручной правки из [UIUC Airfoil Coordinates Database](https://m-selig.ae.illinois.edu/ads/coord_database.html); источник/дата — в `clarky.source.md`, SHA-256 — в summary. Использован portable project-local **XFOIL 6.99**: `.tools/apps/xfoil/usr/bin/xfoil`.

`scripts/run_airfoil_analysis.py` рассчитывает вязкие 2D полярные cases Re **120k, 150k, 200k, 214862, 300k, 430k, 480k**, α **−6…+18°** с шагом 0.25°, Ncrit=9 (clean) и Ncrit=5 (realistic model). Сохраняются точный XFOIL input, stdout/stderr, PACC polar и parsed CSV. Для Ncrit=5 выполнен также прямой reverse sweep 18→−6°; файлы имеют `_reverse`, а combined CSV объединяет только непосредственно сошедшиеся строки с полем `source` (`forward`/`reverse`). Добавленных или интерполированных точек нет.

## 2D результаты XFOIL

Ниже — representative converged значения; это не CFD и не эксперимент.

| Ncrit | Re | CLmax 2D / α | CDmin | max L/D (CL) | Combined direct polar: отсутствующие α |
|---|---:|---:|---:|---:|---|
| 9 | 150k | 1.3807 / 12.75° | 0.01245 | 64.7 (0.947) | 3 |
| 9 | 300k | 1.4064 / 13.0° | 0.00808 | 84.9 (0.855) | 1 |
| 9 | 430k | 1.4211 / 13.5° | 0.00690 | 94.7 (0.832) | 0 |
| 5 | 150k | 1.3674 / 12.75° | 0.01098 | 63.5 (0.948) | 0 |
| 5 | 300k | 1.3958 / 13.5° | 0.00824 | 77.9 (1.094) | 0 |
| 5 | 430k | 1.4364 / 14.25° | 0.00744 | 87.3 (1.081) | 2 (1.5°, 5.25°) |

Конкретные пропуски, последняя сошедшаяся α и warnings записаны в `summary.json`. Для wing/stall solver используется только первая наблюдаемая pre-peak ветвь CL; post-peak continuation не считается надёжной характеристикой срыва. Графики CL–α, CD–CL, L/D–CL, Cm–α и Re-сравнения генерируются в `analysis/aero/plots/`.

## 3D оценка и stall

2D CLmax не подставляется напрямую в Vs. Clean solver использует 40 станций на полукрыле, taper/washout, локальный Re от искомой скорости, finite-AR induced angle, интегрирование с весом `chord × dy` и **не даёт credit флаперонам**. Для 2400 g получен self-consistent clean case: **CLmax,wing = 1.163**, α≈12°, Vs=**34.49 km/h**, Re root/tip **164k / 131k**.

Ncrit=5 direct-polar coverage после обоих sweep всё ещё имеет внутренние pre-peak gaps для части нужных section conditions. Поэтому Ncrit=5 solver возвращает `unsupported`; далее — не solver outputs, а прозрачные engineering sensitivity scenarios. При `AR=7.111` и `f(e)=1/[1+6.3/(πeAR)]`:

- nominal: `1.163 × 0.9822 × f(0.85)/f(0.90) = CLmax,wing 1.126`;
- conservative: nominal basis при `e=0.75`, затем `×0.90` = `CLmax,wing 0.981`.

| Масса | Clean CL=1.163 | Nominal scenario CL=1.126 | Conservative scenario CL=0.981 |
|---:|---:|---:|---:|
| 2200 g | 33.02 km/h | 33.56 km/h | 35.95 km/h |
| 2400 g | 34.49 km/h | 35.05 km/h | 37.55 km/h |
| 2600 g | 35.91 km/h | 36.48 km/h | 39.09 km/h |
| 2800 g | 37.26 km/h* | 37.86 km/h | 40.56 km/h |

`*` Clean 2800 g не имеет непрерывного direct-polar покрытия в strict solver; это mass-scaled estimate с CL=1.163, не solver result. Это не лётные ограничения: нужны консервативные наземные/лётные испытания.

## Крейсер, ветер и вывод

Для target mass требуемый CL в 50/60/70/80/90/100 km/h: **0.553 / 0.384 / 0.282 / 0.216 / 0.171 / 0.138**. Наиболее эффективная wing-only скорость примерно **55–65 km/h**; mission operating range остаётся 60–90 km/h. Для крыла alone оценка drag при 80/90/100 km/h — примерно **1.37 / 1.58 / 1.84 N**. Это не full-aircraft drag: фюзеляж, оперение, винт/мотогондола, зазоры и паразитное сопротивление не включены; точный aircraft drag/power здесь не рассчитан.

Groundspeed = airspeed − headwind: 70 km/h TAS даёт 52/41/34/27 km/h при 5/8/10/12 m/s; 90 km/h даёт 72/61/54/47 km/h. Диапазон 60–90 km/h кинематически пригоден для ветреного дальнолёта, но не заменяет энергетический расчёт.

Clark Y остаётся кандидатом №1: результаты и рабочий Re-диапазон не показывают причины менять площадь, хорду, span, washout или профиль. Возможные дальнейшие сравнения — только при необходимости: **NACA 4412**, **E205** или **Selig S3021**; сначала проверить их реальные координаты/толщину и прогнать тем же pipeline. Ни один из них не выбран. Геометрия и профиль этой работой не менялись.

Ограничения: XFOIL особенно ненадёжен около срыва/низкого Re, не моделирует производственные дефекты, 3D separation, фактические флапероны и полный самолёт. Он не является CFD или экспериментом. `--reuse-raw` лишь переобрабатывает сохранённые raw polars; обычный запуск выполняет XFOIL.
