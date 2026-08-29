"""Command-line interface for Issue Scout."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone

from issue_scout import __version__
from issue_scout.github import GitHubError, search_issues
from issue_scout.output import render_json, render_markdown, render_terminal
from issue_scout.query import build_query
from issue_scout.ranking import days_since, rank_issue


def parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    command = argparse.ArgumentParser(
        prog="gh issue-scout",
        description="Find fresh, active, and apparently unclaimed GitHub issues.",
    )
    command.add_argument("keywords", nargs="*", help="optional search terms")
    command.add_argument("--label", action="append", help="label to require; repeat for multiple labels")
    command.add_argument("--language", help="repository primary language")
    command.add_argument("--repo", help="limit to OWNER/REPOSITORY")
    command.add_argument("--org", help="limit to one organization")
    command.add_argument("--query", help="append raw GitHub search qualifiers")
    command.add_argument("--min-stars", type=int, default=50, help="minimum repository stars (default: 50)")
    command.add_argument("--max-age", type=int, default=90, help="maximum issue age in days (default: 90)")
    command.add_argument(
        "--max-repo-idle",
        type=int,
        default=365,
        help="exclude repositories not pushed to within this many days (default: 365)",
    )
    command.add_argument("--claim-window", type=int, default=30, help="days in which claim comments count (default: 30)")
    command.add_argument("--include-claimed", action="store_true", help="show issues with recent claim evidence")
    command.add_argument("--include-assigned", action="store_true", help="search assigned issues too")
    command.add_argument("--limit", type=int, default=12, help="number of results (default: 12)")
    command.add_argument("--fetch", type=int, help="GitHub candidates to fetch before ranking (max: 100)")
    command.add_argument("--show-query", action="store_true", help="print the generated GitHub query to stderr")
    command.add_argument("--open", action="store_true", help="open the top result in a browser")
    command.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    output = command.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="emit JSON")
    output.add_argument("--markdown", action="store_true", help="emit a Markdown table")
    command.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return command


def main(argv: list[str] | None = None) -> int:
    """Run Issue Scout and return a process exit code."""
    arguments = parser().parse_args(argv)
    if arguments.limit < 1:
        return _argument_error("--limit must be at least 1")
    if arguments.min_stars < 0:
        return _argument_error("--min-stars cannot be negative")
    if arguments.claim_window < 1:
        return _argument_error("--claim-window must be at least 1")
    if arguments.max_repo_idle < 1:
        return _argument_error("--max-repo-idle must be at least 1")
    if arguments.fetch is not None and not 1 <= arguments.fetch <= 100:
        return _argument_error("--fetch must be between 1 and 100")

    try:
        search_query = build_query(
            keywords=arguments.keywords,
            labels=arguments.label,
            language=arguments.language,
            repository=arguments.repo,
            organization=arguments.org,
            max_age_days=arguments.max_age,
            include_assigned=arguments.include_assigned,
            extra_query=arguments.query,
        )
    except ValueError as error:
        return _argument_error(str(error))

    if arguments.show_query:
        print(f"query: {search_query}", file=sys.stderr)
    fetch_limit = arguments.fetch or min(100, max(30, arguments.limit * 5))
    try:
        search = search_issues(search_query, fetch_limit)
    except GitHubError as error:
        print(f"gh issue-scout: {error}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    ranked = []
    for issue in search.issues:
        if issue.stars < arguments.min_stars:
            continue
        if days_since(issue.repo_pushed_at, now) > arguments.max_repo_idle:
            continue
        candidate = rank_issue(issue, now=now, claim_window_days=arguments.claim_window)
        if candidate.claim_evidence and not arguments.include_claimed:
            continue
        ranked.append(candidate)
    ranked.sort(key=lambda candidate: (-candidate.score, -candidate.issue.stars, candidate.issue.url))
    results = ranked[: arguments.limit]

    if arguments.json:
        print(render_json(results))
    elif arguments.markdown:
        print(render_markdown(results))
    elif results:
        print(render_terminal(results, color=not arguments.no_color))
    else:
        print("No matching, apparently unclaimed issues found.")

    print(
        f"Scanned {len(search.issues)} of {search.total_count} matches; "
        f"GraphQL cost {search.rate_cost}, {search.rate_remaining} remaining.",
        file=sys.stderr,
    )
    if arguments.open and results:
        subprocess.run(["gh", "issue", "view", results[0].issue.url, "--web"], check=False)
    return 0


def _argument_error(message: str) -> int:
    print(f"gh issue-scout: {message}", file=sys.stderr)
    return 2
