# LR1600 material and structural test coupons

These are **TEST-ONLY, NOMINAL, NO-KERF** files.  They are not aircraft
production parts and must never be substituted for flight structure.  All
dimensions are mm.  Generate with `python scripts/generate_test_coupons.py`.

The test dimensions live in `parameters.yaml`; only the D-box root Clark Y
outline and 30%-chord spar location are loaded from the typed aircraft loader.
The generated manifest identifies material, quantity and intended use.  Laser
operators must apply any kerf process settings outside the source geometry.

For a D-box article, record the whole assembled test-cell mass and separately
record `fixture_mass_g`: birch-3 end bulkheads/clamps and all torque-fixture
parts are test-fixture-only.  Only `flight_representative_mass_g` (complete
article minus fixture mass) may be supplied to a wing mass-budget workflow.
