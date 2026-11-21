# Git Pre-Commit and Gitleaks

This reference explains how this repository uses Git pre-commit hooks and Gitleaks to catch
accidentally staged secrets before they are committed.

## What the tools do

- **Git hooks** run scripts at Git lifecycle points. A `pre-commit` hook runs before a commit is
  created.
- **pre-commit** installs and runs hooks declared in `.pre-commit-config.yaml`.
- **Gitleaks** detects credential-like values. This repository's hook scans staged changes, and
  blocks the commit when it finds a likely secret.

## Set up the hook

From the repository root, install the development dependency and register the Git hook:

```powershell
py -m pip install -r requirements-dev.txt
py -m pre_commit install
```

The configuration pins Gitleaks to `v8.30.1`. On its first run, pre-commit downloads and prepares
the hook environment. The hook then runs automatically on each `git commit`.

To validate the configuration:

```powershell
py -m pre_commit validate-config
```

To run Gitleaks manually, stage the changes you want checked and run:

```powershell
py -m pre_commit run gitleaks
```

The Gitleaks hook is configured with `--staged`; it scans the staged Git content, not the entire
repository history. `pre-commit run --all-files` does not turn this hook into a full-history scan.

## Respond to a finding

1. Do not commit the finding. Remove the credential from the staged change and re-stage the
   corrected file.
2. If the value was a real credential and has been exposed outside your machine, revoke or rotate
   it. Removing it from the latest change does not erase it from prior Git history.
3. Treat allowlisting as an exception that needs review. Prefer a narrow, documented exception for
   a confirmed false positive; never allowlist a real credential to make the check pass.

## What this does not replace

Git hooks run on a developer's machine and can be bypassed with `git commit --no-verify`. They are
an early warning, not an enforcement boundary. GitHub secret scanning and push protection provide
server-side checks; push protection blocks supported detected secrets before they are pushed.
Generic-pattern coverage is configured separately, so push protection does not necessarily block
every kind of secret.

## References

- [pre-commit documentation](https://pre-commit.com/)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [Gitleaks pre-commit hook definition](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml)
- [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)
- [GitHub secret scanning](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning)
