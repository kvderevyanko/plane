# LR1600 material measurements

`measurements.yaml` is an untracked, user-entered laboratory notebook in YAML.
Copy `measurements.example.yaml`, enter only observations actually made, then
run:

```bash
python3 scripts/analyze_material_measurements.py
python3 scripts/analyze_wing_structure.py --materials-results analysis/materials/results/summary.json
```

The first command writes derived values to `analysis/materials/results/summary.json`.
It never fills in a missing value from an engineering assumption.  Every result
has a `state`: `MEASURED`, `DATASHEET`, `ASSUMPTION`, `DERIVED`, or
`NOT_MEASURED`.  This workflow records measured geometry, mass and stiffness;
it does **not** create a tensile, compression, bearing or adhesive-strength
allowable from a home test.

`measurements.example.yaml` is intentionally empty but valid.  Keep raw
observations in `measurements.yaml`, photos under `analysis/materials/photos/`,
and do not edit a generated result by hand.
