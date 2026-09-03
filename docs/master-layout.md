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

## Fuselage/package integration v1

`fuselage_integration` is a typed preliminary **envelope and station**
contract used only by `cad/master_layout/model.py`; it is not a second source
of wing geometry and not production DXF.  The configured body reservation is
`X=-500…+410`, maximum external width 180 and height 190.  This unusually long
forward envelope is intentional: the revised complete-ledger CG study places
the 6S1P battery substantially ahead of the wing datum.  Its pitch-inertia and
rough-landing nose-protection penalty remains a design trade to be checked in
the next CAD/proof step, not something to hide by shortening the nose.

The layout renders the following confirmed preliminary references:

| Reference | Typed value / treatment |
| --- | --- |
| Outer body | rectangular installation envelope only; no implied final aerodynamic profile |
| Stations | `X=-285, -170, -55, +65, +130, +200, +285, +365`; 2-mm birch formers/webs except the listed hardpoint stations |
| Hardpoint stations | `X=-55, +65, +130, +200, +285, +365`; 3-mm birch local doublers/gear, boom, or motor load paths |
| Battery hatch reservation | 230 × 110 mm at `X=-357.5`, top plane `Z=+95`; this is a clearance reservation, **not a passed removal path** |
| Forward tail servos | elevator `(110, 0, -15)`, left rudder `(110, -32, -15)`, right rudder `(110, +32, -15)`; their shown 25×13×25-mm boxes are installation envelopes, not an SKU declaration |
| Boom interfaces | display blocks at `X=+285` and `+365`, `Y=±230`, are provisional alignment/motor-bridge references only; physical tube/joint and primary bending transfer stay TBD |
| Motor plate | replaceable display plate at `X=+410`, centered on the typed `Z=+50` motor axis |

The P60B battery branch is a 503-g design estimate (129.6-Wh nominal,
103.7-Wh study usable). The preliminary 155×75×28-mm 2-long × 3-wide pack
envelope has an indexed rail from `X=-382.5` to `-332.5`, with the first-flight
25%-MAC study index at `X=-370.0`. The unified estimated ledger gives required
centres `-381.39/-369.99/-358.58/-335.77 mm` for 24/25/26/28% MAC respectively;
the rounded rail deliberately covers that set without ballast. This is a
ledger-driven preliminary setting, not an achieved CG measurement. The layout
always reports `battery_removal_validated = false`: a top-removal mock-up must
prove pack, connector, strap and rail clearance at both stops before this can
become production geometry. In particular, do not insert a full-width former
inside the declared hatch opening; its perimeter ring/side rails are not drawn
by the reference model.

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

The typed `ground_operations` and `linkage_reference` sections additionally
render a rough-field **reference** floor/wheels, main-hardpoint points and
forward tail-actuation route lines. The current 13-in baseline uses 100-mm
mains, a 75-mm nose wheel, 350-mm track and the `Z=+50 mm` pusher screen. Its
preliminary static/compressed/tail-low/full-rough tip-clearance values are
154.9/137/93/69 mm. They are not landing-gear, ski, fuselage-skin or pushrod
production geometry. The 14-in option remains secondary and needs taller gear
and a separate prop-to-boom proof.

Before production fuselage geometry can be created, proof the battery removal
path, actual pack dimensions/mass, complete gear bay, boom/motor joints,
control-route free play and installed cooling/EMI arrangement. Those results
must replace design estimates in the typed configuration; no kerf compensation
belongs in the future source CAD.
