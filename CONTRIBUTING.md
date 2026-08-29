# Contributing

Contributions should keep Issue Scout fast, inspectable, and dependency-free.

## Workflow

1. Open an issue for behavior changes that affect ranking or claim detection.
2. Fork the repository and create a focused branch.
3. Add or update tests for every behavior change.
4. Run the checks below.
5. Open a pull request that explains the user-visible effect and any scoring tradeoff.

```bash
python3 -m unittest discover -v
python3 -m compileall -q issue_scout tests gh-issue-scout
```

Ranking changes must remain deterministic and documented in `README.md`. Avoid network calls outside GitHub, hidden heuristics, and model-based scoring.
