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

## [ERR-20260607-004] branch_cadence_requires_synthesis_manifest

**Logged**: 2026-06-07T14:34:31+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
AutoDrift research validation rejects another ordinary process milestone once branch cadence requires synthesis.

### Error
```text
error: m3013-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-result-audit: workflow_synthesis.branch 'engineering_controller_route_a_post_residual_stop_source_axis_expansion' has 11 non-synthesis milestones since the last synthesis; cadence is 10, so add a gate_tier='process' synthesis milestone with workflow_synthesis.synthesis_decision before continuing
```

### Context
- Command attempted: `make research-validate`
- M3013 was initially registered as a plain result audit after M3012 env materialization.
- The branch had already crossed the synthesis cadence, so the next process milestone must be a synthesis decision milestone.

### Suggested Fix
When `research-validate` reports branch cadence exhaustion, convert the next process audit into an explicit synthesis milestone with `workflow_synthesis.synthesis_decision`, `synthesis_artifact`, and `synthesis_questions`, or insert a separate synthesis before further narrow design/audit work.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3013-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-result-audit.json, src/autodrift/research_validate.py

---

## [ERR-20260607-003] csv_writer_crlf_line_endings

**Logged**: 2026-06-07T14:21:50+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
Python `csv.DictWriter` rewrote AutoDrift CSV ledgers with CRLF line endings, causing `git diff --check` to report trailing whitespace across the full file.

### Error
```text
experiments/research_queue.csv:1: trailing whitespace.
experiments/scoreboard.csv:2931: trailing whitespace.
```

### Context
- Command attempted: `git diff --check`
- Files updated with `csv.DictWriter(..., newline='')` but without `lineterminator='\\n'`.
- The fix was to normalize `\\r\\n` to `\\n` before rerunning `git diff --check`.

### Suggested Fix
When writing AutoDrift CSV ledgers from Python, pass `lineterminator='\\n'` to `csv.DictWriter` or normalize line endings immediately after writing.

### Metadata
- Reproducible: yes
- Related Files: experiments/research_queue.csv, experiments/scoreboard.csv

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

## [ERR-20260607-001] manifest_missing_failure_types

**Logged**: 2026-06-07T00:43:53+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
AutoDrift process-v2 manifest validation rejects new manifests that omit `failure_types`.

### Error
```text
error: m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight: process-v2 manifest missing fields ['failure_types']
```

### Context
- Command attempted: `make research-validate`
- The M2916 manifest was hand-written from a nearby template but omitted the top-level process-v2 `failure_types` list.
- The fix was to add the standard harness failure taxonomy list before rerunning validation.

### Suggested Fix
When adding a new AutoDrift manifest, copy the complete process-v2 skeleton first: `gate_tier`, `promotion_decision`, `failure_types`, `lineage`, `review_artifact`, `public_gates`, `private_holdout_policy`, and `forbidden_shortcuts`.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m2916-engineering-controller-route-a-dependency-facing-evidence-surface-execution-admission-materialization-preflight.json

---

## [ERR-20260607-002] research_state_command_parallel_race

**Logged**: 2026-06-07T12:19:55+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
AutoDrift research state commands that read or update `experiments/research_status.json` should not be run in parallel.

### Error
```text
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### Context
- Commands attempted in parallel: `make research-validate`, `make research-plan`, and `make research-review TASK=...`
- `research-plan` rewrote `experiments/research_status.json` while `research-validate` was reading it, causing a transient empty-file JSON parse.
- The Makefile `research-review` target also ignored `TASK=...` and used the default M90 manifest.

### Suggested Fix
Run AutoDrift research state commands serially when they read or write queue/status/log files. For review generation, pass the manifest path explicitly instead of assuming `TASK=...` is honored.

### Metadata
- Reproducible: yes
- Related Files: Makefile, experiments/research_status.json, src/autodrift/research_validate.py, src/autodrift/research_cycle.py

---

## [ERR-20260607-003] autodrift_research_status_wrong_path

**Logged**: 2026-06-07T14:49:26+08:00
**Priority**: low
**Status**: pending
**Area**: docs

### Summary
AutoDrift live research status is under `experiments/research_status.json`, not the repository root.

### Error
```text
sed: can't read research_status.json: No such file or directory
```

### Context
- Command attempted: `sed -n '1,260p' experiments/manifests/m3015-...json && sed -n '1,220p' research_status.json`
- The harness skill correctly points at `experiments/research_status.json`; the root-level path came from stale turn context.

### Suggested Fix
For AutoDrift research-loop checks, read `experiments/research_status.json` and `experiments/research_queue.csv` directly.

### Metadata
- Reproducible: yes
- Related Files: experiments/research_status.json, experiments/research_queue.csv

---

## [ERR-20260607-004] autodrift_research_log_wrong_path

**Logged**: 2026-06-07T14:51:20+08:00
**Priority**: low
**Status**: pending
**Area**: docs

### Summary
AutoDrift does not have `experiments/research_log.md`; current milestone tracking uses queue, status, scoreboard, reviews, docs, and manifests.

### Error
```text
rg: experiments/research_log.md: No such file or directory (os error 2)
```

### Context
- Command attempted to search `experiments/research_log.md` along with queue and scoreboard.
- The stale path came from compacted context, not the live repository tree.

### Suggested Fix
Search live files first with `rg --files experiments docs`, then update only existing ledger files.

### Metadata
- Reproducible: yes
- Related Files: experiments/research_queue.csv, experiments/research_status.json, experiments/scoreboard.csv

---

## [ERR-20260607-005] git_diff_check_trailing_blank_line

**Logged**: 2026-06-07T15:07:19+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
`git diff --check` rejects a new blank line at EOF in `docs/research-log.md`.

### Error
```text
docs/research-log.md:53603: new blank line at EOF.
```

### Context
- Command attempted: `git diff --check`
- The M3015 research-log note replacement left a trailing blank line at the end of the markdown file.

### Suggested Fix
After scripted markdown ledger updates, run `git diff --check` and remove EOF-only blank lines before validation.

### Metadata
- Reproducible: yes
- Related Files: docs/research-log.md

---

## [ERR-20260607-006] autodrift_training_stage_stage_enum

**Logged**: 2026-06-07T15:19:02+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
AutoDrift manifest validation rejects non-enum `training_stage.stage` values.

### Error
```text
error: m3018-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-preflight: training_stage.stage must be one of ['action_grounding_posttrain', 'behavior_pretrain', 'capability_pretrain', 'evaluation_only', 'guarded_rl', 'infrastructure', 'process']
```

### Context
- Command attempted: `make research-validate`
- Invalid value used: `analysis_only`
- Correct value for no-execution materialization infrastructure milestones: `infrastructure`

### Suggested Fix
When creating AutoDrift manifests, use only the validator enum for `training_stage.stage`; put descriptive analysis scope in `stage_objective` and `local_search_guard.actual_progress_type`.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3018-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-preflight.json

---
