# Master-layout reference model

`model.py` creates only a visual CadQuery reference of the configured wing,
the sole known aircraft geometry at this stage.  It uses the common aircraft
coordinate system: root leading-edge datum at `(0, 0, 0)`, `+X` aft, `+Y`
right, and `+Z` up, in mm.

The thin rendered wing is not a structural skin model; its `0.25 mm` display
thickness only makes CadQuery tessellation deterministic.  It does not add a
fuselage, motor, battery, booms, tail, or any inferred component volume.

MAC and its leading-edge position are read via the corresponding `WingConfig`
properties.  The trapezoid matches the existing centred planform.  A CG band
is drawn only when the typed `cg.initial_envelope.status` is
`initial_design_assumption` and has both configured MAC fractions.  Generated
PNGs are disposable downstream inspection artifacts.

Explicitly `known` mass-ledger entries appear as labelled coordinate markers.
They are point references only, not inferred physical envelopes. `tbd` entries
are intentionally omitted from the drawing and remain visible through the
mass-properties calculator's unresolved list.
