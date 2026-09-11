# DeltaTile: a small accelerator for changing sensor features

Architecture proposal, 2026-09-11. This records the original rationale. The implemented pin/cycle contract is in [info.md](info.md), which supersedes tentative interface choices below. Physical signoff status is tracked separately; parameters here are not measured results.

## Recommendation

Build a conventional, independently testable 2×2 signed INT4 systolic array first. Retain its four accumulators between transactions so a host can apply exact corrections to previous results. Demonstrate dense recomputation and incremental updates on the same sensor feature sequence, with identical final scores.

The intended application is two sensor feature vectors evaluated against two programmable linear class scores. A desk vibration or gesture demo is a candidate; dataset selection, training, quantization, and accuracy measurement are still required. This is a linear inference primitive, not a complete wake-word recognizer.

## Creative directions considered

| Direction | Distinguishing experiment | Main cost or risk |
| --- | --- | --- |
| Zero-aware dense array | Disable unnecessary arithmetic on zero products | Operand-isolation overhead may exceed savings at this size |
| Variable-precision serial array | Compare area and latency at 2-bit and 4-bit precision | More control logic and a more complex verification space |
| **Incremental array (recommended)** | Reuse previous scores; send only changed feature contributions | Host bookkeeping, synchronization, and worst-case correction traffic |

Incremental neural computation is established research; we should not claim invention of temporal sparsity. Related work includes [Delta Networks](https://proceedings.mlr.press/v70/neil17a.html) and [EdgeDRNN](https://arxiv.org/abs/2012.13600). Our proposed contribution is a constrained implementation and measured tradeoff study with exact integer updates. Tiny Tapeout already lists a [Tiny TPU Systolic Array](https://www.tinytapeout.com/chips/ttgf26a/tt_um_bgao43) and [Tiny Ternary Tapeout](https://tinytapeout.com/chips/tt09/tt_um_tiny_ternary_tapeout).

## Arithmetic contract

Let X contain two rows of K sensor features and W contain K rows of two weights. Compute C = XW, producing four scores. Start with K ≤ 16, no bias, and signed two's-complement INT4 operands in [-8, 7].

When W stays fixed:

`C_new = C_old + (X_new - X_old) W`

Only exactly unchanged quantized features are omitted. There is no approximate threshold in version 1. If weights, feature scaling, or model identity change, clear and recompute all scores.

Four signed 12-bit accumulators are proposed. An individual product lies in [-56, 64]; with K = 16, a full score lies in [-896, 1024], within [-2048, 2047]. Do not saturate intermediate accumulations: clipping would destroy exact incremental equivalence.

The difference between two INT4 values is in [-15, 15], so it does not always fit in INT4. Keep the multiplier at 4×4 bits by splitting a large correction into signed INT4 pieces. Examples: +15 becomes +7, +7, +1; -15 becomes -8, -7. Repeat the corresponding weight pair for each piece. Each feature's pieces must be applied in order before moving to the next feature. The corresponding intermediate feature value stays between its old and new values, preserving the score bound.

For the two input rows, pair their pieces by position and pad the shorter list with zero. If both feature deltas are zero, omit that feature's outer-product token entirely. The host knows each token's weights; feature addresses do not have to be stored on-chip.

Count correction tokens before starting. If their count is at least K, use a clear-and-dense recomputation instead. This policy bounds arithmetic-token traffic by the dense baseline, but does not erase host comparison cost or protocol overhead.

## Proposed chip architecture

- Four processing elements arranged as 2×2. Each has a signed INT4 multiplier, 12-bit accumulator, and operand-forwarding state.
- Output-stationary dataflow: activations move right, weights move down, and partial scores remain in each processing element.
- Stagger row 1 and column 1 by one logical array step; propagate validity with operands so only matching tokens accumulate. Physical wire placement is determined by place and route, not guaranteed by the logical grid.
- A small byte-wide synchronous interface stages two activation nibbles and two weight nibbles on successive cycles. One outer-product token needs at least two input byte transfers. Four MACs per token is not a claim of four MACs per external clock.
- Proposed command functions: clear scores and pipeline; stream operands; drain the pipeline; select and read score bytes. Exact opcode encoding, handshake, latency, and pin allocation are still to be frozen in a separate interface specification.
- Retain scores between updates; drain all tokens before marking a result complete. Read scores only at transaction boundaries. Reset invalidates the retained result and requires a fresh dense initialization.
- Use the 8 dedicated inputs for payload, 8 dedicated outputs for readback, and bidirectional pins with fixed directions for command/handshake/status. Dedicated clock/reset remain separate. Drive all unused output paths explicitly.
- Optional zero-product accumulator enables and operand isolation must preserve token timing. They reduce switching opportunities, not the length of the systolic schedule. Do not independently skip pipeline steps at different processing elements.

The host retains old features and model weights, creates correction streams, and performs any feature extraction. The chip retains only four scores plus small pipeline/control state. This keeps storage small but means the demonstrated system cannot claim to keep that host asleep while the host is supplying updates. Autonomous sensing, ADCs, audio preprocessing, SRAM, training, and a full neural network are outside version 1.

## Example workload

For K = 16, a dense result uses 16 outer-product tokens and 64 scalar MAC opportunities. If only two feature positions change across the two rows and every correction fits INT4, an incremental result needs two tokens and eight MAC opportunities. That is an 8× reduction in tokens for this example, not an 8× measured end-to-end speedup or energy saving. Readback, framing, pipeline drain, host work, and I/O switching remain.

The executable model covers every signed INT4 old/new/weight combination, long randomized update sequences, repeated extreme transitions, and unchanged/sparse/dense workloads. It is an arithmetic model, not a cycle-accurate systolic model.

## Budget and shuttle evidence

The [Tiny Tapeout calculator](https://app.tinytapeout.com/calculator?shuttle=ihp&tiles=1&pcbs=1), inspected on 2026-09-11 with IHP, Individual, Digital, one tile and one PCB, displayed:

| Item | Displayed cost |
| --- | ---: |
| One tile | €70 |
| One discounted individual devkit | €100 |
| Worldwide economy shipping | €15 |
| Total | **€185** |
| Two tiles with the same devkit/shipping | **€255** |

The discounted board price is subject to availability. Confirm eligibility, currency conversion, destination taxes, and final checkout total before buying. A $150–$200 all-in budget is not established by these euro prices. Do not assume a submission-only purchase includes a physical devkit.

The [Tiny Tapeout homepage](https://tinytapeout.com/) currently lists IHP26b as open. Its extracted countdown was not reliable, so no deadline is claimed here. Verify its live deadline and available capacity before committing to that run. Use the [official IHP Verilog template](https://github.com/TinyTapeout/ttihp-verilog-template) if IHP is selected.

The [FAQ's roughly 1,000-gate tile estimate](https://tinytapeout.com/faq/) explicitly describes TT04–TT10. It is not a guarantee that this design fits a current IHP tile. Four multipliers, accumulation and forwarding registers, input staging, readback, clocking, and routing all consume area. Final feasibility comes from the chosen shuttle's actual implementation flow.

## Tapeout milestones and decision gates

1. **Architecture proof:** validate exact delta arithmetic and corner cases. Choose application data and compare dense vs incremental token counts. The arithmetic reference model is included; real-data validation remains.
2. **Area feasibility:** implement a processing element, then the minimal complete array and interface. Run synthesis and place and route in the official one-tile template early. Record standard-cell area, utilization, timing slack, and routing completion. Do this before adding application-specific hardware.
3. **Freeze the interface:** specify every command, cycle, stall, result byte, reset rule, and input/output direction. Add a cycle-accurate reference model and host driver.
4. **RTL verification:** check signed extremes, pipeline alignment, drain behavior, stalls, back-to-back updates, reset during traffic, clear during idle, full readback, and dense/incremental equivalence. Add long randomized sequences that can catch persistent-state drift.
5. **Demonstration and measurements:** train or choose two small class score functions; quantify INT4 accuracy on held-out data. Compare transaction counts and measured latency. Evaluate switching from equivalent workloads and use the PDK power flow if available. Keep simulated power estimates separate from later silicon measurements, and include host/board power in system claims.
6. **Physical signoff and submission:** pass the template's required checks, including timing and physical verification; document pins, setup, clock constraints, and known-answer bring-up vectors. Generate final GDS and documentation from the same verified revision; link that revision in the submission portal and verify acceptance before its deadline. Purchase and account actions remain outstanding.

If the minimal four-PE design fails one-tile implementation, first evaluate serial multiplication and reduce optional control/debug logic. A shared-MAC fallback can preserve the incremental application, but changes the architecture story and must be described honestly. Increase tile count only if a revised budget permits it.
