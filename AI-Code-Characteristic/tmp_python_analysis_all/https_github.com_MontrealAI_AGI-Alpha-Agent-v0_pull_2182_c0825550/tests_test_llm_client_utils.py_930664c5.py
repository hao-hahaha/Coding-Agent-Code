from alpha_factory_v1.demos.self_healing_repo.agent_core import llm_client


def test_summarize_error_returns_first_line() -> None:
    log = "E   ValueError: bad\nline2\nline3"
    assert llm_client.summarize_error(log) == "E   ValueError: bad"


def test_generate_branch_name_slugified() -> None:
    log = "E   ValueError: something went wrong on operation"  # long line
    name = llm_client.generate_branch_name(log)
    assert name.startswith("e-valueerror-something")
    assert len(name) <= 30
