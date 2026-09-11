"""MicroPython known-answer bring-up for a supported Tiny Tapeout demo board.

Select DeltaTile before calling run(tt). Stops automatic clocking and drives only
the lower four bidirectional pins. API checked against tt-micropython-firmware
d485c7a9986336024e35d790568fca33be1c5665; not yet tested on fabricated hardware.
"""
import time


def exchange(tt, command, payload=0):
    tt.clk(0)
    tt.ui_in.value = payload
    tt.uio_in.value = 8 | command
    time.sleep_us(10)
    tt.clock_project_once(msDelay=1)
    time.sleep_us(10)
    result = int(tt.uo_out.value)
    status = int(tt.uio_out.value)
    tt.uio_in.value = 0
    if not status & 0x10 or status & 0x40:
        raise RuntimeError("Chip disabled or command error: reset and retry")
    if command == 4 and not status & 0x80:
        raise RuntimeError("Result not settled")
    return result


def read_scores(tt):
    exchange(tt, 0)
    exchange(tt, 0)
    scores = []
    for index in range(4):
        low = exchange(tt, 4, 2 * index)
        high = exchange(tt, 4, 2 * index + 1)
        value = low | (high << 8)
        scores.append(value - 65536 if value >= 32768 else value)
    return [scores[:2], scores[2:]]


def run(tt):
    tt.clock_project_stop()
    tt.uio_oe_pico.value = 0x0F
    tt.uio_in.value = 0
    tt.ui_in.value = 0
    tt.pins.project_clk_driven_by_RP2(True)
    tt.clk(0)
    tt.reset_project(True)
    tt.clock_project_once(msDelay=1)
    tt.clock_project_once(msDelay=1)
    tt.reset_project(False)
    exchange(tt, 1)
    exchange(tt, 2, 0xE3)
    exchange(tt, 3, 0xF4)
    result = read_scores(tt)
    assert result == [[12, -3], [-8, 2]], result
    exchange(tt, 2, 0x01)
    exchange(tt, 3, 0xF4)
    updated = read_scores(tt)
    assert updated == [[16, -4], [-8, 2]], updated
    print("DeltaTile known-answer checks passed:", result, "->", updated)
    return updated
