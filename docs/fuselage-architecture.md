# LR1600 Fuselage Architecture v1

**Status:** preliminary structural architecture and packaging estimate, not production CAD, a measured mass, material allowable, or flight release. All stations use the wing-root-LE datum; +X is aft. The 2,600-g integration case is used. Wing geometry and its structural concept are unchanged.

## Selected architecture and envelope

Selected: a repairable plywood-frame/four-longeron semi-monocoque fuselage. Laser-cut internal structure, local birch hardpoint boxes and continuous carbon longerons carry load; removable foam/light-composite shell, hatches, printed camera bezel and printed cable guides are secondary. None of those secondary parts receives wing, boom, motor, battery or landing-load credit. A 14-g lower skid is sacrificial and replaceable.

Preliminary outer envelope is **X=-500 to +410**, W=**180** (Y=+/-90), H=**190** (about Z=-95...+95); a replaceable motor plate reaches X=+430. The 910-mm body prioritises serviceability and no-ballast CG closure over minimum frontal area. This nose length is an explicit pitch-inertia penalty, not an aesthetic choice.

| Station X | Function | Primary material |
|---:|---|---|
| -285 | nose-gear / front lower-keel **partial U-web** station | 2-mm birch; printed camera bezel secondary |
| -170 | lower-keel / battery-side-rail **partial U-web** station | 2-mm birch/local non-ferrous fasteners |
| -55 | wing-forward shear frame | 3-mm birch web, 2-mm flanges |
| +65 | wing-rear shear frame / gear-box front | 3-mm birch |
| +130 | main-gear reaction frame | 3-mm birch double-shear box |
| +200 | gear-box rear / equipment frame | 3-mm web, 2-mm flange |
| +285 | boom/motor torque web | 3-mm birch/carbon-wrap interfaces |
| +365 | motor plate / boom-clamp frame | 3-mm birch and replaceable plates |

Intermediate shape formers are 2-mm birch. The **two lower 5x3-mm pultruded-carbon longerons** (or substantiated straight-grain spruce equivalents) run continuously from X=-475 to +365, tying the forward battery-stop/keel box into the wing box. The upper pair runs X=-170 to +365; 2-mm birch side rails and the hatch perimeter are primary tension/shear members around the battery opening. Thus no battery stop discharges into unsupported shell. Exact section, supplier data, scarf detail and adhesive overlap remain coupon/CAD gates. Sand laser-charred structural bond faces to sound wood, abrade and de-dust. Nominal CAD contains no kerf compensation; a measured-kerf coupon controls finished slots.

## Primary paths

| Interface/event | Primary load path | Never primary |
|---|---|---|
| Wing attachment | wing root spar/D-box hardpoints -> paired 3-mm saddle/shear frames at -55/+65 -> longerons and central box | foam, hatch, one former, printed saddle |
| Twin booms | provisional indexed +285/+365 alignment and motor-bridge stations; final primary bending transfer remains a dedicated boom/wing-interface CAD and proof gate | adhesive-only tube joint, foam, one bolt |
| Main gear | GFRP leg -> +65/+130/+200 double-shear box -> lower longerons and upper closure web | shell, foam, printed fairing |
| Nose gear | strut bearing tube -> -285/-170/-55 lower-keel box -> lower longerons | camera tray/nose shell |
| Motor | fixed 25-g fuselage cross-member/base -> paired shear keys -> boom clamp frames and central torque web; separate replaceable plate/adapter then bolts to base | printed tab, thin tongue, adhesive alone |
| Battery | broad 2-mm cradle -> 3-mm end stops/two straps -> lower longerons and hatch-perimeter side rails | cells, shrink-wrap, hook-and-loop alone, hatch |
| Body bending/torsion | four longerons carry bending; plywood frames and local diagonal 2-mm webs close central box | foam shell alone |

Boom axes remain Y=+/-230, outside the 180-mm body. The fuselage supplies a central bridge and clamp frames, not a narrow wall carrying the full 460-mm separation. Use two indexed stations >=80 mm apart, non-crushing liners and two anti-rotation shear features per boom. Fixture axes/tail during bonding. Preliminary targets: each boom axis +/-0.5 mm at both clamps, station separation +/-0.5 mm, and differential tail incidence <=0.25 deg after proof.

## Battery and service access

The P60B 6S1P integration envelope is **155 x 75 x 28 mm**, a feasible two-cells-long by three-cells-wide 21700 arrangement including interconnect, insulation, connector exit and modest assembly allowance; it is not a verified pack drawing. The unchanged indexed **50-mm** rail is X=-382.5...-332.5. With the fixed-nose gear ledger, required pack centres are -384.78/-373.40/-362.03/-339.27 mm for 24/25/26/28% MAC respectively. The X=-370.0 nominal reference yields 25.30% MAC; exact 25% remains reachable at X=-373.40, while exact 24% is 2.28 mm ahead of the rail. The complete moving pack envelope remains X=-460...-255. Final measured-CG release is mandatory.

Use a top hatch with a provisional **230 x 110-mm clear opening** (approximately X=-472.5...-242.5), two mechanical latches and a secondary retained strap. It fully clears the pack at both rail limits. No full-width former crosses this opening: the -285/-170 stations are lower-keel partial U-webs only, while the birch perimeter/side rails close the load path. The pack lifts up after guarded disconnect; it does not pass servo horns/high-current wire. Full-area non-compressive cradle, 3-mm stops and two 20-mm straps take the 6-g retention assumption with 1.5 proof: a 503-g pack needs **29.6 N operational / 44.4 N proof per principal direction**. Treat each complete stop/strap path as capable of the full proof load rather than claiming a failed path shares it. At nominal X=-370.0 the battery CG ledger moment is **-186,110 g mm**. Proof with an inert dummy in six directions.

FPV occupies a protected lower-front cassette centred at X=-215, Z=+5, vertically separated from the pack. Optional 25--60-g HD camera uses a removable tray centred at X=-175; its break-away printed cradle is not a nose-impact path. FC/equipment trays are X=+80...+210 with an upper service hatch. GNSS uses the non-ferrous upper support at X=-105, Z=+95; preserve a compass keep-out from the nose strut and high-current wiring.

## Materials and mass

| Group | Central mass g | Function |
|---|---:|---|
| 2-mm frame, keel, shear webs | 70 | primary shape/shear/torsion |
| Carbon longerons/local wraps | 34 | primary bending continuity |
| 3-mm birch wing/gear/boom hardpoints | 70 | bearing/clamp/concentrated reactions |
| Foam/light-laminate shell and extended-nose reinforcement | 62 | enclosure only; local bumper support |
| Battery cradle, rails, hatch, straps/latches | 55 | retention/service |
| Fixed motor base/cross-member | 25 | fuselage-side primary interface; excludes removable plate/adapter |
| Equipment/camera trays | 18 | secondary support |
| Replaceable skid/bumper | 14 | ground protection |
| Adhesive, inserts, fasteners, chafe allowance | 50 | installation allowance |
| **Fuselage structural group, no removable gear** | **398** | **design estimate** |

The single point submitted to the current CG ledger is **398 g at X=-1.6 mm** (moment -636.8 g mm), not measured. The removable motor plate/adapter/positive prop-retention group is a separate **50-g propulsion-ledger item** and is explicitly excluded from this 398-g fuselage group; only its fixed 25-g base/cross-member remains here. Plausible mass interval is 365--440 g, driven by plywood density, carbon section, adhesive uptake, latches and proof outcome. Do not remove 3-mm gear/boom boxes or continuous longerons only to meet target mass. Expected early failures: plywood bearing/splitting, unprepared-bond peel, local carbon crushing at clamp, gear-leg root delamination and motor-plate bolt bearing; global foam-shell failure must remain non-critical.

## Motor and cooling interfaces

The fixed base accepts a separate replaceable 50-g plate/adapter/positive-retention group for the current 50-mm-diameter, 70-mm installed-length, <=180-g motor class without locking an SKU. The preliminary proof envelope is **15.1 N axial thrust** (1.5 x a 10.1-N screening thrust), **1.26 N m torsion** (1.5 x a 0.84-Nm screening torque), and **0.64 N m motor-inertia bending moment** (4 g on 180 g at a 90-mm CG offset). These are bounded design screens, not measured motor data. Before release, proof selected hardware to measured static thrust, 1.5 times measured torque and 4-g motor inertia at true CG offset; inspect plate twist, bolt bearing, clamp slip, carbon crushing and prop alignment.

Provide a baffled lower-front inlet for battery/FC, a protected side inlet at X=+190 for ESC/regulator flow, and upper/aft outlets at X=+275...+340. Outlet free area >=1.25x inlet after guards. Recessed mesh is allowed only when temperature testing shows acceptable pressure loss; exits must not ingest grass. Use grommets, strain relief and removable covers at all wire/antenna penetrations.

## Release gates

1. Coupon actual birch bearing/net-section, carbon clamp liner and prepared bond, then proof a representative wing/boom/gear bay.
2. Proof installed main/nose hardpoints vertically and laterally to `landing-gear.md`, with no permanent set, slip, cracking, delamination or incidence loss.
3. Proof battery cradle/rails/stops/latch in six directions; repeat removal after proof.
4. Demonstrate dummy-prop clearance at maximum compression, 20-mm rut and 8-deg tail-low attitude.
5. Enter weighed parts and measured CG before calling the integration case a flight release.
