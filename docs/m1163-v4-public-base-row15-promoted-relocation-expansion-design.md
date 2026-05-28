# M1163 V4 Public Base Row15 Promoted Relocation Expansion Design

## Purpose

M1163 designs a bounded relocation-expansion diagnostic after M1161 produced a
sparse, duplicate-dominated wrong-history surface.

This milestone is design-only. It does not run relocation, mine rows, run
replay, train actor weights, run PPO, promote, use private holdout, or change
actor inputs.

## Audit Input

Use the existing M1161 outcome CSV:

```text
runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
```

Do not rerun matched-current mining or the matched-history outcome gate in the
next milestone. The M1162 audit already showed that source budget was strong:

```text
matched_current_accepted_pair_count: 4585
selected_physical_pairs before relocation: 242
```

## Diagnostic Question

M1161 failed after relocation:

```text
accepted_wrong_history_rows: 15
accepted_wrong_physical_pairs: 2
accepted_wrong_targets: 1
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_normal_margin_max: 0.002483
```

M1164 should answer:

```text
Was the M1161 accepted surface sparse because the relocation search was too
narrow, or because fresh wrong-matched-history sensitivity is genuinely scarce?
```

## Expansion Scope

M1164 should expand relocation only:

```text
max_candidates: 1600
max_candidates_per_physical_pair: 12
max_candidates_per_checkpoint_target: 256
body_longitudinal_offsets: -1.0, 0.0, 1.0
body_lateral_offsets: -0.3, 0.0, 0.3
half_width_inflations: 0
```

This is deliberately bounded. It is wide enough to test whether small
body-frame obstacle shifts unlock more wrong-history success drops, but not so
wide that it becomes a full new mining campaign.

## M1164 Command

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
  --outcome-csv runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 1600 \
  --max-candidates-per-physical-pair 12 \
  --max-candidates-per-checkpoint-target 256 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.25 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.0005,0.001,0.0025,0.005,0.01,0.02,0.04,0.08,0.12,0.16,0.20 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=-1.0,0.0,1.0 \
  --body-lateral-offsets=-0.3,0.0,0.3 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1164_row15_promoted_relocation_expansion_seed116100
```

## Acceptance Criteria

Keep the M1160 gate unchanged:

```text
accepted_wrong_history_rows >= 100
accepted_wrong_physical_pairs >= 12
accepted_wrong_left_steps >= 6
accepted_wrong_checkpoints >= 4
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 3 at width 0.005
accepted_wrong_normal_margin_max >= 0.01
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
control_accepted_wrong_rows == 0
source_budget_ready == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

## Result Interpretation

If M1164 passes, route to compact conversion design.

If M1164 improves accepted rows and diversity but still fails slack, route to a
staged relocation-expansion audit. Do not convert.

If M1164 remains near M1161 levels, classify the branch as wrong-history
intervention scarcity and route to mechanism audit rather than another mining
retry.

## Decision

```text
decision: row15_promoted_relocation_expansion_design_admit_run
next: m1164-v4-public-base-row15-promoted-relocation-expansion-run
```
