# LR1600 former–web material-tab convergence v4.3

Scope is the thirty active former-to-web registration joints only. Longeron
saddles, supports and all other fuselage subsystems remain explicitly deferred.

## Geometry contract

Each `JointDefinition` owns one `web_tongue_into_former_open_bounded_notch`.
The longitudinal web is the sole material owner. Two definition-generated web
relief cuts leave a 20-mm-high, former-thickness-wide tongue, connected to the
web at both X ends. The transverse former receives the tongue through an
open-in-Y but Z-bounded notch. It has three locating faces (inner, upper and
lower); it is not a full-height clearance channel.

The source placement map feeds both `PartInstance` placement and `PartFrame`.
Joint local coordinates are transforms of the placed world datum. DXF and STEP
therefore use the same `PartDefinition` operations as collision validation.
The obsolete v3 `mating_interfaces()` metadata contract is no longer an
acceptance oracle: v4.3 tests the actual placed tab solid, its BRep attachment
faces and its complementary receiver void instead.

## Accepted former/web sequence

1. Locate all formers on the datum jig.
2. Insert keel L from +Y, then keel R from -Y.
3. Insert side L from +Y, then side R from -Y.

All web paths are sampled at 0/25/50/75/100 percent using transformed BReps.
S3 and S4 pass with no feature-pair whitelist. Final tab/body overlap is zero;
tab occupancy is measured against the actual receiver subtraction volume.

## Limits and next pass

Minimum actual-boundary ligament is 6.0 mm (5 mm general, 6 mm at critical
stations). The 20-mm tongue retains only 38% of keel-web height or 22% of
side-web height locally. It is a dry-fit/registration feature, not credited as
a primary web-continuity load path; expected local failure is split/shear at a
relief root. Longeron geometry remains unresolved and is outside this result.

## Current independent-review disposition

**REJECT — preserve WIP.**  The current report's ligament and locating-face
metrics are not yet derived from the actual final profile boundary/contact
geometry.  In particular, the terminal +365 keel relief leaves only about
0.5 mm at the real web end, and port-side receivers retain a 0.2-mm lateral
air gap despite the metadata reporting zero alignment error.  The duplicated
active placement map also remains alongside the legacy `part_instances()`
map.  These are former–web material-joint blockers; no conclusion about the
deferred longeron subsystem is implied.
