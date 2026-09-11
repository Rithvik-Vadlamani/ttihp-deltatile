"""Host validation and transport failure handling (plain pytest)."""
import pytest
from host.deltatile import plan_frame, decode_scores, run_plan


def test_bringup_and_readback():
    plan = plan_frame([[3], [-2]], [[4, -1]])
    assert plan.commands[:3] == ((1, 0), (2, 0xE3), (3, 0xF4))
    data = iter([12, 0, 253, 255, 248, 255, 2, 0])
    def exchange(cmd, payload):
        return (next(data) if cmd == 4 else 0), 0x90
    assert run_plan(exchange, plan) == [[12, -3], [-8, 2]]


def test_sparse_and_dense_policy():
    w = [[-8, 7] for _ in range(16)]
    old = [[0] * 16 for _ in range(2)]
    assert plan_frame(old, w, old).tokens == 0
    new = [row[:] for row in old]
    new[0][2] = 1
    assert plan_frame(new, w, old).tokens == 1
    assert plan_frame([[7] * 16] * 2, w, [[-8] * 16] * 2).mode == "dense"


@pytest.mark.parametrize("features,weights", [
    ([[0]], [[1, 2]]), ([[0], [0]], []), ([[8], [0]], [[1, 2]]),
    ([[0], [0]], [[1]]), ([[0] * 17] * 2, [[0, 0]] * 17),
    ([[0.5], [0]], [[1, 2]]),
])
def test_input_contract(features, weights):
    with pytest.raises(ValueError):
        plan_frame(features, weights)


@pytest.mark.parametrize("status", [0, 0xD0, 0x10])
def test_transport_errors(status):
    plan = plan_frame([[0], [0]], [[0, 0]])
    with pytest.raises(RuntimeError):
        run_plan(lambda cmd, payload: (0, status), plan)


def test_bad_sign_extension():
    with pytest.raises(ValueError):
        decode_scores([0, 8, 0, 0, 0, 0, 0, 0])


def test_transport_corruption():
    plan = plan_frame([[1], [1]], [[1, 1]])
    with pytest.raises(RuntimeError, match="differs"):
        run_plan(lambda cmd, payload: (0, 0x90), plan)
