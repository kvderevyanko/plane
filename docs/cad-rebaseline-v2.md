# LR1600 CAD integration rebaseline v2

This is a reference-layout update only.  It does not alter wing geometry and
does not release an external fuselage skin, landing gear, skis or linkages for
manufacture.

## Typed rough-field reference

The preferred pusher integration is a 13×10 pusher, with propeller/motor axis
at `Z=+50 mm`, propeller plane `X=430 mm`, static ground plane `Z=-270 mm`,
and the two main wheel contact stations at `X=125 mm`, `Y=±175 mm`. Main wheels
are Ø100 mm and the nose wheel is Ø75 mm. These are preliminary packaging
points, not a selected wheel, leg or steering mechanism.

The supplied structural screen records 13-in tip clearance as 154.9 mm static,
137 mm with 18-mm compression, 93 mm at 8-degree tail-low stance, and 69 mm
in the full rough case (rut plus tolerance). The last case exceeds the current
60-mm minimum study goal. The 14-in propeller remains secondary: it requires
taller gear and a separate boom/clearance proof.

The clearance relation retained for checking is:

```text
Zaxis − (Xprop − Xmain) sin(theta) − compression − rut >= Rprop + Cdynamic
```

The aero conservative preliminary screen used 10 degrees and 20 mm combined
compression/rut and gave a required static axis height of about 307 mm above
ground for 13 in.  The structural integration screen supersedes that for the
current layout with an explicit 8-degree/15-mm/20-mm-plus-5-mm-tolerance case.
Both assumptions remain in the record; do not silently exchange one for the
other when changing gear geometry.

## Structural and actuation markers

The master layout marks, but does not draw, two main hardpoint points at
`X=125, Y=±175, Z=-60 mm`. The intended load path is 3-mm birch double-shear
faces with a 2-mm web and continuous carbon longerons.  Seasonal skis pivot
on the retained wheel axles and require +20/-5-degree pitch freedom; ski
dimensions and retainers remain TBD, so no invented ski solid is rendered.

Elevator and both independent rudder servos relocate to `X=110 mm`.  Layout
routes are reference lines to the typed tail stations for one 610-mm elevator
and two 650-mm rudder 3-mm-OD/1-mm-ID carbon pushrods, supported at no more
than 200-mm intervals.  Horn geometry, guide count, buckling, backlash,
service access and measured linkage mass remain validation gates.

## CAD gate

The current geometry proves only that the stated rough-field clearance screen
can be represented consistently in the aircraft datum. It does not prove the
long forward battery removal route, actual hardware envelopes, ski dimensions,
wheel-leg load proof or final boom/motor joints. These remain production-CAD
gates.
