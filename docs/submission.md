# DeltaTile submission record

The design release is complete. Tiny Tapeout portal acceptance has not been recorded. The owner explicitly instructed that no purchases be made; paid allocation, checkout, fabrication orders, delivery, and silicon testing are outside the current task.

## Frozen submission candidate

| Field | Value |
| --- | --- |
| Project | DeltaTile |
| Author | Rithvik Vadlamani |
| Repository | https://github.com/Rithvik-Vadlamani/ttihp-deltatile |
| Release | v0.1.0 |
| Verified implementation revision | 72cf3db7bd78a53d63e1f8e8d39cbff5dc5a253c |
| Target shuttle | Tiny Tapeout IHP26b |
| Tile allocation requested by design | One digital 1x1 tile |
| Top module | tt_um_rithvik_deltatile |
| Clock | 10 MHz |
| GDS workflow run | 34581705980 |
| RTL and host workflow run | 34581706028 |
| Datasheet workflow run | 34581706006 |

Package: `deltatile-ihp26b-72cf3db.zip` (1,482,494 bytes).

SHA-256: `d27630f3e3b5a0734c411a996533ce33dd2b113e907885b040288aa0c601ef3d`.

The package contains an exact source archive and per-file checksums. Later documentation commits do not replace the verified implementation revision. Select the verified workflow/revision when the portal offers that choice; do not accidentally submit a documentation-only HEAD with no corresponding physical build.

## Submission description

DeltaTile is a 2x2 signed INT4 systolic array with four retained signed 12-bit accumulators. A host streams dense products or exact corrections derived from changed input features. Large corrections are split into legal INT4 tokens, and the host chooses dense refresh when cheaper. The chip provides command-driven execution, status outputs, and byte-wide result readback. Its numeric contract supports dot products up to length 16. The host owns feature history and weights. No autonomous audio processing, measured power reduction, or silicon-tested classification accuracy is claimed.

## Portal status

As of September 11, 2026, the portal requires Tiny Tapeout OAuth authorization for the Rithvik-Vadlamani account. Its requested scope is read-only access to GitHub email addresses. Approval is pending. No project ID, allocation, acceptance receipt, or order number has been issued for this design.

The repository and its release remain private. Any necessary repository access change must be resolved before the portal can import the design. No assertion is made that the current private repository is accepted by Tiny Tapeout.

The portal displayed an IHP26b deadline of September 21, 2026, at 3 p.m. Central on September 11. A saved project, if available without payment, is distinct from a reserved or accepted fabrication slot.

## Completion evidence

See [signoff.md](signoff.md) for physical, functional, timing, and manufacturing checks and their limits, [info.md](info.md) for the interface, and [bringup.md](bringup.md) for the hardware test procedure. The release includes all three and the generated four-page datasheet. The source and manufacturing files are frozen; real silicon bring-up remains dependent on a future separately authorized fabrication order.
