from __future__ import annotations

import pytest

from scripts.nccl_allreduce_bench import bus_bandwidth_gbps


def test_allreduce_bus_bandwidth_uses_standard_ring_correction() -> None:
    assert bus_bandwidth_gbps(1_000_000_000, 1.0, 2) == pytest.approx(1.0)
    assert bus_bandwidth_gbps(1_000_000_000, 1.0, 16) == pytest.approx(1.875)


@pytest.mark.parametrize(
    ("nbytes", "seconds", "world_size"),
    [(0, 1.0, 2), (1, 0.0, 2), (1, 1.0, 1)],
)
def test_allreduce_bus_bandwidth_rejects_invalid_inputs(
    nbytes: int, seconds: float, world_size: int
) -> None:
    with pytest.raises(ValueError):
        bus_bandwidth_gbps(nbytes, seconds, world_size)
