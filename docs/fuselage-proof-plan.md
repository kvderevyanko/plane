# LR1600 Fuselage Prototype v1 — proof articles and gates

**Status:** required physical proof plan; no test result is implied.  The
2,600-g integration design case is the source-of-truth mass case.  This plan
does not validate wing structure, unselected boom tubing, the selected motor,
or a full aircraft.  Use a guarded fixture, calibrated/known load, a catch
where falling mass is possible, photos and the [test record sheet](test-record-sheet.md).

## General method

Use the actual CAD article, actual birch/carbon/fasteners/adhesive and actual
assembly preparation.  Test in 25/50/75/100/proof increments with a 60-s dwell
at each unless a fixture-specific instruction is safer.  Measure initial and
residual deflection/alignment after unloading.  Stop immediately for crack,
split, audible fibre failure, adhesive-line opening, permanent set, hole
ovality, bolt/pin movement, clamp slip, delamination or a change in indexed
heading.  Shields are mandatory around carbon/GFRP, moving levers and hanging
weights; no person stands in the load line.

Pass means the full stated proof load is held with no damage, no permanent set,
no slip and no alignment loss beyond drawing tolerance.  Passing is a
prototype gate, not an ultimate strength allowable or production approval.

## Required representative articles

| ID / article | Representative content | Applied proof / method | Required observations and likely first failure |
| --- | --- | --- | --- |
| `FG-MAIN-ROOT-01` | X=+65…+200 `FUS-GEAR-DOUBLER-*`, `FUS-GEAR-SPREADER-*` and `FUS-GEAR-CLAMP-LAND` cassette; 2-mm closure webs, lower longeron segments, actual spreader/bolts and a GFRP leg root. | **121 N vertical** on one main; separate **35 N lateral** and **35 N longitudinal** at the wheel/leg reaction line. Apply through a rounded wheel/axle fixture, not directly to one plywood edge. | Leg-root delamination/yield, birch bearing/net-section split, bolt slip, adhesive peel, longeron disturbance and residual gear alignment. |
| `FG-NOSE-INDEX-01` | X=-285 lower-keel box, `FUS-NOSE-INDEX-BLOCK`, two `FUS-NOSE-INDEX-DOUBLER` parts, actual strut tang/capture hardware and an accurate fork/strut dummy or real part. | **60 N vertical**, then **35 N lateral** and **35 N longitudinal** with the tang captured in its 12-mm key. | Key-face crush, plywood split, capture-bolt migration, yaw slip and residual straight-ahead heading. Clamp friction is not credited. |
| `FG-BATTERY-RET-01` | Full rail/cradle, `FUS-BAT-FWD-STOP`, `FUS-BAT-AFT-STOP`, both `FUS-BAT-STRAP-ANCHOR-*` pairs, hatch opening and inert 503-g dummy. | **44.4 N** in +X, -X, +Y, -Y, +Z and -Z, one direction at a time. Cycle pack removal/reinstallation after proof. | Stop crush/splitting, rail pull-out, strap-anchor tear-out, buckle/fastener release, hatch interference or connector misuse. Each independent stop/strap path must demonstrate its full assigned reaction. |
| `FG-BOOM-CLAMP-01` | One `B285`/`B365` clamp frame segment, the actual tube, actual compliant liner, clamp hardware and a representative boom stub. | Establish safe tightening torque first.  Apply axial slip, transverse and torsion screens derived from the coupled boom load release analysis; repeat at least ten install/remove cycles. | Carbon local crush, liner creep, frame split, bolt bearing, clamp slip and lost angular index.  **No numerical boom structural approval exists until tube data/load case is closed.** |
| `FG-MOTOR-PLATE-01` | Fixed cross-member, `B365` support, actual removable plate/adapter, selected or accurate motor mass/CG and bolts/shear keys. | Current provisional screen: **15.1 N axial**, **1.26 N m torsion**, **0.64 N m inertia bending**.  Replace with selected-motor measured static thrust, 1.5x measured torque and 4-g inertia at actual offset before release. | Plate twist, bolt bearing, key slip, fastener loosening, carbon crush and prop-axis movement. |
| `FG-CARBON-BIRCH-01..03` | Actual 5 x 3 longeron stock bonded to laser-cut/prepared birch with the same overlap, adhesive and cure as fuselage. | Slow guarded lap/peel/shear comparison, three repeats.  Record maximum applied load and failure mode; do not derive a generic allowable. | Adhesive/carbon interface failure, plywood delamination or peel at a square termination.  Adhesive/carbon-interface failure fails the preparation gate. |
| `FG-TAB-SLOT-2/3` | The actual 2-mm and 3-mm material, representative tab/slot teeth and corner relief. | Laser-process calibration / repeated dry insertions, not a structural qualification. | Finished fit, tab damage, char, slot ovality and need for downstream kerf setting. |

The existing plywood bearing and carbon-to-birch coupons in
[material-testing.md](material-testing.md) remain prerequisites; these fuselage
articles add the real load path and assembly geometry they cannot represent.

## Full skeleton proof sequence

After the relevant representative articles pass, proof the dry structural
skeleton before light shell completion:

1. Install the instrumented/marked dummy battery, gear interfaces, boom/motor
   alignment fixtures and wing-side gauges.  Record initial X/Y/Z datums,
   diagonals, motor axis and indexed nose heading.
2. Carry out main and nose hardpoint proof as installed assemblies.  Use a
   fixture that follows the real reaction line and supports the fuselage at
   its intended wing-interface/datum locations; do not make the foam shell a
   reaction member.
3. Apply battery retention proof in all six directions; remove/reinstall the
   dummy through the hatch afterwards.  A retained battery that cannot be
   serviced is a failure of this prototype objective.
4. Fit the non-rotating 13-in prop disk and run the compression / 20-mm-rut /
   8-degree tail-low clearance check.  This validates geometry only; it is not
   a rotating-prop test.
5. Verify boom alignment under the current fixture.  Coupled wing/boom bending
   proof is a separate release gate and is not inferred from a static
   clamp-fit check.
6. Inspect every bond line, longeron, hardpoint, clamp, gear key and fastener;
   weigh the bare skeleton and each removable group.  Enter measured mass and
   station moments in the hardware ledger workflow, then recompute CG.

## Proof closure criteria and blockers

The prototype may proceed from cut parts to a dry structural assembly only
after tab/slot calibration and the battery removal sweep are demonstrated.  It
may receive the representative loaded interfaces after the associated articles
pass.  It is **not** production-ready until all of the following are closed:

- actual birch density/thickness, bearing/net-section and carbon-birch bond
  evidence;
- selected GFRP laminate thickness/lay-up, root holes and fatigue/impact
  behaviour;
- main root and fixed nose-index proof with residual alignment recorded;
- selected boom tube OD/wall/allowables, non-crushing liner torque and coupled
  wing/boom bending proof;
- selected motor/adapter measured thrust, torque, vibration and motor-plate
  proof;
- six-direction battery proof, repeated wing-on service removal and measured
  pack/structure mass and CG;
- physical prop-clearance, cooling/EMI and installed avionics service checks.

Until then, all fuselage flight hardware and full assembly remain
`NOT RELEASED`; only explicitly labelled plywood parts and jigs are
`PROTOTYPE CUTTABLE` / `TOOLING`.
