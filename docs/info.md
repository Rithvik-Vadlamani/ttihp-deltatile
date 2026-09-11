# How it works

DeltaTile is a 2x2 output-stationary systolic array with signed INT4 multiplication and four signed 12-bit retained accumulators. It computes C = XW for a 2xK input matrix and a Kx2 weight matrix. Activations move right, weights move down, and the second row/column are delayed by one clock to align products.

For fixed weights, retained scores support exact incremental inference: C_new = C_old + (X_new - X_old) W. A host keeps old features and weights and streams only changed contributions. A difference outside [-8,7] is split into multiple INT4 values: +15 = +7 +7 +1; -15 = -8 -7. Process each feature's pieces in order. Use clear-and-dense recomputation when it costs fewer tokens. No ADC, feature extraction, model memory, or autonomous event detector is included.

## Interface and timing

All inputs are synchronous to `clk`; clock target is 10 MHz. Keep data/control stable across the rising edge. `rst_n` is an active-low synchronous reset: hold it low for at least two rising clock edges. Reset works even when `ena` is low. With `ena` low, all other chip state and in-flight computation hold.

`ui_in[7:0]` is payload. `uio_in[2:0]` is command and `uio_in[3]` is STROBE. Every enabled rising edge with STROBE=1 executes a command; this is a level-sampled bus, not an edge-triggered request. Back-to-back commands may keep STROBE high. Upper bidirectional pins are outputs (`uio_oe=0xf0`) and must not be driven by the host.

| Command | Value | Payload and effect |
| --- | --- | --- |
| NOP | 0 | No command effect; pipeline still advances |
| CLEAR | 1 | Zero scores; flush pipeline and staged A; clear ERROR and read selector |
| LOAD_A | 2 | Low nibble = row 0 activation; high nibble = row 1 activation; replaces any staged pair |
| MAC | 3 | Low nibble = column 0 weight; high nibble = column 1 weight; consume staged A and launch one outer product |
| READ | 4 | Bits [2:1] select score 00,01,10,11; bit 0 selects low/high byte; upper payload bits ignored |
| CLEAR_ERROR | 5 | Clear sticky ERROR without disturbing computation |
| Reserved | 6,7 | Set ERROR; no command data effect |

MAC without a staged activation pair is rejected and sets ERROR. READ while a pair is staged or the pipeline is busy is rejected and leaves the selector unchanged. Errors do not stop already accepted computation. CLEAR aborts every pending contribution, including products that would otherwise complete on its rising edge.

One token needs LOAD_A then MAC, so maximum input rate is one token per two clocks. If MAC is accepted at edge n, C00 updates at n, C01/C10 at n+1, and C11 at n+2. Ordinary commands and idle cycles advance the pipeline. Another LOAD_A can occur at n+1, followed by another MAC at n+2. After the last MAC, allow two enabled rising edges before requesting READ. READ on the exact edge at which the last product completes is still rejected because BUSY was high before that edge.

`uo_out` continuously reflects the selected result byte. A successful READ changes the selector at its rising edge. Read each score's low byte then high byte; high-byte bits [7:4] replicate the sign, so the two bytes form a signed 16-bit sign extension of the 12-bit result. The bus is not a snapshot register: do not launch computation while reading a set of scores.

| Output pin | Meaning |
| --- | --- |
| uio[4] READY | Equal to ena; commands are sampled when high, subject to the command rules |
| uio[5] BUSY | At least one accepted product remains in flight |
| uio[6] ERROR | Sticky command error; cleared by reset, CLEAR, or CLEAR_ERROR |
| uio[7] RESULT_VALID | ena high, no staged activation pair, and pipeline empty |

RESULT_VALID indicates a settled arithmetic state, including the zero state after reset; it does not know whether the host has sent a complete model frame. A host must track frame boundaries itself and reject results when ERROR is set.

## Numeric limits

All nibbles use signed two's complement [-8,7]. For K<=16 without bias, scores are in [-896,1024] and fit the accumulator. Correctly ordered incremental updates between valid feature vectors remain within this range. Weights and feature scaling must stay fixed across retained-score updates. Clear and recompute after changing either, losing synchronization, or resetting the chip.

Accumulation wraps modulo 4096 outside the supported range. There is no saturation or overflow flag. Sending arbitrary unbounded corrections violates the application's range guarantee. A host should force a dense refresh after any protocol interruption.

# How to test

Reset, then apply the following commands on successive rising clock edges:

| Command | Payload | Purpose |
| --- | --- | --- |
| CLEAR | 0x00 | Initialize |
| LOAD_A | 0xE3 | Row activations [3,-2] |
| MAC | 0xF4 | Column weights [4,-1] |
| NOP | 0x00 | Advance |
| NOP | 0x00 | Drain |

The scores must be [[12,-3],[-8,2]]. READ selector payloads 0 through 7 must return `0C 00 FD FF F8 FF 02 00`. Then LOAD_A=0x01, MAC=0xF4, two NOPs updates scores to [[16,-4],[-8,2]], showing an incremental +1 change in row 0. The corresponding bytes are `10 00 FC FF F8 FF 02 00`.

The Cocotb suite in `test/` uses only top-level pins and runs against both RTL and the generated gate-level netlist. It covers all signed multiplier inputs, score readback, dense/incremental equivalence, extreme transitions, random commands, reset, stalls, aborts, invalid reads, and modulo overflow behavior.

# External hardware

A Tiny Tapeout-compatible demo board or external synchronous pattern generator is sufficient. The host supplies clock, payload, and command inputs and reads result/status outputs. Start bring-up with a slow clock and the known-answer sequence above. Sensor demonstrations additionally need a sensor/ADC and host feature preparation; these are not required for core chip testing.
