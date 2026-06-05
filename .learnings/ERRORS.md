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

## [ERR-20260605-002] csv_dictwriter_extra_fields_and_line_endings

**Logged**: 2026-06-05T16:05:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Bulk CSV rewrite for research queue and scoreboard can create noisy full-file diffs or truncate output if `DictWriter` receives parsed extra fields.

### Error
```text
ValueError: dict contains fields not in fieldnames: None
```

### Context
- Command attempted: Python `csv.DictReader`/`csv.DictWriter` rewrite of `experiments/research_queue.csv` and `experiments/scoreboard.csv`.
- The queue rewrite used the default CSV writer line terminator and produced a full-file diff.
- The scoreboard rewrite opened the file for writing before failing, leaving a partial file that had to be restored from `HEAD`.

### Suggested Fix
For repository CSV status files, restore from `HEAD` before replaying intended row changes after a failed bulk write, set `lineterminator='\n'`, and remove any `None` extra-field keys before `DictWriter.writerow(s)`.

### Metadata
- Reproducible: yes
- Related Files: experiments/research_queue.csv, experiments/scoreboard.csv

---
