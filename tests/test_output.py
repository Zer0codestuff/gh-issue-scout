from datetime import datetime, timezone
from unittest import TestCase

from issue_scout.models import Issue, RankedIssue
from issue_scout.output import render_json, render_markdown


class OutputTests(TestCase):
    def setUp(self) -> None:
        issue = Issue(
            repository="octo/repo",
            number=3,
            title="[BUG] Pipe | and brackets [work]",
            url="https://github.com/octo/repo/issues/3",
            created_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
            updated_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
            stars=120,
            repo_pushed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        self.ranked = RankedIssue(issue=issue, score=88.5, reasons=("fresh",))

    def test_markdown_escapes_table_and_link_syntax(self) -> None:
        output = render_markdown([self.ranked])

        self.assertIn(r"\[BUG\] Pipe \| and brackets \[work\]", output)

    def test_json_contains_stable_fields(self) -> None:
        output = render_json([self.ranked])

        self.assertIn('"score": 88.5', output)
        self.assertIn('"repository": "octo/repo"', output)
