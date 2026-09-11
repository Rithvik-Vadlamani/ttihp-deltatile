"""Require complete, clean final implementation metrics, including clock fanout."""
import csv
import json
import math
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/wokwi/final/metrics.csv")
with path.open(newline="") as stream:
    metrics = {}
    for row in csv.DictReader(stream):
        try:
            metrics[row["Metric"]] = float(row["Value"])
        except ValueError:
            pass  # Non-numeric metadata such as floorplan rectangles.

required_zero = [
    "design__lint_error__count", "design__lint_warning__count",
    "design__inferred_latch__count", "design__instance_unmapped__count",
    "synthesis__check_error__count", "design__power_grid_violation__count",
    "design__critical_disconnected_pin__count", "timing__unannotated_net_filtered__count",
    "design__max_slew_violation__count", "design__max_cap_violation__count",
    "design__max_fanout_violation__count", "timing__setup_vio__count",
    "timing__hold_vio__count", "timing__setup_r2r_vio__count",
    "timing__hold_r2r_vio__count", "route__drc_errors",
    "antenna__violating__nets", "antenna__violating__pins",
    "magic__drc_error__count", "magic__illegal_overlap__count",
    "design__lvs_error__count",
]
failures = []
for key in required_zero:
    if key not in metrics or metrics[key] != 0:
        failures.append(f"{key} = {metrics.get(key, 'MISSING')}")
for key in ("timing__setup__ws", "timing__hold__ws"):
    if key not in metrics or not math.isfinite(metrics[key]) or metrics[key] < 0:
        failures.append(f"{key} = {metrics.get(key, 'MISSING')}")
for key, value in metrics.items():
    if "__corner:" in key and any(key.startswith(base + "__corner:") for base in required_zero):
        if value != 0:
            failures.append(f"{key} = {value}")
if failures:
    raise SystemExit("Signoff metric check FAILED:\n" + "\n".join(failures))
print("Signoff metric check PASSED")
print(json.dumps({key: metrics[key] for key in (
    "timing__setup__ws", "timing__hold__ws", "design__instance__utilization",
    "design__instance__count", "design__instance__area",
    "design__instance__count__class:sequential_cell",
)}, indent=2))
