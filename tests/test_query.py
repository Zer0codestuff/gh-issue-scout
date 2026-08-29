from datetime import datetime, timezone
from unittest import TestCase

from issue_scout.query import build_query, quote_value


class QueryTests(TestCase):
    def test_default_query_targets_recent_unassigned_good_first_issues(self) -> None:
        query = build_query(now=datetime(2026, 8, 29, tzinfo=timezone.utc))

        self.assertEqual(
            query,
            'is:issue is:open archived:false no:assignee label:"good first issue" '
            "created:>=2026-05-31 sort:created-desc",
        )

    def test_filters_and_extra_query_are_composed(self) -> None:
        query = build_query(
            keywords=["parser"],
            labels=["help wanted"],
            language="C++",
            repository="owner/repo",
            include_assigned=True,
            extra_query="-label:blocked",
            max_age_days=30,
            now=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )

        self.assertEqual(
            query,
            'is:issue is:open archived:false label:"help wanted" language:C++ '
            "repo:owner/repo created:>=2026-07-30 parser -label:blocked sort:created-desc",
        )

    def test_repo_and_org_are_mutually_exclusive(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be used together"):
            build_query(repository="owner/repo", organization="owner")

    def test_quote_value_removes_embedded_quotes(self) -> None:
        self.assertEqual(quote_value('good "first" issue'), '"good first issue"')
