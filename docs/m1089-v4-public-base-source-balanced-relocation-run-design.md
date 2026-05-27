# M1089 V4 Public Base Source-Balanced Relocation Run Design

## Purpose

M1089 designs the next step after M1088 separated the source-diversity failure
into two parts:

```text
pre-boundary candidate budget: ready
old boundary relocation export: still six-pair limited
```

This milestone is design-only. It does not train, run PPO, promote a
checkpoint, use private holdout, rerun mining, or weaken robustness thresholds.

## Starting Evidence

M1088 showed that the existing M1083 outcome CSV is not source-budget limited:

```text
candidate_wrong_history_rows: 7257
eligible_physical_pairs: 371
eligible_left_steps: 28
eligible_checkpoints: 4
eligible_targets: 3
source_budget_ready: true
```

The M1086 selector can choose a source-balanced candidate set:

```text
selected_rows: 512
selected_physical_pairs: 370
selected_left_steps: 28
selected_targets: 3
max_selected_pair_fraction: 0.005859375
decision: source_balanced_candidates_ready
```

But the already-generated M1083 boundary relocation artifact remains
export-limited:

```text
balanced_exportable_rows: 102
accepted_wrong_physical_pairs: 6 / 10 required
accepted_wrong_success_drop_fraction: 1.0
decision: reject_duplicate_dominated_boundary_surface
```

Therefore post-filtering the old accepted rows cannot create the missing four
physical pairs. The source-balanced candidates have to enter the relocation
evaluation itself.

## Code Audit

Existing code has two separate paths:

```text
wrong_history_boundary_relocation_surface:
  selects wrong-history candidates and runs relocation replay.

source_balanced_boundary_relocation_surface:
  computes source budget, selects balanced candidates, and marks balanced
  export rows from already-existing boundary relocation CSVs.
```

The current `source_balanced_boundary_relocation_surface` CLI is an
existing-artifact smoke only. It does not call:

```text
collect_requested_outcome_snapshots
build_boundary_relocation_rows
replay_outcome_variant
```

The current `wrong_history_boundary_relocation_surface` runner does call those
relocation functions, but its candidate selection is not source-balanced. It
cannot directly enforce M1086's physical-pair round-robin selection before
relocation replay.

So M1090 needs an implementation milestone. A run-only milestone with existing
code would either rerun the old source-unaware relocation path or only repeat
M1088's artifact smoke.

## Required M1090 Runner

M1090 should extend `src/autodrift/source_balanced_boundary_relocation_surface.py`
with a full relocation runner. The runner should:

1. Read the outcome CSV.
2. Build and write `source_budget_summary.json`.
3. Use `select_source_balanced_candidates` before relocation.
4. Fail closed before replay if the source budget or selected candidates cannot
   satisfy the configured minimum diversity.
5. For each checkpoint label, collect requested snapshots only for the selected
   candidates assigned to that checkpoint.
6. Call `build_boundary_relocation_rows` with the selected candidates.
7. Mark balanced export rows using `mark_balanced_export_rows`.
8. Write raw and balanced artifacts.
9. Classify the final decision using the existing robustness thresholds.

Required output schema:

```text
summary.json
source_budget_summary.json
source_budget_rows.csv
balanced_candidate_rows.csv
candidate_balance_rejection_rows.csv
boundary_relocation_rows.csv
balanced_accepted_wrong_history_rows.csv
balance_rejection_rows.csv
robustness_gates.csv
surface_summary.csv
```

The raw `boundary_relocation_rows.csv` remains the replay audit trail. Only
`balanced_accepted_wrong_history_rows.csv` is eligible for later compact corpus
conversion.

## Thresholds To Preserve

M1090 and the later run must keep the current robustness thresholds unchanged:

```text
accepted_wrong_rows >= 80
accepted_wrong_physical_pairs >= 10
accepted_wrong_left_steps >= 5
accepted_wrong_checkpoints >= 3
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 2
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
control_accepted_wrong_rows == 0
```

Candidate-selection quotas may be adjusted only to increase coverage before
replay. They cannot redefine the robustness gate.

## Proposed CLI Shape

M1090 should add a full-run mode while keeping the existing artifact-smoke mode.

Proposed command shape:

```bash
PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy proof_current=<checkpoint.pt> \
  --checkpoint-policy short61049=<checkpoint.pt> \
  --checkpoint-policy short61050=<checkpoint.pt> \
  --checkpoint-policy short61051=<checkpoint.pt> \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1083_proof_hardened_retarget_outcome_seed108200/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 512 \
  --max-candidates-per-physical-pair 8 \
  --max-candidates-per-checkpoint-target 64 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 10 \
  --target-min-left-steps 5 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 10 \
  --max-candidate-pair-fraction 0.25 \
  --min-base-action-distance 0.0 \
  --min-base-margin-gap 0.005 \
  --target-normal-margins 0.0005,0.001,0.0025,0.005,0.01,0.02,0.04 \
  --body-longitudinal-offsets=-2.0,-1.0,0.0,1.0,2.0 \
  --body-lateral-offsets=-0.4,0.0,0.4 \
  --half-width-inflations 0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.04 \
  --min-margin-gap 0.04 \
  --margin-bucket-width 0.005 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1091_source_balanced_boundary_relocation_seed109100
```

The argparse form for negative offset lists must use `--option=value`, matching
the M1083 command-fix lesson.

## Tests Required In M1090

M1090 should add focused tests for:

```text
1. selected candidates are passed into relocation without falling back to global top-K;
2. missing/insufficient source budget fails closed before replay;
3. full-run artifact writer includes source-budget, selected-candidate, raw boundary, balanced export, and robustness gate outputs;
4. existing artifact-smoke CLI behavior remains intact;
5. source-balanced full-run mode does not train, run PPO, promote, or use private holdout.
```

Synthetic tests should mock or use tiny data where possible. M1090 does not need
to run the expensive M1091 relocation experiment.

## Decision

```text
source_balanced_relocation_design_route_to_runner_implementation
```

Next:

```text
m1090-v4-public-base-source-balanced-relocation-runner-implementation
```

M1090 should be implementation/infrastructure only. M1091 should be the first
actual source-balanced relocation replay run.
