from scripts.smoke_local_judge import direct_session


def test_internal_judge_smoke_ignores_global_proxy_environment() -> None:
    session = direct_session()
    assert session.trust_env is False
