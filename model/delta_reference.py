"""Arithmetic feasibility model only: no clock, protocol, RTL, or power model."""

from random import Random


def split_delta(delta):
    """Exact monotonic INT4 pieces for a difference of two INT4 values."""
    assert -15 <= delta <= 15
    pieces = []
    while delta:
        piece = max(-8, min(7, delta))
        pieces.append(piece)
        delta -= piece
    return pieces


def dense(x, weights):
    return [[sum(a * w[col] for a, w in zip(row, weights))
             for col in range(2)] for row in x]


def correction_tokens(old, new, weights):
    tokens = []
    for k, weight_pair in enumerate(weights):
        pieces = [split_delta(new[r][k] - old[r][k]) for r in range(2)]
        for p in range(max(map(len, pieces))):
            activation_pair = [row[p] if p < len(row) else 0 for row in pieces]
            tokens.append((activation_pair, weight_pair))
    return tokens


def apply_tokens(scores, tokens):
    out = [row[:] for row in scores]
    for activations, weights in tokens:
        for r in range(2):
            for c in range(2):
                assert -8 <= activations[r] <= 7
                assert -8 <= weights[c] <= 7
                out[r][c] += activations[r] * weights[c]
                assert -2048 <= out[r][c] <= 2047, "12-bit accumulator overflow"
    return out


def run_checks():
    cases = 0
    for old in range(-8, 8):
        for new in range(-8, 8):
            pieces = split_delta(new - old)
            assert sum(pieces) == new - old
            for weight in range(-8, 8):
                score = old * weight
                feature = old
                for p in pieces:
                    feature += p
                    assert -8 <= feature <= 7
                    score += p * weight
                assert score == new * weight
                cases += 1

    rng = Random(20260911)
    updates = 0
    for k in (1, 2, 8, 16):
        weights = [[rng.randrange(-8, 8) for _ in range(2)] for _ in range(k)]
        x = [[rng.randrange(-8, 8) for _ in range(k)] for _ in range(2)]
        scores = dense(x, weights)
        for step in range(2500):
            new = [row[:] for row in x]
            for r in range(2):
                for i in range(k):
                    if rng.random() < (0.1 if step % 2 else 1.0):
                        new[r][i] = rng.randrange(-8, 8)
            tokens = correction_tokens(x, new, weights)
            # Always exercise corrections, even when dense would cost less.
            scores = apply_tokens(scores, tokens)
            assert scores == dense(new, weights)
            x = new
            updates += 1

    weights = [[-8, 7] for _ in range(16)]
    x = [[-8] * 16 for _ in range(2)]
    scores = dense(x, weights)
    for step in range(100):
        new = [[7 if step % 2 == 0 else -8] * 16 for _ in range(2)]
        scores = apply_tokens(scores, correction_tokens(x, new, weights))
        assert scores == dense(new, weights)
        x = new

    old = [[0] * 16 for _ in range(2)]
    sparse = [row[:] for row in old]
    sparse[0][2], sparse[1][7] = 1, -2
    assert len(correction_tokens(old, old, weights)) == 0
    assert len(correction_tokens(old, sparse, weights)) == 2
    large_old = [[-8] * 16 for _ in range(2)]
    large_new = [[7] * 16 for _ in range(2)]
    assert len(correction_tokens(large_old, large_new, weights)) == 48
    print(f"PASS: {cases} exhaustive old/new/weight cases")
    print(f"PASS: {updates} consecutive randomized matrix updates; 100 extreme updates")
    print("Token examples (K=16): dense=16; unchanged=0; two small changes=2")
    print("Worst +15 transition: 48 correction tokens; choose 16-token dense refresh")
    print("Arithmetic verified only. RTL, timing, area, power, and I/O remain unverified.")


if __name__ == "__main__":
    run_checks()
