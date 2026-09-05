# LR1600 former–web convergence v4.2

## Scope and disposition

This pass covers only the twelve active plywood instances that form the basic
former–web skeleton: eight transverse formers, two keel webs and two side
webs.  Carbon longeron saddles, carbon support and bond geometry, and every
other fuselage subsystem are explicitly deferred.

`JointDefinition` is the authoritative source for all thirty active joints.
It defines a placed world datum and derives each participant's local profile
operation through its explicit `PartFrame`; the resulting `PartDefinition`
profiles remain the common source for DXF, STEP extrusion and collision solids.
The terminal keel profile is locally extended from 843 to 845 mm so the last
receiving operation remains inside the actual contour.  This is a local joint
contour change, not an aircraft-station change.

## Selected dry assembly order

1. Locate all transverse formers on the datum jig.
2. Insert the port keel web laterally from +Y through its open former notches.
3. Insert the starboard keel web laterally from -Y through its open former notches.
4. Insert the port side web laterally from +Y through its open former notches.
5. Insert the starboard side web laterally from -Y through its open former notches.

The receiving notches are open at the respective former sides and extend the
web height, avoiding the rejected v4.1 long closed-slot threading.  The
v4.2 assembly report checks transformed BReps at 0, 25, 50, 75 and 100 percent
of each motion; no whole-part pair exemption is used.

## Acceptance boundary

This document does not award any longeron structural or production credit.
The next pass must independently repair and prove lower/upper longeron saddle,
clearance, finite contact-area and support-continuity geometry.

## Current independent-review disposition

**REJECT — preserve WIP.**  The current CSG no-collision result is not a
former–web joint acceptance: independent review established that the
full-height former receiving operation removes every declared former tab.
Consequently the 30 declared metadata tabs have zero material occupancy in the
actual placed former solids.  The next correction must generate complementary
material tab and receiving-void geometry from each `JointDefinition`, then
repeat the profile, final-pose and insertion gates.  It must not treat the
current zero-overlap report as a dry-fit release.
