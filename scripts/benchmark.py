"""Deterministic synthetic traffic study. Does not estimate power or accuracy."""
import json
from pathlib import Path
import random
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from host.deltatile import plan_frame

records = []
for probability in (0.0, 0.01, 0.05, 0.1, 0.25, 1.0):
    rng = random.Random(9112026)
    weights = [[rng.randrange(-8, 8) for _ in range(2)] for _ in range(16)]
    old = None
    features = [[0] * 16 for _ in range(2)]
    tokens = clocks = dense_frames = 0
    frames = 2000
    for _ in range(frames):
        features = [[max(-8, min(7, v + rng.choice((-1, 1))))
                     if rng.random() < probability else v for v in row] for row in features]
        plan = plan_frame(features, weights, old)
        tokens += plan.tokens
        clocks += len(plan.commands)
        dense_frames += plan.mode == "dense"
        old = [row[:] for row in features]
    records.append({
        "per_feature_change_attempt_probability": probability,
        "frames": frames, "mean_tokens": tokens / frames,
        "mean_command_clocks": clocks / frames,
        "dense_frames": dense_frames,
        "command_clock_ratio_vs_dense": (43 * frames) / clocks,
    })
report = {
    "scope": "Synthetic bounded INT4 random walk, 2x16 features, fixed 16x2 weights; exact updates",
    "baseline": "Dense refresh: 16 tokens and 43 command clocks per frame, including clear, drain and full readback",
    "limitations": "No host runtime, feature acquisition, board I/O delays, power, accuracy, or silicon measurements",
    "seed": 9112026,
    "results": records,
}
destination = root / "docs" / "synthetic-traffic.json"
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
