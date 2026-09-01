# LR1600 master layout and mass properties

## Scope and source of truth

This module establishes a common reference for subsequent fuselage, twin-boom,
empennage, propulsion, battery, and avionics work. It is **not** external
fuselage CAD or a hardware selection, and it does not alter the wing. The wing representation is only a
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

The current `cg.initial_envelope.status` is `initial_design_assumption`, based
on the preliminary tail-stability sensitivity study. It is a design band, not
a measured aircraft CG. The distinct `first_flight_recommendation` marker is
also preliminary and must be replaced by a weighed all-up aircraft CG before
flight.

## Mass ledger and calculator

Each `mass_budget.components` entry has a stable `id`, human-readable `name`,
`status`, `mass_g`, `x_mm`, `y_mm`, and `z_mm`. `side` plus a matching
`pair_id` records left/right symmetric pairs explicitly; each physical member
remains an individual point mass. A `known` or `design_estimate` entry requires
all four numerical values. A `tbd` entry may use `null` for any unmeasured
value and remains visible in calculation output. Negative and non-finite
values are rejected.

[`scripts/mass_properties.py`](../scripts/mass_properties.py) calculates a
measurement-backed subtotal from complete `known` entries:

```text
total mass = Σ mi
Xcg = Σ(mi × Xi) / Σmi
Ycg = Σ(mi × Yi) / Σmi
Zcg = Σ(mi × Zi) / Σmi
```

It returns the complete unresolved list with any known subtotal. If every item
is populated but one or more are `design_estimate`, the same calculator emits
a separately named **estimated configuration CG**; it is never a final
measured-aircraft CG. If even one entry is `tbd`, neither estimate nor subtotal
may be labelled final. The repository ledger currently contains deliberate TBD
placeholders, so it produces no numerical aircraft CG.

## Current master-layout output

`cad/master_layout/model.py` builds a CadQuery reference model containing the
configured wing planform, datum/axes, MAC, CG design band, preliminary
first-flight marker, and explicitly known point-mass markers. When the typed
`tail` and `booms` sections have `initial_design_assumption` status, it also
shows the horizontal stabilizer/elevator, twin fins/rudders, and dashed boom
reference axes. The tail is a preliminary aerodynamic layout, and the dashed
axes run from the wing AC reference to the tail AC reference: they are neither
boom tubes nor selected wing hardpoints. Horizontal-tail and fin leading edges
are derived by aligning their quarter-chord reference with the typed tail AC.

When their typed preliminary sections are defined, the model additionally
draws simple bounding envelopes for the min/max propeller disks at the typed
propeller X/Z plane, motor, battery and full battery-X travel, plus every
component in `avionics.components`. These are installation-volume references,
not selected commercial hardware, mass markers, fuselage skin, wiring, or
mounting geometry. The battery travel solid spans its configured X adjustment
endpoints; the pack solid is centred in that typed travel interval. The ESC is
also rendered only because `propulsion.esc` now supplies an explicit typed
bounding envelope; its still-TBD mass-ledger item is deliberately not treated
as a measured mass marker. The preview workflow creates `master_layout_iso.png`,
`master_layout_top.png`, and `master_layout_side.png` in `generated/previews/`
and lists them in its gallery.

Before any fuselage geometry can be created, determine at minimum: real
component masses; selected battery form factor; ESC envelope; wing-to-fuselage
and boom structural interfaces; boom geometry/material; empennage planform and
control authority; and avionics/antenna/GNSS/EMI installation constraints.
Those data must be entered as sourced configuration values rather than guessed
CAD dimensions.
