# LR1600 material-validation workflow

This home-test programme reduces uncertainty in the preliminary wing concept in
[structures.md](structures.md). Aircraft geometry, target mass and load factor
remain only in `config/aircraft.yaml`, read by the typed config loader. No result
changes geometry or a strength allowable.

> **Poplar plywood 1.5 mm is not available and must not be used. Available
> poplar plywood thickness is 2.0 mm.**

## Start and data entry

Copy `analysis/materials/measurements.example.yaml` to ignored
`analysis/materials/measurements.yaml`; give every specimen an ID, enter raw
values, and keep photos in `analysis/materials/photos/`. Run
`./tools/cad-shell.sh scripts/analyze_material_measurements.py`. It writes
`analysis/materials/results/summary.json`; absent input stays `NOT_MEASURED`.
`MEASURED` means an observation, `DATASHEET` a supplier statement,
`ASSUMPTION` a separate screen and `DERIVED` a calculation from observations.

Use a 0.1-g-or-finer scale and a 0.1-mm-or-better caliper (0.01-mm micrometer
is preferred for plywood). If a 100 x 100 foam coupon weighs below 2 g on a
0.1-g scale, use 200 x 200 coupons or a stack. Record instrument resolution,
ambient temperature and photo filename.

The importer validates `metadata.format_version = 1`,
`metadata.data_variant = home-test-v1`, every top-level domain and rejects unknown fields,
negative loads/masses and impossible dimensions. It writes SHA-256 provenance
for the raw measurement YAML and the typed aircraft YAML. Structural analysis
re-runs the import from the raw YAML and rejects edited/stale summaries; do not
hand-edit `results/summary.json`.

## Coupons to make

| IDs | Material / count | Nominal test-only part |
| --- | --- | --- |
| `MAT-FOAM3-01…03`, `MAT-FOAM5-01…03` | foam 3/5, 3 each | 100 x 100 density square; 200 x 200 optional foam |
| `MAT-POP2`, `MAT-BIRCH2`, `MAT-BIRCH3` | each plywood, 3 | 100 x 100 density/visual coupon |
| `PLY-BEND-*` | each plywood, 3 along + 3 across face grain | 240 x 25 strip |
| `PLY-BEAR-*` | birch2/birch3, 3 each; poplar2 optional | 100 x 30 with centred Ø3/4/5 hole |
| `GLUE-FF/FB/BB-*` | 3 per family | 160 x 25 single-lap, 25 x 25 overlap |
| `GLUE-CB-*` | 3 | 14-mm tube, 75-mm bond to 25 x 100 birch2 plate |
| `LW-RIB-TEST-*` | LW-PLA, 3 | 180 x 20 x 2 rib-like beam |
| `CARBON-SPAR-01` | actual 14 x 12 tube | inspect and reuse uncut for EI test |
| `SOCKET-01` | actual tube, rod, liner, sleeve, birch | representative central socket |
| `DBOX-A/B/C-01` | foam/birch/glue/reinforcement | 300-mm torsion article, root chord 250 |

All CAD exports are test-only, generated in mm, and have no kerf compensation
in nominal geometry. Sand/remove laser char and vacuum it before a structural
glue joint. Printed gauges are screening only: final fit uses actual measured
tube and precision rod.

## Foam density and indentation

Measure L/W, five thickness points (software minimum three), then mass. Density
is `mass_g * 1,000,000 / (L_mm * W_mm * mean_thickness_mm)` kg/m³. Test three
samples and record surface skins/cell direction/dents/water uptake.

For a comparative indentation metric, support a 150 x 150 foam piece on a flat
board, centre a rounded 25 x 25 flat indenter and apply 0.5/1.0/1.5/2.0 kg for
60 s each. Record indentation and recovery after 10 min unloaded. It is not a
modulus or compression allowable. Stop for puncture, cracks or cell collapse.
Unsupported 3-mm foam is not credited as a spar.

## Plywood density, bending and bearing

Record ply count, face grain, voids, delamination, warp and char. Density uses
the foam procedure. For bending place 240 x 25 strip on 25-mm rounded supports,
**200-mm clear span**, with a centred 25-mm shoe. Apply 2/4/6/8 N for 30 s,
unloading between steps; use a catch underneath. Test long/cross face grain.
The tool uses `EI = P L³/(48δ)` and effective E from measured section; R² must
be >=0.995 for stiffness use. Do not load to break.

For bearing, use 100 x 30 coupon, centred Ø3/Ø4/Ø5 hole and 25-mm edge distance.
A smooth bolt/washer in a guarded in-plane pull fixture shows first ovality,
splitting, crushing and net-section failure. Photograph both faces. Stop at a
crack, abrupt displacement or fixture slip. It compares birch2/birch3 for a
future boom detail; it is not a bolt allowable.

## LW-PLA stiffness and creep

Print three beams with 0.20-mm layers, 0.45-mm nominal line width, three walls,
2.0-mm rib body, 10–15% gyroid only around tabs/transitions and layers normal to
the rib plane. Record nozzle, temperature, flow/foaming setting, lot and mass;
the last three are user inputs. Test 1/2/3 N in the 200-mm bending fixture.

For creep, clamp 120 mm as a cantilever, add 1 N at the tip, and record initial,
10 min, 1 h, 4 h and 30-min recovered deflection. 40–50 C is optional only in
a supervised dedicated non-food thermostat box; never use a food oven. LW-PLA
remains optional until density, creep and interlayer observations are acceptable.

## Glue coupons and retained mass

Make three each foam–foam, foam–birch2, birch2–birch2 and carbon–birch2. Use
25 x 25 flat overlaps; carbon uses 75-mm prepared contact. Keep adhesive,
abrasion/cleaning, clamp pressure, cure and ambient identical. Weigh dry parts,
cure, reweigh; retained glue is `after - before`, aggregated as g/cm². Pull
slowly in a guarded fixture and record first slip/failure: `cohesive_foam`,
`adhesive_interface`, `plywood_delamination`, `carbon_interface`, `mixed` or
`no_failure`. First-slip/failure loads are entered as positive N values and
remain in the result. GLUE-GATE is explicit: `NOT_MEASURED` until every family
has three coupons; it fails for adhesive/carbon-interface modes. A spring scale
is comparative only and never creates a numerical joint allowable.

Every coupon needs applied-load evidence: `no_failure` requires a positive
`maximum_applied_load_n`; any observed failure requires positive
`first_slip_load_n` and/or `failure_load_n`. Failure modes are family-specific:
foam joints may be `cohesive_foam`; birch–birch may be
`plywood_delamination`; carbon–birch may be `plywood_delamination`,
`adhesive_interface` or `carbon_interface` but **never** `cohesive_foam`.
`mixed` requires at least two explicitly recorded, family-valid component modes;
it cannot hide an impossible mode. The YAML result retains all recorded loads
and modes for audit. GLUE-GATE evaluates both the headline and every mixed
component mode: therefore a carbon–birch `mixed` coupon containing
`adhesive_interface` or `carbon_interface` fails the gate.

## Carbon inspection and safe EI test

At 100-mm stations measure two perpendicular OD and, without damage, two ID
values. Measure known length/mass for g/m and straightness on a flat surface.
Current inspection screens are OD 14.00 +/-0.10, ID 11.85–12.10 and wall >=0.90;
they are not facts until measured.

Use uncut 800-mm tube on 25-mm saddles at **600-mm span**, centred 25-mm saddle,
mechanical catch and shielding. Apply known 5/10/15/20 N (about
0.51/1.02/1.53/2.04 kg) for 30 s. 20 N gives only 3.0 N m central moment and
about 24 MPa nominal stress: non-destructive, not a strength test. Record centre
deflection to 0.1 mm. R² >=0.995 is required. Valid EI can affect **deflection
only**, never tension/compression/shear allowables. Wear eye protection, stay
out of the bending plane, shield carbon splinters and capture hanging masses.

The spar geometry gate is also required before E may feed deflection: every
station must meet OD 13.90–14.10, ID 11.85–12.10, minimum wall >=0.90 and
ovality <=0.20 mm. Store all station/axis values; do not average away a failed
station. Measure the actual joiner rod at several stations, weigh known length
for g/m, then enter tube/rod fit pairs. Each radial clearance must be
0.075–0.175 mm; this completes DIMENSION-GATE only together with spar/rod gates.

## Socket and D-box proof articles

`SOCKET-01`: two actual tube segments >=325 mm, actual 600-mm rod with 275-mm
insertion each side, 50-mm central/support zone, 50-mm prepared liners/external
±45 sleeves, paired 50 x 50 birch2 plates with >=30-mm net ligament. This is
not a flight part. Use guarded opposed 250-mm torque arms, no foam. Current
100% root moment is 15.982 N m (6.52 kg at each 250-mm arm), but the structural
closeout proof is **1.25 x = 19.977 N m** (79.91 N / 8.15 kg equivalent per
arm). Test 25/50/75/100/125% with 60-s dwells. PASS requires that 1.25 proof,
no slip, crush, hoop split, delamination or plate crack, and <=0.10-mm residual
displacement. Any damage is STOP. This is a proof gate, not an ultimate strength
claim.

`DBOX-A/B/C`: actual root Clark-Y chord 250 mm, LE-to-spar 75 mm, 300-mm length,
ribs/bulkheads at 0/100/200/300. A is foam-only control; B continuous ±45 glass
80–110 g/m² candidate; C continuous ±45 carbon 80–120 g/m² candidate. Each has
foam3 skin, birch2 closure and actual adhesive. Clamp one end; use 250-mm arm
and guarded 0.5/1.0/1.5/2.0-kg masses. Measure pointer/scale (primary) and phone
inclinometer (check). `GJ = T L / theta`; R² >=0.995. Record constituent and
complete masses. Article GJ is **not** an effective material G.

For each D-box article record foam, ribs, closure, dry reinforcement,
adhesive/resin, **test-fixture mass** (end bulkheads/clamps) and complete mass.
`complete = flight-representative constituents + fixture mass` must reconcile.
The importer subtracts only the explicit fixture mass before conservative
root-article-per-metre scaling; never scale torque arms, external guards or end
fixture hardware into the wing budget.
In YAML these fields are `mass_breakdown_g.fixture_mass_g` and
`mass_breakdown_g.complete_article_mass_g`; the five flight-representative
constituents must also be recorded separately.

## Gates before production wing CAD

| Gate | Pass condition |
| --- | --- |
| SPAR-GATE | dimensions pass screens; linear EI corresponds to E >=70 GPa; strength evidence remains separate |
| DIMENSION-GATE | spar OD/ID/wall/ovality pass at every station; rod 11.50–11.70 and every radial clearance 0.075–0.175 mm |
| SOCKET-GATE | `SOCKET-01` survives 19.977 N m (1.25x) proof without damage/slip and <=0.10-mm residual |
| DBOX-GATE | reinforced article is linear and GJ >=22.8 N m²; separate from 300-MPa effective-G screen |
| GLUE-GATE | three documented repeats/family, no unacceptable adhesive/carbon-interface failure; no automatic allowable |
| MASS-GATE | re-run using density/spar g/m and article mass; final pass needs wing allocation not yet in YAML |

Mandatory: foam3/foam5/poplar2/birch2/birch3 density, spar inspection/EI,
foam–foam/foam–plywood/carbon–birch glue, socket proof, D-box GJ and mass-budget
rerun. LW-PLA is optional when it is not used in the first wing.

```bash
./tools/cad-shell.sh scripts/analyze_material_measurements.py
./tools/cad-shell.sh scripts/analyze_wing_structure.py --materials-results analysis/materials/results/summary.json --use-measured-stiffness --dbox-variant C
```

Density uses at least three specimens and retains mean/min/max/standard deviation;
the budget always propagates measured min/max, never collapses density scatter to
a point. The named D-box variant replaces overlapping planning portions with its
fixture-excluded, closed root-article mass conservatively scaled across 1.6 m.
Glue g/cm² remains `NOT_MEASURED` for wing mass until all four families have
three coupons and an explicit reproducible bond-area model is supplied. No safety
factor changes silently.
