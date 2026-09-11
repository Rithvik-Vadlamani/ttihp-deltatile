# DeltaTile design signoff

**Design package verified; fabrication submission and silicon validation remain outstanding.**

Verified implementation revision: `72cf3db7bd78a53d63e1f8e8d39cbff5dc5a253c`.
Target: Tiny Tapeout IHP26b, one digital tile, `tt_um_rithvik_deltatile`.

## Evidence

- [Physical build, strict metric check, gate-level simulation, and Tiny Tapeout precheck](https://github.com/Rithvik-Vadlamani/ttihp-deltatile/actions/runs/34581705980): passed.
- [RTL, arithmetic reference, and host tests](https://github.com/Rithvik-Vadlamani/ttihp-deltatile/actions/runs/34581706028): passed.
- [Official datasheet build](https://github.com/Rithvik-Vadlamani/ttihp-deltatile/actions/runs/34581706006): passed. All four pages rendered and visually checked; final rendered pages are identical to those inspected.
- Downloaded implementation `src/project.v` and `src/config.json` match the verified source byte for byte. The submission's `commit_id.json` identifies the same revision and physical workflow.

| Item | Result |
| --- | --- |
| Process | IHP SG13G2 |
| Flow | LibreLane 3.0.5 |
| PDK revision | c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c |
| Tile size | 202.08 x 154.98 micrometers, 1x1 |
| Clock target | 10 MHz (100 ns period) |
| Reported standard-cell utilization | 56.4103% |
| Synthesized cell area | 13,091.0472 square micrometers |
| Synthesized cells | 990, including tie cells; not NAND-equivalent gates |
| State bits / sequential cells | 87 |
| Clock buffers after clock-tree synthesis | 31 |
| Worst setup slack across reported corners | +58.9964 ns |
| Worst hold slack across reported corners | +0.1093 ns |
| Setup / hold / fanout / slew / capacitance violations | 0 |
| Routing DRC / Magic DRC / antenna violations | 0 |
| LVS errors / critical disconnected pins | 0 |
| RTL and routed-netlist tests | 5 passed each, no failures or skipped tests |
| Host validation tests | 13 passed |
| Independent arithmetic checks | 4,096 exhaustive cases; 10,000 randomized and 100 extreme matrix updates |

The independent Tiny Tapeout precheck passed all ten reported checks, including KLayout SG13G2 DRC, geometry, pin labels, pin placement, boundary, layers, cell names, analog-pin checks, and Verilog syntax. Its full report is included with the release evidence.

## Timing assumptions and reviewed warnings

The official flow uses its generic SDC with a 100 ns clock, 20 ns input/output delays, 0.006 pF output load, 0.25 ns clock uncertainty, 0.15 ns clock transition, and 5% timing derating. STA covers the reported nominal-parasitic fast 1.32 V/-40 C, typical 1.20 V/25 C, and slow 1.08 V/125 C corners. These are implementation checks under the supplied flow assumptions, not a measured silicon maximum frequency.

The first layout had a clock-root fanout of 16 against an 8-load library limit. The final configuration uses 20-micrometer clock-buffer spacing, and the strict signoff script verifies zero fanout violations at every reported corner. No fanout constraint was relaxed.

The flow still emits standard environment/PDK warnings: generic SDC fallback, power terminals ignored by signal-oriented operations, unsupported LEF enclosure annotations in the router, no configured long-wire threshold, and no top-level supply locations for IR-drop analysis. Four unused bidirectional input paths have no gate connection. Main-flow KLayout DRC is disabled by the official template, but the separate Tiny Tapeout KLayout precheck passes. The full warning log is retained. No measured power, board-level signal integrity, or IR-drop claim is made from these reports.

## Release and remaining work

The release package contains GDS, OASIS, LEF, routed Verilog, extracted SPEF, flow/PDK metadata, source, command documentation, the datasheet, a layout preview, test reports, and checksums. The source revision above is the fabrication candidate; later documentation-only commits do not change that candidate.

No Tiny Tapeout project allocation, accepted submission, or fabrication purchase has been recorded. The portal displayed an IHP26b deadline of September 21, 2026 at 3:00 p.m. Central when inspected on September 11. Browser GitHub sign-in is required to continue. Repository access must be suitable for Tiny Tapeout when submitting; the development repository is currently private.

The calculator displayed EUR185 for one IHP digital tile, one discounted individual devkit, and shipping. Discount eligibility, availability, exchange rate, and any destination taxes must be checked at purchase; this is not a confirmed USD200 checkout total. Fabrication and delivery occur after an accepted paid submission. The MicroPython bring-up script is prepared against the official firmware API but awaits real hardware. Sensor classification accuracy and system energy benefits have not been demonstrated.
