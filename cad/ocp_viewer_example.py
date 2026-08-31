"""Open this non-production example in VS Code with OCP CAD Viewer installed."""

from ocp_vscode import show

from cad.common.calibration_coupon import make_solid


# OCP CAD Viewer visualizes this existing calibration model; it does not export
# or change any project geometry.
show(make_solid(), names=["LR1600 calibration coupon"])
