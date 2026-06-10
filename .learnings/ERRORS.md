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
## [ERR-20260608-002] pytest_fixture_import_path

**Logged**: 2026-06-08T13:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Debug helper tried to import a test file via `tests.<module>` even though this repository's tests directory is not a Python package.

### Error
```text
ModuleNotFoundError: No module named 'tests.test_engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_materialization_preflight'
```

### Context
- Command attempted: ad hoc Python snippet to inspect failing M3187 gates.
- The test file exists but `tests/` has no package import path for direct dotted import.

### Suggested Fix
Use `importlib.util.spec_from_file_location` or duplicate the small fixture in the debug snippet when inspecting tests in this repo.

### Metadata
- Reproducible: yes
- Related Files: tests/test_engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_spec_materialization_preflight.py

---
## [ERR-20260608-001] autodrift_artifact_filename_guess

**Logged**: 2026-06-08T13:13:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
Guessed an M3153 artifact filename instead of checking the summary path map first.

### Error
```text
head: cannot open 'runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight/counterfactual_replay_rows.csv' for reading: No such file or directory
```

### Context
- Command attempted: `head -n 10 .../counterfactual_replay_rows.csv`
- Actual artifact is `counterfactual_replay_comparison_rows.csv`, listed by `summary.json` and `ls`.

### Suggested Fix
When inspecting AutoDrift run artifacts, read `summary.json.paths` or list the run directory before guessing long generated filenames.

### Metadata
- Reproducible: yes
- Related Files: runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight/summary.json

---
## [ERR-20260608-001] research_validate_manifest_stage_scoreboard

**Logged**: 2026-06-08T01:15:00Z
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
`make research-validate` failed after M3147/M3148 because one manifest used a non-enumerated training stage and completed queue tasks lacked scoreboard rows.

### Error
```text
error: m3147...: training_stage.stage must be one of ['action_grounding_posttrain', 'behavior_pretrain', 'capability_pretrain', 'evaluation_only', 'guarded_rl', 'infrastructure', 'process']
error: m3147...: completed enforced task missing scoreboard row
error: m3148...: completed enforced task missing scoreboard row
```

### Context
- Command attempted: `make research-validate`
- M3147 used `training_stage.stage: diagnostic_materialization`, which is descriptive but not in the validator enum.
- M3147 and M3148 had completed queue rows but no matching `experiments/scoreboard.csv` rows.

### Suggested Fix
Use one of the validator stage enum values such as `infrastructure` or `process`; after completing manually queued milestones, add matching scoreboard rows before `make research-validate`.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3147-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-action-delta-coverage-diagnostic-materialization-preflight.json, experiments/scoreboard.csv

---
## [ERR-20260608-001] shell_json_inspection_jq_missing

**Logged**: 2026-06-08T08:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The local AutoDrift shell environment does not have `jq`, so JSON summary inspection should use Python or repository readers.

### Error
```text
/bin/bash: line 1: jq: command not found
```

### Context
- Command attempted: `jq '{status_pass, gate_matrix_pass, ...}' runs/m3137_.../summary.json`
- The failure happened while inspecting M3137 output, not during the research runner.

### Suggested Fix
Use `python - <<'PY'` or repo JSON helpers for structured JSON reads unless `jq` availability has been verified.

### Metadata
- Reproducible: yes
- Related Files: runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/summary.json

---
## [ERR-20260608-002] autodrift_research_status_parallel_plan_validate

**Logged**: 2026-06-08T06:20:03+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Running `make research-validate` in parallel with `make research-plan` can make the validator read `experiments/research_status.json` during a status rewrite.

### Error
```text
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

### Context
- Commands attempted in parallel: `make research-validate` and `make research-plan`
- `research-plan` updates `experiments/research_status.json`; `research-validate` read it while it was transiently empty.
- The status file was immediately valid afterward and pointed to M3121.

### Suggested Fix
Run AutoDrift status-mutating commands serially. Do not parallelize `research-plan`, `research-run-next`, or other `research_cycle` status writers with `research-validate`.

### Metadata
- Reproducible: yes
- Related Files: experiments/research_status.json, src/autodrift/research_cycle.py, src/autodrift/research_validate.py

---
## [ERR-20260608-001] autodrift_local_search_guard_reset_after_synthesis

**Logged**: 2026-06-08T05:58:30+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
AutoDrift materialization manifests after a concrete synthesis should not carry stale same-failure repeat counts that force the validator to require another synthesis decision.

### Error
```text
error: m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-stability-recovery-repair-materialization-preflight: local_search_guard requires a workflow synthesis decision when local_search_risk is high or repeat/repair counts reach 3
```

### Context
- Command attempted: `make research-validate`
- M3117 was the concrete synthesis decision.
- M3118 is the next materialization on the selected route, but its `local_search_guard.same_failure_repeat_count` was copied as 4.

### Suggested Fix
After a concrete synthesis routes to a new materialization mechanism, reset materialization-local repeat counters to the new branch scope unless the materialization itself is another synthesis milestone.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-stability-recovery-repair-materialization-preflight.json

---

## [ERR-20260607-009] autodrift_trace_artifact_schema_assumption

**Logged**: 2026-06-07T17:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
AutoDrift trace audits should inspect live CSV and NPZ schemas before assuming legacy artifact names or tensor keys.

### Error
```text
FileNotFoundError: capture_plan.csv
KeyError: observations is not a file in the archive
```

### Context
- Command attempted: ad hoc M3027 audit script.
- Actual files use `*_rows.csv` names.
- Actual trace tensor keys are `observation_trace`, `action_trace`, `next_observation_trace`, `reward_trace`, `done_trace`, and `timeout_trace`.
- `gate_matrix.csv` uses `status_pass`, not `pass`.

### Suggested Fix
For AutoDrift research audits, read one live CSV row and one live NPZ key list before writing count or tensor checks.

### Metadata
- Reproducible: yes
- Related Files: runs/m3027_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_deployable_trace_capture_preflight

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

## [ERR-20260607-007] autodrift_local_search_guard_synthesis_decision

**Logged**: 2026-06-07T15:41:29+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
AutoDrift manifest validation requires a real `workflow_synthesis.synthesis_decision` when local-search repeat counts reach the guard threshold.

### Error
```text
error: m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis: local_search_guard requires a workflow synthesis decision when local_search_risk is high or repeat/repair counts reach 3
```

### Context
- Command attempted: `make research-validate`
- M3020 had `local_search_guard.same_failure_repeat_count: 3` but `workflow_synthesis.synthesis_decision: not_applicable`.
- The milestone is itself a synthesis continuation, so the manifest must pre-register a concrete synthesis decision.

### Suggested Fix
When same-failure repeat count reaches 3 or local-search risk is high, set `workflow_synthesis.synthesis_decision` to `continue`, `pivot`, `stop`, or `promote_to_next_branch` instead of `not_applicable`.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.json

---

## [ERR-20260607-008] autodrift_workflow_synthesis_artifact_layout

**Logged**: 2026-06-07T15:42:10+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
AutoDrift synthesis manifests require `synthesis_artifact` and `synthesis_questions` inside `workflow_synthesis` when the synthesis decision is concrete.

### Error
```text
error: m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis: workflow_synthesis.synthesis_artifact must be non-empty text for synthesis milestones
error: m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis: workflow_synthesis.synthesis_questions must be a non-empty list of non-empty text
```

### Context
- Command attempted: `make research-validate`
- M3020 had top-level `synthesis_artifact` and `synthesis_questions` but `workflow_synthesis.synthesis_decision: continue`.
- The validator reads synthesis metadata from the nested `workflow_synthesis` object for concrete synthesis milestones.

### Suggested Fix
For concrete synthesis milestones, put `synthesis_artifact` and a list-form `synthesis_questions` inside `workflow_synthesis`; avoid relying on top-level synthesis fields.

### Metadata
- Reproducible: yes
- Related Files: experiments/manifests/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.json

---
## [ERR-20260607-001] research_review_scoreboard_csv

**Logged**: 2026-06-07T20:56:00Z
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
Manual scoreboard row contained an unescaped comma, causing `make research-review` to fail while parsing `experiments/scoreboard.csv`.

### Error
```text
ValueError: scoreboard row 3027 has extra fields
```

### Context
- Command: `make research-review RESEARCH_MANIFEST=experiments/manifests/m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis.json`
- The row was appended by hand instead of through `csv.DictWriter`.

### Suggested Fix
When adding scoreboard rows manually, avoid commas in free-text fields or use a CSV writer/upsert helper.

### Metadata
- Reproducible: yes
- Related Files: experiments/scoreboard.csv

---
