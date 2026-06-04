## [ERR-20260605-001] jq_command_missing

**Logged**: 2026-06-05T00:00:00+08:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
`jq` is not installed in the AutoDrift workspace environment.

### Error
```text
/bin/bash: line 1: jq: command not found
```

### Context
- Command attempted: `jq '{...}' runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/summary.json`
- Purpose: summarize M2714 JSON artifact after materialization.

### Suggested Fix
Use Python standard-library JSON extraction for repo-local checks unless `jq` availability has been verified.

### Metadata
- Reproducible: yes
- Related Files: runs/m2714_engineering_controller_route_a_current_m1690_exact_executable_reentry_panel/summary.json

---
