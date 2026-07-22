from __future__ import annotations

from scripts.probe_single_node_collectives import combine_rounds, validate_rank_results


def _records(*, gloo_ok: bool = True, socket: str | None = None) -> list[dict]:
    return [
        {
            "rank": rank,
            "local_rank": rank,
            "world_size": 8,
            "cuda_device": rank,
            "nccl_all_reduce_sum": 28,
            "gloo_all_reduce_sum": 28 if gloo_ok else 27,
            "nccl_barrier_completed": True,
            "gloo_barrier_completed": gloo_ok,
            "pid": 1000 + rank + (100 if socket else 0),
            "gloo_socket_ifname": socket,
            "nccl_socket_ifname": socket,
            "error": None,
        }
        for rank in range(8)
    ]


def test_two_fresh_collective_rounds_pass() -> None:
    default = validate_rank_results(_records())
    default["round_name"] = "default"
    pinned = validate_rank_results(_records(socket="ib0"))
    pinned["round_name"] = "ib0"
    assert combine_rounds([default, pinned])["status"] == "pass"


def test_adversarial_missing_rank_fails() -> None:
    result = validate_rank_results(_records()[:-1])
    assert result["status"] == "fail"
    assert result["checks"]["exact_rank_count"] is False


def test_adversarial_nccl_only_result_fails_without_gloo_full_mesh() -> None:
    result = validate_rank_results(_records(gloo_ok=False))
    assert result["status"] == "fail"
    assert result["checks"]["gloo_full_mesh_all_reduce_exact"] is False
    assert result["checks"]["both_barriers_completed"] is False
