# LR1600 wing mass revalidation — 2600 g preliminary sensitivity

## Scope and disposition

**Disposition: PASS CONDITIONAL.** Existing LR1600 wing geometry and structural
concept are conditionally acceptable for a **2600-g preliminary design case**
without structural redesign. This is not a production release, MTOW change, or
ultimate-strength claim.

`config/aircraft.yaml` remains source of truth: `aircraft.target_mass_g` is
**2400 g** and `design_load_factor_g` is **4.0**. The 2600-g case is only an
in-memory override in the reproducible analyses. Airfoil, planform, washout,
dihedral, spar, joiner/socket, ribs, D-box and boom-attachment concepts are
unchanged; no automatic reinforcement was made.

Run:

```bash
./tools/cad-shell.sh scripts/analyze_wing_aero_mass_sensitivity.py
./tools/cad-shell.sh scripts/analyze_wing_mass_revalidation.py
```

Outputs: [aero JSON](../analysis/aero/mass_sensitivity_2400_2600.json),
[aero CSV](../analysis/aero/mass_sensitivity_2400_2600.csv), structural
[summary](../analysis/wing_mass_revalidation/summary.json), and
[comparison](../analysis/wing_mass_revalidation/comparison.csv).

## Aero revalidation

Existing direct XFOIL polars, the 40-station finite-wing stall solver and
`wing_drag_n` were reused. Wing-only drag excludes fuselage, tail, pusher,
gaps and full-aircraft CdA. Ncrit=5 direct-polar gaps remain, so realistic
stall values are engineering sensitivities rather than new strict stall roots.

| Metric | 2400 g | 2600 g |
|---|---:|---:|
| Wing loading, g/dm² | 66.67 | 72.22 |
| Required CL at 50 / 60 / 70 / 80 / 90 km/h | .553 / .384 / .282 / .216 / .171 | .599 / .416 / .306 / .234 / .185 |
| Clean finite-wing stall, km/h | 34.49 | 35.91 |
| Nominal realistic engineering stall, km/h | 35.05 | 36.48 |
| Conservative realistic engineering stall, km/h | 37.55 | 39.09 |
| 99%-of-best wing-only L/D band, km/h | 56–64 | 59–67 |

At 50 / 60 / 70 / 80 / 90 km/h, induced drag is .648 / .450 / .331 / .253 /
.200 N at 2400 g and .760 / .528 / .388 / .297 / .235 N at 2600 g. Total wing
drag is 1.083 / 1.000 / 1.075 / 1.279 / 1.534 N and 1.197 / 1.074 / 1.108 /
1.295 / 1.544 N respectively. The speed shift follows `sqrt(2600/2400) =
1.0408`; it is not a new aircraft optimum. No approved approach multiplier
exists; any future `Vapp/Vstall` policy must retain its multiplier, with all
stall-referenced speeds increasing 4.08%.

## Four-g structural revalidation

The existing design/limit interpretation and elliptic per-console distribution
are retained; no ultimate factor is introduced.

| Metric | 2400 g | 2600 g |
|---|---:|---:|
| Total / per-panel design lift, N | 94.144 / 47.072 | 101.989 / 50.995 |
| Root shear / root moment | 47.071 N / 15.982 N m | 50.994 N / 17.314 N m |
| 14×12 spar root stress / shear screen | 128.91 / 2.305 MPa | 139.65 / 2.497 MPa |
| Spar tip deflection, E=70 GPa | 38.36 mm | 41.56 mm |
| Spar tip deflection, E=110 GPa | 24.41 mm | 26.45 mm |
| Joiner stress / E=70-GPa centre deflection | 107.04 MPa / .083 mm | 115.96 MPa / .090 mm |

At 2600 g conservative spar-envelope tension/compression/shear screening SFs
are 2.506 / 2.148 / 14.016; nominal values are 4.297 / 3.580 / 24.027.
These are not measured allowables. Root ribs, longitudinal plates and their
configuration remain unchanged; their joint/load-path qualification remains
outstanding.

The E=70-GPa screen exceeds the existing 40-mm deflection STOP. No spar is
changed: qualification requires actual existing Ø14×12 spar **EI >=63.12 N
m²**, equivalent to **E >=72.73 GPa** for its present geometry. Measured EI
qualifies deflection only; it never replaces strength allowables.

The existing 1.25 vertical screen at 2600 g is 63.742 N / 21.642 N m; the
loaded panel in the existing 70/30 split is 71.391 N / 24.239 N m. They remain
sensitivity screens, not new qualification loads.

## Joiner, socket and D-box

At 2600 g, provisional socket screens are: carbon bearing 2.618 MPa (SF
5.729), hoop 16.728 MPa (SF 1.494), birch bearing 7.528 MPa (SF 1.993), birch
net tension 12.546 MPa (SF 1.594), and bond line .301 MPa. These are not
measured allowables; the representative tube/liner/birch/bond proof remains
mandatory.

The existing local socket rule is retained: `1.25 × root design moment` =
**21.642 N m**. Existing 250-mm torque arms require **86.57 N (8.83 kg
equivalent) each**. PASS criteria are unchanged: no slip, crushing, hoop
splitting, delamination or plate cracking, with residual displacement <=.10
mm. This is a socket proof only: do not make a 125% full-wing proof without
limit/ultimate classification and safety review.

The existing worst-|Cm|/lift-offset model at effective G=300 MPa gives:

| Tip twist, degrees | 70 km/h | 90 km/h | 100 km/h | 120 km/h |
|---|---:|---:|---:|---:|
| 2400 g | 1.046 | 1.642 | 1.995 | 2.814 |
| 2600 g | 1.057 | 1.653 | 2.006 | 2.825 |

The exact 2600-g root-equivalent requirement is 22.860 N m², so the practical
reinforced D-box qualification gate is **GJ >=22.9 N m²**. Existing `<=2° @
100 km/h` and `<=3° @120 km/h` gates are unchanged. This is not flutter
substantiation.

## Boom/root transfer, gates and limits

At y=230 mm, mass-dependent 4-g wing background section shear/moment become
32.587 N / 7.717 N m from 30.081 N / 7.123 N m. No new wing-background boom
limiter appears. Published boom/tail aerodynamic, yaw, handling and landing
loads are not scaled by 2600/2400 because their physical assumptions do not
automatically depend on MTOW.

The boom hardpoint remains not release-ready: X coordinate, clamp/fastener
geometry, bond area, bearing/net-section proof and representative mounted test
are TBD. No bolt or attachment geometry is inferred.

Required conditions are: existing spar EI >=63.12 N m² and <=40-mm proof
deflection; representative D-box GJ >=22.9 N m² and existing twist gates;
representative socket proof at 21.642 N m; and every existing dimensional,
strength-evidence, glue, mass and hardpoint gate. Re-run on actual MTOW,
article, geometry, or load-interpretation change. This sensitivity does not
release manufacture, maiden flight, or a changed MTOW.

The maintained material workflow's canonical 2400-g PASS is explicitly
**not transferable** to this 2600-g case: its E>=70-GPa, 19.977-N-m socket,
and 22.8-N-m² D-box gates are below the requirements above. Until these
2600-g-specific values are explicitly evidenced and recorded against the
revalidation artifact, its qualification status is
`UNQUALIFIED_PENDING_2600G_SPECIFIC_EVIDENCE`.

The 70/30 result is an asymmetric sensitivity only, not a proof-load schedule:
its 24.239-N-m loaded-panel moment exceeds the 21.642-N-m symmetric socket
proof, and it therefore cannot be claimed covered by that proof. It reduces
the provisional socket hoop/net SF screens to about 1.07/1.14 and needs a
separate asymmetric case classification before it could govern qualification.
There is no numerical local allowable model for root ribs, longitudinal plates
or their joints; these paths remain unverified/TBD and are covered only by the
existing representative proof and material/joint gates.

For audit, the 2600-g five-zone symmetric 100% full-wing schedule per console
is 12.898, 12.362, 11.212, 9.213 and 5.307 N at y=80, 240, 400, 560 and 720
mm respectively (1.315, 1.261, 1.143, .939 and .541 kg equivalent). It is a
100% current design/limit schedule, not the 125% socket proof.
