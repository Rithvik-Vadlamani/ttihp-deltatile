"""Host packet planning and transport adapter; hardware access is supplied by caller."""
from dataclasses import dataclass

from model.delta_reference import correction_tokens, dense

NOP, CLEAR, LOAD_A, MAC, READ, CLEAR_ERROR = range(6)


def validate_inputs(features, weights):
    if len(features) != 2 or not 1 <= len(weights) <= 16:
        raise ValueError("Require two feature rows and K in [1,16]")
    k = len(weights)
    if any(len(row) != k for row in features) or any(len(row) != 2 for row in weights):
        raise ValueError("Require features shaped 2xK and weights shaped Kx2")
    if any(type(v) is not int or not -8 <= v <= 7
           for rows in (features, weights) for row in rows for v in row):
        raise ValueError("All features and weights must be signed INT4 integers")


def pack(a, b):
    return (a & 15) | ((b & 15) << 4)


@dataclass(frozen=True)
class FramePlan:
    mode: str
    tokens: int
    commands: tuple
    expected: tuple


def plan_frame(features, weights, previous=None):
    """Use previous only after successful readback with the same weights/scaling.

    On reset, any transport error, model change, or uncertain delivery, omit previous
    to force a clear-and-dense refresh. The planner never assumes a frame was sent.
    """
    validate_inputs(features, weights)
    if previous is not None:
        validate_inputs(previous, weights)
        tokens = correction_tokens(previous, features, weights)
    else:
        tokens = []
    use_dense = previous is None or len(tokens) >= len(weights)
    commands = []
    if use_dense:
        commands.append((CLEAR, 0))
        tokens = [([features[0][k], features[1][k]], w) for k, w in enumerate(weights)]
    for a, b in tokens:
        commands.extend(((LOAD_A, pack(*a)), (MAC, pack(*b))))
    commands.extend(((NOP, 0), (NOP, 0)))
    commands.extend((READ, i) for i in range(8))
    expected = tuple(tuple(row) for row in dense(features, weights))
    return FramePlan("dense" if use_dense else "incremental", len(tokens), tuple(commands), expected)


def decode_scores(data):
    if len(data) != 8 or any(not 0 <= v <= 255 for v in data):
        raise ValueError("Require eight result bytes")
    scores = []
    for i in range(0, 8, 2):
        value = data[i] | (data[i + 1] << 8)
        value = value - 65536 if value >= 32768 else value
        if not -2048 <= value <= 2047:
            raise ValueError("Bad 12-bit sign extension; check the bus or read alignment")
        scores.append(value)
    return [scores[:2], scores[2:]]


def run_plan(exchange, plan):
    """exchange(command, payload) clocks once and returns (result_byte, status_byte).

    Caller must reset hardware before first use. No other writer may use the bus
    during a plan. Transport must meet setup/hold and must leave STROBE low if an
    independent clock continues after the final command.
    """
    readback = []
    for command, payload in plan.commands:
        result, status = exchange(command, payload)
        if not status & 0x10 or status & 0x40:
            raise RuntimeError("Chip disabled or command error; reset and perform a dense refresh")
        if command == READ:
            if not status & 0x80:
                raise RuntimeError("Result is not settled; reset and perform a dense refresh")
            readback.append(result)
    scores = decode_scores(readback)
    if tuple(map(tuple, scores)) != plan.expected:
        raise RuntimeError("Readback differs from exact software result; do not retain this frame")
    return scores
