"""Terminal, Markdown, and JSON output."""

from __future__ import annotations

import json
import os
import shutil
import sys
import textwrap
from datetime import datetime, timezone

from issue_scout.models import RankedIssue
from issue_scout.ranking import days_since, human_count


def _color(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def render_terminal(results: list[RankedIssue], *, color: bool = True) -> str:
    """Render a readable terminal list."""
    enabled = color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    width = max(72, shutil.get_terminal_size((100, 24)).columns)
    lines: list[str] = []
    now = datetime.now(timezone.utc)
    for index, ranked in enumerate(results, start=1):
        issue = ranked.issue
        age = max(1, round(days_since(issue.created_at, now)))
        prefix = _color(f"{index:>2}. {ranked.score:>5.1f}", "1;32", enabled)
        identity = _color(f"{issue.repository}#{issue.number}", "1;36", enabled)
        metadata = f"{human_count(issue.stars)} stars | {age}d | {issue.comment_count} comments"
        lines.append(f"{prefix}  {identity}  {metadata}")
        lines.append(f"    {textwrap.shorten(issue.title, width=width - 4, placeholder='...')}")
        if ranked.reasons:
            lines.append(f"    why: {', '.join(ranked.reasons)}")
        if ranked.claim_evidence:
            lines.append(_color(f"    claimed: {ranked.claim_evidence}", "33", enabled))
        lines.append(f"    {issue.url}")
    return "\n".join(lines)


def render_markdown(results: list[RankedIssue]) -> str:
    """Render a Markdown table suitable for notes or an issue."""
    lines = [
        "| Score | Repository | Issue | Stars | Comments | Why |",
        "| ---: | --- | --- | ---: | ---: | --- |",
    ]
    for ranked in results:
        issue = ranked.issue
        title = (
            issue.title.replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        why = ", ".join(ranked.reasons).replace("|", "\\|")
        lines.append(
            f"| {ranked.score:.1f} | `{issue.repository}` | "
            f"[#{issue.number}: {title}]({issue.url}) | {issue.stars} | "
            f"{issue.comment_count} | {why} |"
        )
    return "\n".join(lines)


def render_json(results: list[RankedIssue]) -> str:
    """Render stable machine-readable output."""
    payload = [
        {
            "score": ranked.score,
            "repository": ranked.issue.repository,
            "number": ranked.issue.number,
            "title": ranked.issue.title,
            "url": ranked.issue.url,
            "created_at": ranked.issue.created_at.isoformat(),
            "updated_at": ranked.issue.updated_at.isoformat(),
            "stars": ranked.issue.stars,
            "language": ranked.issue.language,
            "labels": list(ranked.issue.labels),
            "comment_count": ranked.issue.comment_count,
            "reasons": list(ranked.reasons),
            "claim_evidence": ranked.claim_evidence,
        }
        for ranked in results
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)
