"""Pin-only tests run unchanged against RTL and the routed gate-level netlist."""
import random
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model.delta_reference import dense, correction_tokens
from host.deltatile import plan_frame, decode_scores


def nibble_pair(a, b):
    return (a & 15) | ((b & 15) << 4)


def signed12(n):
    return ((n + 2048) % 4096) - 2048


class Oracle:
    """Timed arithmetic events, independent of the RTL forwarding registers."""
    def __init__(self):
        self.scores = [0] * 4
        self.events = []
        self.pending = None
        self.error = 0
        self.select = 0

    def edge(self, cmd, payload, strobe, ena, reset):
        if reset:
            self.__init__()
            return
        if not ena:
            return
        if strobe and cmd == 1:
            self.__init__()
            return
        was_busy = bool(self.events)
        keep = []
        for delay, index, delta in self.events:
            if delay == 1:
                self.scores[index] = signed12(self.scores[index] + delta)
            else:
                keep.append((delay - 1, index, delta))
        self.events = keep
        if not strobe:
            return
        if cmd == 2:
            self.pending = [(payload >> shift) & 15 for shift in (0, 4)]
            self.pending = [v if v < 8 else v - 16 for v in self.pending]
        elif cmd == 3:
            if self.pending is None:
                self.error = 1
            else:
                b = [(payload >> shift) & 15 for shift in (0, 4)]
                b = [v if v < 8 else v - 16 for v in b]
                a = self.pending
                self.scores[0] = signed12(self.scores[0] + a[0] * b[0])
                self.events.extend([(1, 1, a[0] * b[1]),
                                    (1, 2, a[1] * b[0]),
                                    (2, 3, a[1] * b[1])])
                self.pending = None
        elif cmd == 4:
            if was_busy or self.pending is not None:
                self.error = 1
            else:
                self.select = payload & 7
        elif cmd == 5:
            self.error = 0
        elif cmd in (6, 7):
            self.error = 1


class Pins:
    def __init__(self, dut):
        self.dut = dut
        self.oracle = Oracle()
        self.cycles = 0

    async def tick(self, cmd=0, payload=0, strobe=0, ena=1, reset=False, noise=0):
        d = self.dut
        d.clk.value = 0
        d.ena.value = ena
        d.rst_n.value = not reset
        d.ui_in.value = payload & 255
        d.uio_in.value = (noise & 240) | (int(strobe) << 3) | cmd
        await Timer(50, unit="ns")
        d.clk.value = 1
        self.oracle.edge(cmd, payload, strobe, ena, reset)
        await Timer(50, unit="ns")
        self.cycles += 1
        o = self.oracle
        busy = bool(o.events)
        status = ((ena and not busy and o.pending is None) << 7) | (o.error << 6) | (busy << 5) | (ena << 4)
        assert int(d.uio_oe.value) == 240, f"output directions at {self.cycles}"
        assert int(d.uio_out.value) == status, f"status at {self.cycles}: expected {status:#x}"
        score = o.scores[o.select >> 1]
        expected = ((score >> 8) if o.select & 1 else score) & 255
        assert int(d.uo_out.value) == expected, f"readback at {self.cycles}: expected {expected:#x}"

    async def command(self, cmd, payload=0):
        await self.tick(cmd, payload, strobe=1)

    async def reset(self):
        await self.tick(reset=True)
        await self.tick(reset=True, ena=0)
        await self.tick()

    async def token(self, a, b):
        await self.command(2, nibble_pair(*a))
        await self.command(3, nibble_pair(*b))

    async def read_scores(self):
        await self.tick()
        await self.tick()
        result = []
        for index in range(4):
            await self.command(4, 2 * index)
            low = int(self.dut.uo_out.value)
            await self.command(4, 2 * index + 1)
            high = int(self.dut.uo_out.value)
            result.append(signed12((high << 8) | low))
        return [result[:2], result[2:]]


@cocotb.test()
async def exhaustive_multiplier_and_readback(dut):
    p = Pins(dut)
    await p.reset()
    for a in range(-8, 8):
        for b in range(-8, 8):
            await p.command(1)
            other_a = 7 - (a + 8)
            other_b = 7 - (b + 8)
            await p.token([a, other_a], [b, other_b])
            assert await p.read_scores() == [[a*b, a*other_b], [other_a*b, other_a*other_b]]


@cocotb.test()
async def retained_dense_and_incremental_scores(dut):
    p = Pins(dut)
    await p.reset()
    rng = random.Random(91726)
    for k in (1, 2, 8, 16):
        weights = [[rng.randrange(-8, 8) for _ in range(2)] for _ in range(k)]
        x = [[rng.randrange(-8, 8) for _ in range(k)] for _ in range(2)]
        await p.command(1)
        for i in range(k):
            await p.token([x[0][i], x[1][i]], weights[i])
        assert await p.read_scores() == dense(x, weights)
        for _ in range(100):
            new = [[v if rng.random() < 0.8 else rng.randrange(-8, 8) for v in row] for row in x]
            for a, b in correction_tokens(x, new, weights):
                await p.token(a, b)
                if rng.random() < 0.2:
                    await p.tick()
            assert await p.read_scores() == dense(new, weights)
            x = new
    # Worst product, worst full score, and the three-piece +15 correction.
    weights = [[-8, 7] for _ in range(16)]
    x = [[-8] * 16 for _ in range(2)]
    await p.command(1)
    for i in range(16):
        await p.token([-8, -8], weights[i])
    assert await p.read_scores() == [[1024, -896], [1024, -896]]
    for t in range(20):
        new = [[7 if t % 2 == 0 else -8] * 16 for _ in range(2)]
        for a, b in correction_tokens(x, new, weights):
            await p.token(a, b)
        assert await p.read_scores() == dense(new, weights)
        x = new


@cocotb.test()
async def randomized_protocol_pipeline_and_reset(dut):
    p = Pins(dut)
    await p.reset()
    rng = random.Random(19485)
    for _ in range(15000):
        await p.tick(cmd=rng.randrange(8), payload=rng.randrange(256),
                     strobe=rng.random() < 0.8, ena=rng.random() < 0.9,
                     reset=rng.random() < 0.003, noise=rng.randrange(256))
    await p.reset()
    assert await p.read_scores() == [[0, 0], [0, 0]]


@cocotb.test()
async def directed_abort_hold_errors_and_wrap(dut):
    p = Pins(dut)
    await p.reset()
    await p.command(3, 255)  # MAC without operands: rejected.
    assert int(dut.uio_out.value) & 64
    await p.command(5)
    await p.command(2, 0x11)
    await p.command(4, 7)  # Pending A prevents reading.
    assert int(dut.uio_out.value) & 64
    await p.command(2, 0x23)  # Explicit replacement of staged A.
    await p.command(3, 0x45)
    for _ in range(5):
        await p.tick(cmd=1, strobe=1, ena=0)  # Whole array freezes.
    await p.command(4)  # Busy read rejected while pipe progresses.
    assert await p.read_scores() == [[15, 12], [10, 8]]
    await p.command(1)
    await p.token([-8, 7], [7, -8])
    await p.command(1)  # Clear in flight flushes every result.
    assert await p.read_scores() == [[0, 0], [0, 0]]
    await p.token([7, -8], [-8, 7])
    await p.tick(reset=True, ena=0)  # Reset overrides disable.
    assert await p.read_scores() == [[0, 0], [0, 0]]
    # Out-of-contract streams have explicitly defined modulo-4096 behavior.
    for _ in range(40):
        await p.token([-8, -8], [-8, -8])
    assert await p.read_scores() == [[-1536, -1536], [-1536, -1536]]


@cocotb.test()
async def host_packet_plans_on_chip(dut):
    p = Pins(dut)
    await p.reset()
    rng = random.Random(6241)
    weights = [[rng.randrange(-8, 8) for _ in range(2)] for _ in range(16)]
    previous = None
    features = [[0] * 16 for _ in range(2)]
    observed_modes = set()
    for frame in range(200):
        features = [[v if rng.random() < (0.95 if frame % 2 else 0)
                     else rng.randrange(-8, 8) for v in row] for row in features]
        plan = plan_frame(features, weights, previous)
        observed_modes.add(plan.mode)
        data = []
        for cmd, payload in plan.commands:
            await p.command(cmd, payload)
            status = int(dut.uio_out.value)
            assert not status & 0x40
            if cmd == 4:
                assert status & 0x80
                data.append(int(dut.uo_out.value))
        assert decode_scores(data) == dense(features, weights)
        previous = [row[:] for row in features]
    assert observed_modes == {"dense", "incremental"}
