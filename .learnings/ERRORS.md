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

## [ERR-20260606-001] csv_scoreboard_truncation_recurrence

**Logged**: 2026-06-06T00:45:21+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Scoreboard CSV rewrite failed again on a parsed `None` extra-field key after opening the file for output, truncating `experiments/scoreboard.csv`.

### Error
```text
ValueError: dict contains fields not in fieldnames: None
```

### Context
- Command attempted: Python `csv.DictReader`/`csv.DictWriter` update for `experiments/research_queue.csv` and `experiments/scoreboard.csv`.
- Queue update completed before the scoreboard write failed.
- Scoreboard had to be reconstructed from `HEAD:experiments/scoreboard.csv` plus the intended new row.

### Suggested Fix
Never open scoreboard for writing until all rows have been normalized. Drop `None` keys from every row and validate fieldnames in memory before truncating the file.

### Metadata
- Reproducible: yes
- Related Files: experiments/scoreboard.csv, experiments/research_queue.csv
- See Also: ERR-20260605-002

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

## [ERR-20260606-002] missing_make_precommit_target

**Logged**: 2026-06-06T08:53:18+08:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
The AutoDrift Makefile does not define a `precommit` target.

### Error
```text
make: *** No rule to make target 'precommit'.  Stop.
```

### Context
- Command attempted: `make precommit`
- Purpose: run a final repository gate after M2839 audit and M2840 synthesis manifest updates.
- Actual Makefile gates are `check-diff`, `research-validate`, `test-light`, and full `test`.

### Suggested Fix
Use the Makefile targets that exist in this repository. For this research harness, run `make check-diff`, `make research-validate`, and `make test-light` unless a task specifically requires full `make test`.

### Metadata
- Reproducible: yes
- Related Files: Makefile

---

## [ERR-20260606-003] manifest_actual_progress_type_enum

**Logged**: 2026-06-06T09:06:31+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
AutoDrift manifest validation rejects non-enum `local_search_guard.actual_progress_type` values.

### Error
```text
error: m2841-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-synthesis-selected-next-route-design: local_search_guard.actual_progress_type must be one of ['design_only', 'evidence_reanalysis', 'new_baseline_comparison', 'new_closed_loop_data', 'new_dataset_or_panel', 'new_scenario_distribution', 'new_tool_or_infra', 'repair_only', 'result_audit', 'synthesis_decision']
```

### Context
- Command attempted: `make research-validate`
- Invalid value used: `route_design`
- Correct value for design-only route milestones: `design_only`

### Suggested Fix
When adding new process manifests, use the validator enum for `actual_progress_type`; descriptive route labels should stay in `branch`, `evidence_axis`, or milestone text.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m2841-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-synthesis-selected-next-route-design.json

---
