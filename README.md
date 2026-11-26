# sntb-nautobot-jobs

Nautobot Jobs for a **study lab** (ENAUTO / AUTOCOR practice). Synced into Nautobot 3.2 as a
Git repository with content type `extras.job`.

**Synthetic data only.** Every address is in `10.99.0.0/16`, every host is `syn-*`. This repo holds no
credentials, no real addresses and no real hostnames, and a test fails if one appears.

## Jobs

| Job | Does | Writes? |
|-----|------|---------|
| Synthetic fabric report | Lists devices with a tag (default `sntb-lab-synthetic`) and **fails** on: no devices, a non-`syn-*` name, no primary IP, a primary IP outside `10.99.0.0/16`, a duplicate primary IP, a device with no interfaces | No (`read_only`) |

The rules live in `jobs/fabric_logic.py` with no Nautobot import, so they run under plain `pytest`.
`jobs/fabric_report.py` is a thin wrapper that reads the database and calls them.

## Test

```bash
pip install pytest
pytest -q        # 8 mutants must each produce a problem; a meta-check proves the address rule is what fires
```

## Use in Nautobot

Add a Git repository (Extensibility, Git Repositories): remote URL of this repo, branch `main`,
provided contents `jobs`. No credentials are needed because the repo is public. After the sync, enable the
job in the Jobs list (Git-sourced jobs start disabled) and run it.
