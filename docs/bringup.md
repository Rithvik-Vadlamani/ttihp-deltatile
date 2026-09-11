# Bring-up procedure

Hardware execution is pending fabrication. The steps below are prepared against the official [Tiny Tapeout demo-board firmware](https://github.com/TinyTapeout/tt-micropython-firmware) API at commit `d485c7a9986336024e35d790568fca33be1c5665`.

1. Use the board and firmware compatible with the shuttle containing this project. The project name will only appear in the shuttle index after integration; there is no assigned project number yet.
2. Copy `host/deltatile_bringup.py` onto the board's MicroPython filesystem as `deltatile_bringup.py`.
3. Connect through its REPL. Select the project using the firmware's shuttle selector. Ensure external hardware does not drive the upper four bidirectional pins or conflict with the demo board's input drivers.
4. Run:

```python
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
tt = DemoBoard.get()
tt.mode = RPMode.ASIC_RP_CONTROL
tt.shuttle.tt_um_rithvik_deltatile.enable()
import deltatile_bringup
deltatile_bringup.run(tt)
```

Expected scores: `[[12, -3], [-8, 2]]`, followed by `[[16, -4], [-8, 2]]`. The script clocks slowly, supplies two reset edges, sets host bidirectional output enables to `0x0f`, and leaves STROBE low after each command. Its use of `clock_project_once` is for functional bring-up, not a throughput measurement.

For full workloads, `host/deltatile.py` provides a desktop-Python frame planner and `run_plan(exchange, plan)`. A transport must present one command/data pair per rising edge and return the settled result/status. Use `previous=None` after reset, changing models, or any transport uncertainty. Only retain a previous feature matrix after its full frame has passed readback verification.

Before claiming silicon performance, compare the software model and physical chip on dense matrices, delta transitions, negative extremes, reset/abort tests, and clock sweeps within the signed-off limit. Before claiming an energy benefit, separate ASIC consumption from board/host overhead and measure both using controlled workloads. The synthetic traffic report does not establish either power or classification accuracy.
