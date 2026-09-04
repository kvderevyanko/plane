# LR1600 Fuselage CAD Convergence v2 — gate record

**Status: NOT RELEASED — corrective WIP.**  This record deliberately does not
replace the `fuselage_structural_group` ledger entry (398 g) or its moment.

## Reconciliation snapshot

| Item | Mass (g) | Status |
| --- | ---: | --- |
| Architecture ledger estimate | 398.000 | Authoritative integration estimate; unchanged |
| WIP before convergence | 676.136 | Divergent profile/box model; invalid |
| Current profile-derived candidate | 457.997 | Not accepted for aircraft CG or manufacture |

The current candidate is 218.139 g below the WIP number.  Its derived
breakdown is 336.742 g birch, 66.030 g 5×3-mm carbon longerons, 20.225 g
adhesive allowance from 61,744 mm² declared bond land, and 35.000 g hardware:
16 g structural fasteners, 8 g hatch hardware, 6 g battery retention, and 5 g
fixed motor-interface hardware.  The removable motor plate/adapter is excluded
from this candidate because it is owned by the propulsion ledger.

The candidate centroid is X/Y/Z = -5.072 / +0.113 / -14.753 mm.  This value is
finite and mechanically derived from the current profile extrusions, but it is
**not credible for replacing the aircraft ledger** because the gate failures
below mean the placed CAD set is not a physical assembly.

## What v2 did establish

- `PartDefinition` is the common nominal source for DXF outline/cutouts,
  plywood extrusion and profile-volume mass rows; the manifest records profile
  hashes and part-instance mapping.
- Four 5×3-mm carbon longerons are present as stock solids at the preserved
  specified paths.
- The current hatch-rail placement gives a nominal 230×125-mm opening.
- The P60B solid is evaluated at -387.5, -384.78, -373.40, -370.0 and
  -332.5 mm, with a discrete withdrawal/cable envelope.  This is a CAD check,
  not a manufacturing release.
- Boom-saddle placeholders remain `NOT RELEASED` and are excluded from the
  flight-mass set and STEP assembly.

## Independent review blockers

The independent review found that the corrective model still has no verified
complementary tab/slot geometry: mates are largely metadata, several placements
either overlap or miss, and longerons/formers do not have validated locating
grooves.  It also found window/hardpoint conflicts, an unproven gear-cassette
load path, an unassembled nose tang/index box, and insufficient proof that
battery service clearances are contacts rather than excluded collisions.

Therefore all apparent `PROTOTYPE CUTTABLE` statuses are provisional model
labels only; a complete structural sheet must **not** be cut.  Required next
work is a placement-led feature model with complementary geometry, pairwise
collision/contact and edge-distance validation, then a new independent review.

## Aircraft-mass sensitivity

No wheels+FPV, skis+FPV, or wheels+FPV+45-g-HD replacement sensitivity is
published here.  Using the candidate mass/centroid would silently convert an
unaccepted CAD set into aircraft mass data.  After the mating and load-path
gates pass, calculate those three cases by replacing only the existing
398-g/(-1.6,0,0)-mm ledger item and report AUW, CG and battery X for 25% MAC;
no ballast assumption is permitted.
