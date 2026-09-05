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

The instance-keyed `active_skeleton_placement_registry()` is the single
editable placement source. `PartInstance` is a computed compatibility view,
and `PartFrame`, JointDefinition transforms and pose checks use this registry.
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
S3 and S4 pass with no feature-pair whitelist. Final tab/body overlap is zero.
Tab occupancy is measured against the bounded final locating envelope inside
the actual open receiver cut, not the intentional lateral entry channel.

## Limits and next pass

The +365 keel contour was extended locally by 6 mm without moving a station.
Its final post-boolean BRep-edge measurement is 6.5 mm; regression recreates
the rejected 845-mm contour and detects its 0.5-mm bridge. Port datum Y=-68.8
was corrected to the actual XZ-extrusion mid-plane Y=-69.0, removing the
systematic 0.2-mm gap at its common source. The same edge algorithm also
found the prior 1.5-mm leading side-web bridge; a local 6-mm leading extension
now measures 7.5 mm. The report measures both web-root and receiver boundary
witnesses from final BRep profile edges; minimum residual ligament is 6.5 mm (5 mm general, 6 mm at critical
stations). The 20-mm tongue retains only 38% of keel-web height or 22% of
side-web height locally. It is a dry-fit/registration feature, not credited as
a primary web-continuity load path; expected local failure is split/shear at a
relief root. Longeron geometry remains unresolved and is outside this result.

## v4.3.1 independent-review disposition

**REJECT — preserve WIP.**  The +365 correction and port-datum correction are
real, but the all-joint boundary/contact evidence is still insufficient for a
release.  The current ligament scan omits some potentially nearer profile
boundaries (including diagonal relationships), so it is not yet a true minimum
distance to the post-boolean 2D boundary.  The contact report only aggregates
face pairs already within its contact tolerance and therefore cannot detect a
missing intended locating face; it also lacks a required port/starboard mirror
regression.  These are material-joint measurement/reporting blockers only.
Longeron geometry remains explicitly deferred.
