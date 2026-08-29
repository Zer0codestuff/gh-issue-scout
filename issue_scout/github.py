"""GitHub GraphQL access through the authenticated gh CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from issue_scout.models import Issue


GRAPHQL_QUERY = r"""
query IssueScout($searchQuery: String!, $limit: Int!) {
  search(query: $searchQuery, type: ISSUE, first: $limit) {
    issueCount
    nodes {
      ... on Issue {
        number
        title
        url
        createdAt
        updatedAt
        labels(first: 20) { nodes { name } }
        assignees(first: 5) { nodes { login } }
        comments(last: 20) {
          totalCount
          nodes {
            bodyText
            createdAt
            author { login }
            authorAssociation
          }
        }
        reactionGroups { content users { totalCount } }
        repository {
          nameWithOwner
          stargazerCount
          pushedAt
          primaryLanguage { name }
        }
      }
    }
  }
  rateLimit { cost remaining resetAt }
}
"""


class GitHubError(RuntimeError):
    """A clear error from gh or GitHub GraphQL."""


@dataclass(frozen=True)
class SearchResult:
    """Issues plus query and rate-limit metadata."""

    issues: tuple[Issue, ...]
    total_count: int
    rate_cost: int
    rate_remaining: int
    rate_reset_at: str


Runner = Callable[..., subprocess.CompletedProcess[str]]


def search_issues(
    search_query: str,
    fetch_limit: int,
    *,
    runner: Runner = subprocess.run,
) -> SearchResult:
    """Run the GraphQL search using the current gh authentication."""
    if shutil.which("gh") is None:
        raise GitHubError("GitHub CLI is required. Install gh and run 'gh auth login'.")
    limit = max(1, min(100, fetch_limit))
    command = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={GRAPHQL_QUERY}",
        "-F",
        f"searchQuery={search_query}",
        "-F",
        f"limit={limit}",
    ]
    completed = runner(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown gh error"
        raise GitHubError(detail)
    try:
        payload: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise GitHubError("gh returned invalid JSON") from error
    if payload.get("errors"):
        messages = "; ".join(error.get("message", "GraphQL error") for error in payload["errors"])
        raise GitHubError(messages)
    data = payload.get("data") or {}
    search = data.get("search") or {}
    nodes = search.get("nodes") or []
    rate = data.get("rateLimit") or {}
    return SearchResult(
        issues=tuple(Issue.from_graphql(node) for node in nodes if node),
        total_count=int(search.get("issueCount", len(nodes))),
        rate_cost=int(rate.get("cost", 0)),
        rate_remaining=int(rate.get("remaining", 0)),
        rate_reset_at=rate.get("resetAt", ""),
    )
