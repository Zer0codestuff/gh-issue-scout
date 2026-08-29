# gh-issue-scout

Find GitHub issues that are fresh, active, and apparently still available.

Issue Scout is a dependency-free GitHub CLI extension. It searches real issues through your existing `gh` authentication, detects recent claim comments, and ranks the remaining candidates with transparent signals. No LLM, service account, tracking, or separate token is involved.

[![CI](https://github.com/Zer0codestuff/gh-issue-scout/actions/workflows/ci.yml/badge.svg)](https://github.com/Zer0codestuff/gh-issue-scout/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Install

Requirements: [GitHub CLI](https://cli.github.com/) authenticated with `gh auth login`, plus Python 3.10 or newer.

```bash
gh extension install Zer0codestuff/gh-issue-scout
```

Upgrade later with:

```bash
gh extension upgrade issue-scout
```

## Use

Run the default scan for recent, unassigned `good first issue` tickets:

```bash
gh issue-scout
```

Focus the search:

```bash
gh issue-scout parser --language Python --min-stars 500
gh issue-scout --org home-assistant --label "help wanted"
gh issue-scout --repo rust-lang/rust --label E-easy --max-age 30
```

Generate output for another tool:

```bash
gh issue-scout --json > candidates.json
gh issue-scout --markdown > candidates.md
```

Useful controls:

```text
--claim-window DAYS   Treat recent claim comments as active for this long
--include-claimed     Show claimed candidates and their evidence
--include-assigned    Include assigned issues in the GitHub search
--max-repo-idle DAYS  Exclude repositories without a recent push
--query QUALIFIERS    Append raw GitHub search qualifiers
--show-query          Print the exact generated search query
--open                Open the top result in a browser
```

Run `gh issue-scout --help` for the complete list.

## What the score means

The score is deterministic and capped at 100. It favors:

| Signal | Maximum effect |
| --- | ---: |
| Recently opened issue | +28 |
| Recently pushed repository | +22 |
| Repository stars | +20 |
| Low comment count | +15 |
| `good first issue` label | +10 |
| `help wanted` label | +5 |
| Positive reactions | +5 |
| Maintainer participation | +5 |
| Assignment or recent claim comment | -100 |

Claim detection checks the latest 20 comments for phrases such as "I would like to work on this" within the configured window. It is intentionally conservative, but language is messy. Always read the full thread and ask the maintainer before investing substantial work.

Issue Scout does not judge whether a change is valuable or appropriate. It removes the first layer of stale and already-claimed results so you can make that decision faster.

## Privacy and permissions

Issue Scout shells out to `gh api graphql`. Requests go directly to GitHub using the account already authenticated in GitHub CLI. The extension stores nothing and sends no telemetry.

It needs only read access to public issue and repository metadata. Private repositories can appear if your current `gh` token can read them and your query targets them.

## Develop

The project uses only the Python standard library.

```bash
python3 -m unittest discover -v
python3 -m compileall -q issue_scout tests gh-issue-scout
./gh-issue-scout --show-query --limit 5
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

## Limits

- GitHub GraphQL returns at most 100 candidates per scan. Issue Scout ranks that fetched window, not every matching issue on GitHub.
- Only the latest 20 comments are inspected for claim language.
- Repository stars and activity are useful triage signals, not guarantees of maintainer responsiveness.
- GitHub Enterprise Server has not been tested yet.

If Issue Scout saves you time, starring the repository helps other contributors find it.

## License

[MIT](LICENSE)
