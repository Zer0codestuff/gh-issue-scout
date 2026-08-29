from datetime import datetime, timedelta, timezone
from unittest import TestCase

from issue_scout.models import Comment, Issue
from issue_scout.ranking import find_claim, human_count, rank_issue


NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


def issue(**overrides: object) -> Issue:
    values: dict[str, object] = {
        "repository": "octo/example",
        "number": 42,
        "title": "Improve parser errors",
        "url": "https://github.com/octo/example/issues/42",
        "created_at": NOW - timedelta(days=2),
        "updated_at": NOW - timedelta(days=1),
        "stars": 2_500,
        "repo_pushed_at": NOW - timedelta(days=1),
        "labels": ("good first issue", "help wanted"),
        "comment_count": 0,
    }
    values.update(overrides)
    return Issue(**values)  # type: ignore[arg-type]


class RankingTests(TestCase):
    def test_fresh_active_issue_scores_high(self) -> None:
        ranked = rank_issue(issue(), now=NOW)

        self.assertGreaterEqual(ranked.score, 85)
        self.assertIn("repo pushed recently", ranked.reasons)
        self.assertIsNone(ranked.claim_evidence)

    def test_recent_claim_comment_is_detected(self) -> None:
        candidate = issue(
            comments=(
                Comment(
                    body="I would like to work on this issue.",
                    created_at=NOW - timedelta(days=1),
                    author="alice",
                ),
            ),
            comment_count=1,
        )

        self.assertEqual(find_claim(candidate, now=NOW), "@alice: I would like to work")
        self.assertEqual(rank_issue(candidate, now=NOW).score, 0)

    def test_old_claim_is_ignored(self) -> None:
        candidate = issue(
            comments=(
                Comment(
                    body="I am working on this.",
                    created_at=NOW - timedelta(days=60),
                    author="alice",
                ),
            ),
            comment_count=1,
        )

        self.assertIsNone(find_claim(candidate, now=NOW, window_days=30))

    def test_bot_claim_is_ignored(self) -> None:
        candidate = issue(
            comments=(
                Comment(
                    body="Claimed by automation.",
                    created_at=NOW - timedelta(days=1),
                    author="triage[bot]",
                ),
            ),
            comment_count=1,
        )

        self.assertIsNone(find_claim(candidate, now=NOW))

    def test_human_count(self) -> None:
        self.assertEqual(human_count(999), "999")
        self.assertEqual(human_count(1_200), "1.2k")
        self.assertEqual(human_count(2_000_000), "2m")
