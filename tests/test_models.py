from unittest import TestCase

from issue_scout.models import Issue


class ModelTests(TestCase):
    def test_graphql_node_is_normalized(self) -> None:
        parsed = Issue.from_graphql(
            {
                "number": 7,
                "title": "Fix it",
                "url": "https://example.test/7",
                "createdAt": "2026-08-20T00:00:00Z",
                "updatedAt": "2026-08-21T00:00:00Z",
                "labels": {"nodes": [{"name": "good first issue"}]},
                "assignees": {"nodes": []},
                "comments": {
                    "totalCount": 1,
                    "nodes": [
                        {
                            "bodyText": "Needs a test",
                            "createdAt": "2026-08-21T00:00:00Z",
                            "author": None,
                            "authorAssociation": "MEMBER",
                        }
                    ],
                },
                "reactionGroups": [
                    {"content": "THUMBS_UP", "users": {"totalCount": 3}},
                    {"content": "CONFUSED", "users": {"totalCount": 9}},
                ],
                "repository": {
                    "nameWithOwner": "octo/repo",
                    "stargazerCount": 100,
                    "pushedAt": "2026-08-22T00:00:00Z",
                    "primaryLanguage": {"name": "Python"},
                },
            }
        )

        self.assertEqual(parsed.repository, "octo/repo")
        self.assertEqual(parsed.positive_reactions, 3)
        self.assertEqual(parsed.comments[0].author, "")
        self.assertEqual(parsed.language, "Python")
