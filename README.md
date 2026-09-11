# Tiny Tapeout accelerator exploration

Proposed direction: **DeltaTile**, a 2×2 signed INT4 systolic accelerator that retains four scores and updates them from changes in input features.

Status: RTL and a pin-level verification suite are implemented. Physical implementation and submission are in progress. One-tile fit, timing, power, application accuracy, and final purchase cost remain unverified until reports are available.

- [Design proposal and tapeout milestones](docs/deltatile-proposal.md)
- [Executable arithmetic model](model/delta_reference.py)
- [Chip interface and bring-up vectors](docs/info.md)
- [RTL](src/project.v) and [pin-level tests](test/test.py)

Run the model checks with `python3 model/delta_reference.py` from this directory. These checks validate arithmetic and workload counts, not clock-level behavior or silicon feasibility.

For RTL simulation, install `test/requirements.txt` in a virtual environment, then run `make` in `test/`. The simulator checkout and virtual environment must be in paths without spaces. The same tests run on the gate-level netlist in the official IHP26b GDS workflow. The clock target is 10 MHz.

For a workspace path containing spaces, run `python3 scripts/run_local_tests.py --venv /path/without/spaces/venv`. This copies the sources to a temporary build directory and preserves the result XML and waveform in `artifacts/local-tests/`.

`host/deltatile.py` plans dense/incremental frames, splits large corrections, checks readback, and accepts a caller-provided bus transport. Host packet plans are exercised against the chip by the fifth Cocotb test.

Template provenance: TinyTapeout/ttihp-verilog-template at `6598bef4d3159f19fe471a2a2225df52e6f5ad25`. The original template license is retained in LICENSE. RTL is original to this project.
