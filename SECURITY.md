# Security policy

## Reporting

Do not open a public issue for a vulnerability that could expose GitHub credentials or private repository metadata. Use GitHub private vulnerability reporting for this repository.

Include the affected version, a minimal reproduction, and the expected impact. Reports that only describe social-engineering or GitHub account compromise outside this extension are out of scope.

## Scope

Issue Scout invokes the installed `gh` executable without a shell and parses its JSON response. It does not read token files directly, persist API responses, or send telemetry.
