# LR1600 Fuselage Skeleton & Longeron v4 gate record

**Status: NOT CUTTABLE — v4 WIP retained.**  This document covers only the
basic skeleton and four 5x3-mm carbon longerons.  Gear, nose, battery, wing,
motor and boom systems were intentionally outside the gate.

## Independent CAD gate result

The active set has 12 plywood definitions, 12 placed instances and 30 declared
former-to-web joints (16 keel and 14 side).  DXF and STEP extrusion both derive
from `PartDefinition` for these active parts.  Those facts do not establish a
physical joint.

The independent CSG check found all 30 former/web joints overlapping in their
final placements, totalling about 886 mm3.  The v4 collision report hid them by
whole-part-pair permission rather than by an identified tab engagement volume.
Former extrusion direction and web-slot placement leave half the former through
the web; keel joints additionally have a Z mismatch.

Discrete independent translation sampling also finds both keel webs and both
side webs colliding with installed formers through their claimed +X insertion
paths.  Therefore Method A fails at the web-installation steps, irrespective of
the declared sequence metadata.

## Longeron-specific blockers

- Lower carbon-to-keel contact is a line contact, with no physical bond area.
  Claimed continuous support and 2,520-mm2 bond area per lower rail are not
  geometry-derived.
- Former notches engage only 1.5 mm of the intended 3-mm stock because their
  placed Z is offset from the declared feature.
- Upper rails can translate in sampled poses, but with zero nominal clearance
  and only 2-mm wide side-web contact; the reported 1,740-mm2/rail area is not
  supported by the solid geometry.

## Required corrective geometry

1. Generate the real tab/notch contours from the same placed feature datum as
   the report, then cut the exact nominal engagement without a whole-part
   collision whitelist.
2. Reposition or orient the former extrusion and each web so tab/slot volume is
   feature-specific and the non-engaged solid volume is disjoint.
3. Model bottom-open 5(Y)x3(Z) lower saddles and top-open upper saddles at the
   actual longeron coordinates; calculate support/bond area from faces.
4. Implement every Method A pose as a translated CSG collision check against
   the already-installed subset.  Report minimum clearance, not a metadata
   PASS.

Until these items pass, no active skeleton part has earned
`PROTOTYPE CUTTABLE — SKELETON SUBSYSTEM ONLY` and no dry-fit laser prototype
should be cut.
