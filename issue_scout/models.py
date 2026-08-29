"""Data models used by Issue Scout."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def parse_datetime(value: str | None) -> datetime:
    """Parse a GitHub ISO timestamp into an aware UTC datetime."""
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass(frozen=True)
class Comment:
    """The comment fields needed for claim detection."""

    body: str
    created_at: datetime
    author: str = ""
    author_association: str = "NONE"


@dataclass(frozen=True)
class Issue:
    """A normalized issue returned by GitHub GraphQL."""

    repository: str
    number: int
    title: str
    url: str
    created_at: datetime
    updated_at: datetime
    stars: int
    repo_pushed_at: datetime
    labels: tuple[str, ...] = ()
    assignees: tuple[str, ...] = ()
    comments: tuple[Comment, ...] = ()
    comment_count: int = 0
    positive_reactions: int = 0
    language: str = ""

    @classmethod
    def from_graphql(cls, node: dict[str, Any]) -> Issue:
        """Build an Issue from a GraphQL node, tolerating deleted users."""
        repository = node.get("repository") or {}
        labels = tuple(
            label.get("name", "")
            for label in (node.get("labels") or {}).get("nodes", [])
            if label and label.get("name")
        )
        assignees = tuple(
            user.get("login", "")
            for user in (node.get("assignees") or {}).get("nodes", [])
            if user and user.get("login")
        )
        comments_connection = node.get("comments") or {}
        comments = tuple(
            Comment(
                body=comment.get("bodyText", ""),
                created_at=parse_datetime(comment.get("createdAt")),
                author=(comment.get("author") or {}).get("login", ""),
                author_association=comment.get("authorAssociation", "NONE"),
            )
            for comment in comments_connection.get("nodes", [])
            if comment
        )
        positive_reactions = sum(
            (group.get("users") or {}).get("totalCount", 0)
            for group in node.get("reactionGroups") or []
            if group and group.get("content") in {"THUMBS_UP", "HEART", "HOORAY", "ROCKET"}
        )
        return cls(
            repository=repository.get("nameWithOwner", ""),
            number=int(node.get("number", 0)),
            title=node.get("title", ""),
            url=node.get("url", ""),
            created_at=parse_datetime(node.get("createdAt")),
            updated_at=parse_datetime(node.get("updatedAt")),
            stars=int(repository.get("stargazerCount", 0)),
            repo_pushed_at=parse_datetime(repository.get("pushedAt")),
            labels=labels,
            assignees=assignees,
            comments=comments,
            comment_count=int(comments_connection.get("totalCount", len(comments))),
            positive_reactions=positive_reactions,
            language=(repository.get("primaryLanguage") or {}).get("name", ""),
        )


@dataclass(frozen=True)
class RankedIssue:
    """An issue plus its transparent ranking details."""

    issue: Issue
    score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)
    claim_evidence: str | None = None
