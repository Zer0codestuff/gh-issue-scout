"""Claim detection and transparent issue scoring."""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone

from issue_scout.models import Issue, RankedIssue


CLAIM_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:i(?:'m| am)|we(?:'re| are))\s+(?:currently\s+)?(?:working|starting|taking|implementing|fixing)\b",
        r"\b(?:i(?:'d| would) like|can i|could i|may i)\s+(?:to\s+)?(?:work|take|pick|handle|implement|fix|be assigned)\b",
        r"\b(?:assign|assigned)\s+(?:this\s+)?to\s+me\b",
        r"\b(?:claiming|claimed by|i claim)\b",
    )
)


def days_since(value: datetime, now: datetime) -> float:
    """Return non-negative elapsed days."""
    return max(0.0, (now - value).total_seconds() / 86_400)


def find_claim(
    issue: Issue,
    *,
    now: datetime | None = None,
    window_days: int = 30,
) -> str | None:
    """Return recent claim evidence from assignees or issue comments."""
    if issue.assignees:
        return f"assigned to {', '.join(issue.assignees)}"
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(days=window_days)
    for comment in reversed(issue.comments):
        if comment.created_at < cutoff or comment.author.endswith("[bot]"):
            continue
        normalized = " ".join(comment.body.split())
        for pattern in CLAIM_PATTERNS:
            match = pattern.search(normalized)
            if match:
                author = f"@{comment.author}" if comment.author else "a commenter"
                return f"{author}: {match.group(0)}"
    return None


def rank_issue(
    issue: Issue,
    *,
    now: datetime | None = None,
    claim_window_days: int = 30,
) -> RankedIssue:
    """Score one issue using documented, deterministic signals."""
    current = now or datetime.now(timezone.utc)
    issue_age = days_since(issue.created_at, current)
    repo_idle = days_since(issue.repo_pushed_at, current)

    score = 0.0
    reasons: list[str] = []

    freshness = max(0.0, 28.0 - issue_age * 0.35)
    score += freshness
    if issue_age < 7:
        reasons.append(f"opened {max(1, round(issue_age))}d ago")
    elif issue_age < 45:
        reasons.append(f"opened {round(issue_age)}d ago")

    activity = max(0.0, 22.0 - repo_idle * 0.08)
    score += activity
    if repo_idle < 14:
        reasons.append("repo pushed recently")
    elif repo_idle < 90:
        reasons.append(f"repo pushed {round(repo_idle)}d ago")

    popularity = min(20.0, math.log10(issue.stars + 1) * 5.0)
    score += popularity
    if issue.stars >= 100:
        reasons.append(f"{human_count(issue.stars)} stars")

    if issue.comment_count == 0:
        score += 15.0
        reasons.append("no comments")
    elif issue.comment_count <= 2:
        score += 11.0
        reasons.append(f"{issue.comment_count} comment{'s' if issue.comment_count != 1 else ''}")
    elif issue.comment_count <= 5:
        score += 6.0
    elif issue.comment_count > 10:
        score -= min(10.0, (issue.comment_count - 10) * 0.8)

    lowered_labels = {label.casefold() for label in issue.labels}
    if "good first issue" in lowered_labels:
        score += 10.0
        reasons.append("good first issue")
    if "help wanted" in lowered_labels:
        score += 5.0
        reasons.append("help wanted")

    if issue.positive_reactions:
        score += min(5.0, math.sqrt(issue.positive_reactions) * 1.5)
        reasons.append(f"{issue.positive_reactions} positive reactions")

    maintainer_comments = sum(
        comment.author_association in {"OWNER", "MEMBER", "COLLABORATOR"}
        for comment in issue.comments
    )
    if maintainer_comments:
        score += min(5.0, maintainer_comments * 2.0)
        reasons.append("maintainer active in thread")

    claim_evidence = find_claim(issue, now=current, window_days=claim_window_days)
    if claim_evidence:
        score -= 100.0

    return RankedIssue(
        issue=issue,
        score=round(max(0.0, min(100.0, score)), 1),
        reasons=tuple(reasons[:5]),
        claim_evidence=claim_evidence,
    )


def human_count(value: int) -> str:
    """Format a count for compact terminal output."""
    if value >= 1_000_000:
        number = f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{number}m"
    if value >= 1_000:
        number = f"{value / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{number}k"
    return str(value)
