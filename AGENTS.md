# Project guide

## Purpose and architecture

`gh-issue-scout` is a dependency-free GitHub CLI extension that finds recent, active, and apparently unclaimed issues. The executable delegates to the `issue_scout` Python package. `github.py` retrieves issue metadata through the authenticated `gh` CLI, `query.py` builds searches, `ranking.py` detects claims and scores candidates, and `output.py` renders terminal, Markdown, or JSON results.

## Run, build, and test

- Run locally: `./gh-issue-scout --help`
- Run tests: `python3 -m unittest discover -v`
- Compile check: `python3 -m compileall -q issue_scout tests gh-issue-scout`
- Install as an extension from a checkout: `gh extension install .`

There is no build step and no third-party Python dependency.

## Current status

Version 0.1.0 is publicly released. Remote installation through GitHub CLI and live GraphQL searches are verified. Core search, ranking, claim detection, terminal output, Markdown output, JSON output, and browser opening are implemented.

## Recent changes

- Added deterministic scoring based on freshness, repository activity, stars, discussion size, labels, reactions, and maintainer participation.
- Added recent claim detection for assignments and common claim phrases.
- Added a repeatable excluded-label search filter for removing blocked or noisy workflows.
- Added an optional issue-activity cutoff through `--updated-within`.
- Added tests, cross-platform CI, security notes, and contributor documentation.
- Published the repository and v0.1.0 release with GitHub CLI extension discovery metadata.

## Project constraints

- Keep source code, documentation, metadata, and user-facing copy in English.
- Support Python 3.10 and newer.
- Keep runtime dependencies at zero.
- Keep ranking deterministic, documented, and explainable.
- Invoke `gh` without a shell and never read GitHub token files directly.
- Preserve JSON field names once released unless a major version documents the break.

## Known issues and next steps

- GitHub GraphQL limits each scan to 100 fetched candidates.
- Claim detection inspects only the latest 20 comments and cannot understand every phrasing.
- GitHub Enterprise Server remains untested.
- Consider pagination and user-configurable scoring weights after the first release.

## Do not

- Do not add LLM-based ranking, telemetry, advertising, or an external service.
- Do not hide ranking weights or claim-detection behavior.
- Do not execute issue text or interpolate it into a shell command.
- Do not automate claiming, commenting on, or assigning issues.
