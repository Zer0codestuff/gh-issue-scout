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

    def test_excluded_labels_are_repeatable_and_safely_quoted(self) -> None:
        query = build_query(
            labels=["help wanted"],
            excluded_labels=["blocked", "needs info"],
            now=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )

        self.assertIn('label:"help wanted" -label:blocked -label:"needs info"', query)

    def test_updated_within_adds_activity_cutoff(self) -> None:
        query = build_query(
            updated_within_days=7,
            now=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )

        self.assertIn("created:>=2026-05-31 updated:>=2026-08-22", query)

    def test_updated_within_rejects_non_positive_days(self) -> None:
        with self.assertRaisesRegex(ValueError, "--updated-within must be at least 1 day"):
            build_query(updated_within_days=0)

    def test_quote_value_removes_embedded_quotes(self) -> None:
        self.assertEqual(quote_value('good "first" issue'), '"good first issue"')
