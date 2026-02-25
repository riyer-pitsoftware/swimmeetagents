import tracker.policy as policy


def test_source_policy_blocks_domain(monkeypatch) -> None:
    monkeypatch.setattr(policy, "is_domain_blocked", lambda _: True)
    monkeypatch.setattr(policy, "is_target_blocked", lambda _: (False, None))
    monkeypatch.setattr(policy, "robots_check", lambda *_: (True, None))

    decision = policy.evaluate_source_policy("https://meetmobile.com/x", "ua", 5)
    assert not decision.allowed
    assert decision.reason == "domain_blocked"


def test_source_policy_blocks_target(monkeypatch) -> None:
    monkeypatch.setattr(policy, "is_domain_blocked", lambda _: False)
    monkeypatch.setattr(policy, "is_target_blocked", lambda _: (True, "private_ip_blocked"))
    monkeypatch.setattr(policy, "robots_check", lambda *_: (True, None))

    decision = policy.evaluate_source_policy("https://example.com", "ua", 5)
    assert not decision.allowed
    assert decision.reason == "private_ip_blocked"


def test_source_policy_blocks_robots(monkeypatch) -> None:
    monkeypatch.setattr(policy, "is_domain_blocked", lambda _: False)
    monkeypatch.setattr(policy, "is_target_blocked", lambda _: (False, None))
    monkeypatch.setattr(policy, "robots_check", lambda *_: (False, "robots_disallow"))

    decision = policy.evaluate_source_policy("https://example.com", "ua", 5)
    assert not decision.allowed
    assert decision.reason == "robots_disallow"


def test_child_policy_allows_clean_target(monkeypatch) -> None:
    monkeypatch.setattr(policy, "is_target_blocked", lambda _: (False, None))
    decision = policy.evaluate_child_policy("https://example.com/results.pdf")
    assert decision.allowed
    assert decision.reason is None
