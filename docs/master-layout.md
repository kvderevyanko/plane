# LR1600 master layout and mass properties

## Scope and source of truth

This module establishes a common reference for subsequent fuselage, twin-boom,
empennage, propulsion, battery, and avionics work. It is **not** a fuselage or
tail design, and it does not alter the wing. The wing representation is only a
reference geometry read from the typed
[`config/aircraft.yaml`](../config/aircraft.yaml) model. That YAML file,
loaded through [`scripts/config.py`](../scripts/config.py), is the single
editable source of aircraft parameters. Files in `generated/` (including
preview PNGs) are downstream disposable artifacts and are never inputs.

## Coordinate system and units

The coordinate system is defined exactly once in `layout.coordinate_system`:

| Item | Definition |
| --- | --- |
| Datum | root-wing leading edge, `(X, Y, Z) = (0, 0, 0)` |
| `+X` | aft along the aircraft |
| `+Y` | right |
| `+Z` | up |
| Length | mm |
| Mass | g |

No fuselage, tail, motor, or CAD-local datum is permitted for mass-property
data. Convert any measured coordinate to this system before entering it in the
ledger.

## MAC and CG reference

MAC is not stored independently: all consumers use
`WingConfig.mean_aerodynamic_chord_mm`. The current typed configuration gives
**225.925925925926 mm** (display: **225.93 mm**). The master layout also uses
the typed `mean_aerodynamic_chord_leading_edge_x_mm` property to place the MAC
in the shared root-LE datum; it derives from the canonical MAC property and
the existing centered trapezoid reference.

The current `cg.initial_envelope.status` is `tbd`. As documented in
[the aerodynamic CG reference](cg-reference.md), a numerical initial/design
range cannot be justified until tail geometry/effectiveness, longitudinal
stability and trim criteria, and pusher thrust-line inputs are defined.
`initial_design_assumption` is allowed only with min/max fractions of MAC and
a recorded basis. It is not a first-flight release: a separate measured,
conservative first-flight CG must be approved after the completed aircraft is
weighed.

## Mass ledger and calculator

Each `mass_budget.components` entry has a stable `id`, human-readable `name`,
`status`, `mass_g`, `x_mm`, `y_mm`, and `z_mm`. `side` plus a matching
`pair_id` records left/right symmetric pairs explicitly; each physical member
remains an individual point mass. A `known` entry requires all four numerical
values. A `tbd` entry may use `null` for any unmeasured value and remains
visible in calculation output. Negative and non-finite values are rejected.

[`scripts/mass_properties.py`](../scripts/mass_properties.py) calculates only
complete `known` entries:

```text
total mass = Σ mi
Xcg = Σ(mi × Xi) / Σmi
Ycg = Σ(mi × Yi) / Σmi
Zcg = Σ(mi × Zi) / Σmi
```

It returns the complete unresolved list with any known subtotal. If even one
entry is `tbd`, `is_final_aircraft_cg` is false: the subtotal must never be
labelled as final aircraft CG. The repository ledger currently contains only
deliberate TBD placeholders, so it produces no numerical aircraft CG.

## Current master-layout output

`cad/master_layout/model.py` builds a CadQuery reference model containing only
the configured wing planform, datum/axes, MAC, explicitly known point-mass
markers, and a CG band when it is justified in the typed config. It intentionally
contains no guessed fuselage, battery, motor, ESC, boom, tail, or electronics
volume. The preview workflow creates `master_layout_iso.png`,
`master_layout_top.png`, and `master_layout_side.png` in `generated/previews/`
and lists them in its gallery.

Before any fuselage geometry can be created, determine at minimum: real
component masses/envelopes; battery form factor and allowable travel; motor,
propeller and ESC installation envelope; wing-to-fuselage and boom structural
interfaces; boom geometry/material; empennage planform and control authority;
and avionics/antenna/GNSS/EMI installation constraints. Those data must be
entered as sourced configuration values rather than guessed CAD dimensions.
