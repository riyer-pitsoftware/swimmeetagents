from __future__ import annotations

from dataclasses import dataclass

from tracker.fetch import is_domain_blocked, is_target_blocked, robots_check


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str | None


ALLOW = PolicyDecision(allowed=True, reason=None)


def evaluate_source_policy(
    source_url: str,
    user_agent: str,
    timeout_seconds: int,
) -> PolicyDecision:
    if is_domain_blocked(source_url):
        return PolicyDecision(allowed=False, reason="domain_blocked")

    blocked, reason = is_target_blocked(source_url)
    if blocked:
        return PolicyDecision(allowed=False, reason=reason or "target_blocked")

    robots_allowed, robots_reason = robots_check(source_url, user_agent, timeout_seconds)
    if not robots_allowed:
        return PolicyDecision(allowed=False, reason=robots_reason or "robots_blocked")

    return ALLOW


def evaluate_child_policy(
    child_url: str,
    user_agent: str,
    timeout_seconds: int,
) -> PolicyDecision:
    return evaluate_source_policy(
        source_url=child_url,
        user_agent=user_agent,
        timeout_seconds=timeout_seconds,
    )
