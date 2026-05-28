# M1176 V4 Public Base Action-Divergent Bounded Relocation Design

## Purpose

M1176 designs a bounded relocation replay over the M1175 action-divergent
candidate export.

M1175 proved that existing M1161 outcome artifacts contain a source-diverse
action-divergent candidate pool:

```text
selected_rows: 240
selected_physical_pairs: 17
selected_left_steps: 9
selected_targets: 3
selected_checkpoints: 6
max_selected_pair_fraction: 0.0625
```

But M1175 is not proof evidence:

```text
success_drop_rows: 0
```

Therefore the next valid step is a bounded relocation replay that asks whether
these action-divergent rows can become source-diverse wrong-history boundary
rows under relocated obstacle timing.

## Design

Use the existing source-balanced relocation runner, but pass the exported
candidate CSV as the `--outcome-csv` input:

```text
runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv
```

This keeps the run bounded to the exported action-divergent candidate set. It
does not rerun broad mining.

The first relocation design uses:

- all six checkpoint labels represented in M1175;
- fine target-normal margins restored by M1169;
- zero body-frame obstacle offsets;
- `wrong_matched_history` only;
- source-diversity gates at least as strict as M1175 selection.

This is intentionally conservative. M1166 showed that broad body-offset
expansion can waste runtime and does not automatically create new
wrong-history surfaces. M1169 showed that fine target margins matter.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 240 \
  --max-candidates-per-physical-pair 15 \
  --max-candidates-per-checkpoint-target 80 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 3 \
  --max-rows-per-pair-fraction 0.15 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.15 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.00025,0.0005,0.00075,0.001,0.00125,0.0015,0.002,0.0025,0.003,0.004,0.005 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=0.0 \
  --body-lateral-offsets=0.0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1177_action_divergent_bounded_relocation_seed117700
```

## Acceptance

M1177 should be judged by the relocation runner summary and robustness gates.
The high-level pass condition is:

```text
decision == source_balanced_boundary_export_pass
passed == true
```

The expected proof-surface criteria are:

```text
accepted_wrong_rows >= 80
accepted_wrong_physical_pairs >= 10
accepted_wrong_left_steps >= 5
accepted_wrong_checkpoints >= 3
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 2
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.15
control_accepted_wrong_rows == 0
```

The run is allowed to fail. A failure should be classified, not repaired by
weakening thresholds inside the same milestone.

## Failure Routing

If M1177 fails because accepted wrong-history rows are still scarce, route to a
mechanism audit:

```text
action_divergent_relocation_scarcity_audit
```

If M1177 finds enough rows but pair/target/checkpoint diversity fails, route to
source-balanced candidate scoring repair.

If M1177 passes, route to a bounded proof-corpus conversion design. Passing
M1177 still would not promote a checkpoint or prove driver performance.

## Caveat

The source obstacle geometry bucket remains weak because M1161/M1175 artifacts
do not include explicit obstacle body geometry columns. M1177 source diversity
therefore remains scoped to physical pairs, checkpoints, targets, and left
steps unless future mining records richer source geometry.

## Guardrail

M1176 itself does not run relocation replay, mining, actor training, PPO,
promotion, private holdout, row conversion, threshold weakening, or actor-input
changes.

## Decision

```text
decision: action_divergent_bounded_relocation_design_admit_run
next: m1177-v4-public-base-action-divergent-bounded-relocation-run
```
