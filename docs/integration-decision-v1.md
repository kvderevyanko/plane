# LR1600 integration decision v1: forward battery bay

**Decision:** accept the extended forward fuselage and P60B rail as the
preliminary, reversible packaging baseline for the 2,600-g integration case,
subject to the structural and validation conditions below.  Use an external
nose limit of **X=-500 mm**, a 155 x 75 x 28-mm P60B study envelope, indexed
battery-CG travel **X=-382.5...-332.5 mm**, and nominal index **X=-370.0 mm**.
This is sufficient to proceed to a packaging/skeleton CAD study; it is not a
production-CAD freeze or flight release.  Wing geometry, wing structural
concept and the root-wing-LE datum are unchanged.

## Inputs and closure

The current unified central ledger uses a 503-g complete-pack estimate, a
398-g fuselage estimate with its revised centroid near X=-1.6 mm, and 202 g of
wheel gear.  Solving the longitudinal first moment for the configured MAC
targets gives:

| Target | CG X, mm | Required battery CG X, mm | Rail-end margin, mm |
|---:|---:|---:|---:|
| 24% MAC | 66.26 | -381.39 | 1.11 from forward limit |
| 25% MAC | 68.52 | -369.99 | 12.51 / 37.51 |
| 26% MAC | 70.78 | -358.58 | 23.92 / 26.08 |
| 28% MAC | 75.30 | -335.77 | 3.27 from aft limit |

Thus 25% MAC is mathematically reachable without ballast, and the required
24--28% span is 45.6 mm inside the 50-mm rail. The 1.1/3.3-mm end margins are
not robust to as-built mass/moment error. They approve only the current
central-ledger packaging baseline.  Before cutting a production tray, repeat
the solver with weighed components and retain space in the skeleton for rail
or stop revision; do not trade primary structure for extra travel.

The union of pack positions is X=-460...-255 mm.  At the forward setting,
the X=-500 outer limit leaves 40 mm ahead of the estimated pack envelope for
a 3-mm tied stop, insulation and a sacrificial bumper/crush space.  This is a
preliminary packaging allowance, not an impact-qualified battery enclosure.
The 230 x 110-mm clear top opening is adequate as a geometric reservation at
both stops: move the pack to a chosen index, isolate and disconnect it, then
lift vertically. The aft pack end is X=-255 at the aft stop, leaving about
13 mm to the X=-242.5 hatch edge. Mock up the actual pack, connector bend
radius, straps, latch and hands/tool access before fixing hatch geometry.

## Structural resolution

The extended nose is coherent only as a primary battery-box cantilever, not as
skin-supported packaging.  The earlier statement that the four primary
longerons run only from X=-170 was incompatible with a forward stop near
X=-475.  The resolved skeleton extends the lower longerons and continuous side
sill/shear path from the forward battery stop region (no later than X=-475)
through the X=-55 wing-forward shear frame and central gear/wing box.  Route
the upper members around the hatch perimeter with closed end rings and local
diagonal shear webs; the removable hatch and foam/composite skin receive no
primary bending or torsion credit.  The forward and aft battery stops, both
20-mm straps and rail attachments must feed this same box in double shear.

For scale, the pack alone at the forward rail end produces about **29.6 N** at
the stated 6-g retention case.  Its bending contribution about the X=-55 frame
is about **9.9 N m operational** and **14.9 N m proof** at factor 1.5.  Nose
structure, FPV/optional camera and local landing/obstacle loads are additional;
these numbers are not the complete nose-box design load.  Coupon allowables
and a representative assembled-box proof are required before manufacture.

## Handling and service trade

At the 25%-MAC target, the pack centre is about 446 mm ahead of CG.  A point
mass screen gives approximately **0.100 kg m2** battery pitch inertia about CG
(about 0.101 kg m2 including the pack's own 155-mm longitudinal extent).  The
same pack at X=-330 would contribute about 0.080 kg m2, so the accepted CG
solution adds roughly **0.020 kg m2** from the battery alone.  This is a real
pitch-response and rough-landing penalty, but preferable to ballast or moving
servos/electronics to the tail.  Keep all other heavy equipment near CG and
make the nose bumper/lower skid replaceable.

Service access remains acceptable if the battery has a guarded disconnect
reachable before unlatching, positive indexed stops, two independent retained
straps, and no servo horn or high-current cable crossing the vertical removal
path.  A jammed or deformed forward stop must be replaceable without removing
the wing or opening the central gear box.

## Margins and gates

- The 155 x 75 x 28-mm pack and 503-g mass are estimates, not a measured pack
  drawing or an accepted cell-interconnect design.
- Demonstrate at least 44.4 N pack retention in each principal direction with
  an inert dummy, then inspect rail indexing, longeron joints, stop bearing,
  hatch-ring distortion and removal.
- Proof the combined nose box using the complete nose mass/load case, not only
  the battery contribution calculated above.
- Recompute wheel, ski and Full-HD configurations from weighed moments.  If
  24% or 28% remains an operational requirement after weighing, enlarge or
  relocate the rail deliberately; the present end margins do not cover mass
  uncertainty.
- Confirm actual-pack clearance, thermal path, connector routing and at least
  the intended sacrificial nose deformation space before production fuselage
  CAD.

Within these boundaries, the X=-500 / X=-382.5...-332.5 architecture is a
technically coherent preliminary solution to no-ballast 25%-MAC closure.  It
does not justify changing the wing, weakening fuselage hardpoints, or calling
2,600 g a final released flight mass.
