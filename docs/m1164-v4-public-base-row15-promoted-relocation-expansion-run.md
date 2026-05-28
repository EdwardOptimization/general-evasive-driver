# M1164 V4 Public Base Row15 Promoted Relocation Expansion Run

## Purpose

M1164 attempted the bounded relocation-expansion diagnostic designed in M1163.
It reused the existing M1161 outcome CSV and did not rerun matched-current
mining or the matched-history outcome gate.

## Command

M1164 launched:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
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

## Result

The command was interrupted after roughly `33` minutes because it had not
written a summary and the run directory still contained no artifacts:

```text
run_dir: runs/m1164_row15_promoted_relocation_expansion_seed116100
summary.json: missing
run_dir files: none
process CPU: about 100%
process RSS: about 1.48 GB
```

No actor training, PPO, promotion, private holdout, actor-input change, new
mining, outcome rerun, threshold weakening, or surface conversion occurred.

## Interpretation

M1164 does not provide a scientific surface result. It provides a process
result: the M1163 expansion is too large for the current interactive research
loop.

The likely cost driver is the cross product of:

```text
1600 candidates
11 target-normal-margin values
3 body-longitudinal offsets
3 body-lateral offsets
5 report variants
up to 60 continuation steps
```

This should be redesigned as a staged resource-bounded diagnostic rather than
rerun as a single large relocation expansion.

## Decision

Do not treat M1164 as a pass or fail for wrong-history surface availability.
Route to a resource-scope redesign that runs a smaller pilot first.

```text
decision: row15_promoted_relocation_expansion_resource_failure_route_to_staged_design
next: m1165-v4-public-base-row15-promoted-staged-relocation-expansion-design
```
