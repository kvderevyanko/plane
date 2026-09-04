# Fuselage Joint & Assembly Convergence v3 — independent gate

**Status: REJECTED — complete plywood set is not cuttable.**

The v3 candidate preserved the lightened topology and reports 467.484 g, within
the 478-g joint budget.  This is not an accepted structural mass or centroid:
the assembly is not physically coherent.

## Independent deterministic findings

- 85 primary-to-primary intersections exceed 0.01 mm3; 63 have no declared
  mating relationship.  Intended contacts are not represented as feature and
  instance-level permissions.
- Former slots miss each longitudinal web in world coordinates.  The existing
  checks find a generic slot, not the stated feature, instance, alignment or
  remaining ligament.
- The four 5x3-mm carbon longerons have neither physical plywood saddles nor
  a valid insertion route: lower rods are separated from their keel webs and
  formers cut into the rods.
- Gear cassette pieces overlap rather than form a closed cassette.  There are
  no configured GFRP-leg solids, valid 4.0-mm pocket/shim stacks, bearing
  report, hardware envelope or replacement sweep.
- The nose tang/index and capture fastener are metadata rather than solids;
  index/doublers overlap.  Geometric anti-rotation and removal are unproven.
- Battery solid clears its five installed X positions, but rails, stops,
  anchors, clamps, strap/hardware access, connector and avionics service
  envelopes lack a real attached assembly.  Removal checks only the rail ends.
- Wing-transfer members are absent.  Motor plate and crossmember are separated
  by 39 mm; boom placeholders are absent from the placed assembly.
- Adhesive mass uses a fourfold longeron-land expression and must be recomputed
  only after real bond faces exist.  Generic structural-hardware ownership
  cannot yet be reconciled against landing-gear hardware.

## Required next geometric work

Replace the present profile/placement abstraction with feature-level geometry:
every actual tab, notch, saddle, bolt land and key needs an instance-level
counterpart, permitted contact volume and insertion path.  Then derive an
unexplained-collision report, a true sequential dry assembly, and only then
recalculate mass and centroid.  No part currently labelled `PROTOTYPE CUTTABLE`
has passed this gate.

## Checks performed

- `./tools/test.sh`: 166 passed, but declarations-only tests do not prove the
  listed physical conditions.
- `git diff --check`: passed.

Physical coupons/proof tests remain later gates; this rejection is based only
on resolvable CAD geometry and assembly conditions.
