"""Build GitHub issue search queries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def quote_value(value: str) -> str:
    """Quote a GitHub search value when necessary."""
    cleaned = value.strip().replace('"', "")
    if not cleaned:
        raise ValueError("search values cannot be empty")
    return f'"{cleaned}"' if any(character.isspace() for character in cleaned) else cleaned


def build_query(
    *,
    keywords: list[str] | None = None,
    labels: list[str] | None = None,
    language: str | None = None,
    repository: str | None = None,
    organization: str | None = None,
    max_age_days: int = 90,
    include_assigned: bool = False,
    extra_query: str | None = None,
    now: datetime | None = None,
) -> str:
    """Create a focused GitHub issue search query."""
    if repository and organization:
        raise ValueError("--repo and --org cannot be used together")
    if max_age_days < 1:
        raise ValueError("--max-age must be at least 1 day")

    current = now or datetime.now(timezone.utc)
    created_after = (current - timedelta(days=max_age_days)).date().isoformat()
    parts = ["is:issue", "is:open", "archived:false"]
    if not include_assigned:
        parts.append("no:assignee")
    for label in labels or ["good first issue"]:
        parts.append(f"label:{quote_value(label)}")
    if language:
        parts.append(f"language:{quote_value(language)}")
    if repository:
        parts.append(f"repo:{quote_value(repository)}")
    if organization:
        parts.append(f"org:{quote_value(organization)}")
    parts.append(f"created:>={created_after}")
    if keywords:
        parts.extend(keyword.strip() for keyword in keywords if keyword.strip())
    if extra_query:
        parts.append(extra_query.strip())
    parts.append("sort:created-desc")
    return " ".join(parts)
