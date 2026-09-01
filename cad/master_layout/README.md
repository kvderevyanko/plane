# Master-layout reference model

`model.py` creates a visual CadQuery reference of configured aircraft geometry
and, when supplied, selected commercial-hardware installation envelopes from
`config/hardware.yaml`.  It uses the common aircraft
coordinate system: root leading-edge datum at `(0, 0, 0)`, `+X` aft, `+Y`
right, and `+Z` up, in mm.

The thin rendered wing is not a structural skin model; its `0.25 mm` display
thickness only makes CadQuery tessellation deterministic.  The model never
adds a fuselage skin or inferred component volume.

MAC and its leading-edge position are read via the corresponding `WingConfig`
properties.  The trapezoid matches the existing centred planform.  A CG band
is drawn only when the typed `cg.initial_envelope.status` is
`initial_design_assumption` and has both configured MAC fractions.  Generated
PNGs are disposable downstream inspection artifacts.

Commercial envelopes are bounding boxes or a propeller disk, not detailed CAD
models, fuselage skin, or procurement approval. The high-current route and
antenna keep-outs are display references only. The selected battery is
deliberately *not* added as a clearance-passed hardware envelope: its rail,
hatch and removal path remain blocked pending defensible CG/mass-moment
closure. The pre-existing aircraft-config battery study envelope remains
visible and is not a claim that a physical pack can be removed.

Explicitly `known` mass-ledger entries appear as labelled coordinate markers.
They are point references only, not inferred physical envelopes. `tbd` entries
are intentionally omitted from the drawing and remain visible through the
mass-properties calculator's unresolved list.
