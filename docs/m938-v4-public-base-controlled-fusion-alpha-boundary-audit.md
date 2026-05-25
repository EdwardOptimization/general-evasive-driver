# M938 V4 Public Base Controlled Fusion Alpha Boundary Audit

## Purpose

M937 showed a controlled fusion-plus-head trust-region conflict on a coarse alpha
grid. M938 runs a no-training fine alpha sweep over the saved M937 raw
controlled-fusion direction to determine whether there is a narrow admissible
overlap between normal retention and tail lift.

No training, exact compatibility, replay, PPO, or promotion is run.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_raw_direction_feasibility \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m937_v4_public_base_controlled_fusion_surface/checkpoints/raw_controlled_fusion_update.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --target-rows runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv \
  --m912-summary runs/m912_v4_public_base_sequence_recalibration_audit/summary.json \
  --low-tail-rows runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv \
  --run-dir runs/m938_v4_public_base_controlled_fusion_alpha_boundary \
  --device cpu \
  --alphas 0.050,0.075,0.100,0.125,0.150,0.175,0.200,0.225,0.250,0.275,0.300,0.325,0.350,0.500,0.750,1.000
```

## Artifacts

- Summary: `runs/m938_v4_public_base_controlled_fusion_alpha_boundary/summary.json`
- Alpha metrics: `runs/m938_v4_public_base_controlled_fusion_alpha_boundary/alpha_metrics.csv`
- Objective rows: `runs/m938_v4_public_base_controlled_fusion_alpha_boundary/objective_rows.csv`

## Result

M938 is a clean no-training alpha-boundary audit:

```text
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
joined_target_rows: 122
missing_target_keys: 0
actor_mean_changed_between_checkpoints: true
fusion_changed_between_checkpoints: true
forbidden_parameter_changed_between_checkpoints: false
training_started: false
candidate_alpha_count: 0
strict_candidate_count: 0
low_tail_effect_candidate_count: 0
target_tolerance_candidate_count: 0
normal_safe_low_tail_trend_count: 5
result_class: public_base_controlled_fusion_raw_direction_feasibility_trust_region_conflict
```

The saved M937 raw checkpoint differs from M399 only on the allowed controlled
surface.

## Boundary Findings

Best normal-retaining row:

```text
alpha: 0.15
normal_retention_pass: true
tail_lift_pass: false
first_action_drift_from_base_mean: 0.0023812945
first_action_drift_from_base_p95:  0.0062792329
normal_anchor_mse_mean:            0.0000031994
normal_anchor_mse_p95:             0.0000131429
normal_intervention_gap_p10:       0.0093974071
gap_deficit_mean:                  0.0150613526
low_tail_fraction:                 0.3858202696
target_action_mse_mean:            0.0005423113
```

Tail-lift starts after normal retention has already failed:

```text
alpha: 0.25
normal_retention_pass: false
tail_lift_pass: true
first_action_drift_from_base_mean: 0.0037174641
first_action_drift_from_base_p95:  0.0098562753
gap_deficit_mean:                  0.0138036459
low_tail_fraction:                 0.3569661975
```

The key observation is that alpha `0.15` is a near-miss:

```text
p10 gap:        passes the p10 direction implied by the registered gate
low-tail frac:  improves substantially and is below the registered fraction band
deficit mean:   still slightly above the registered deficit target
normal:         still retained
```

So this is not a complete no-overlap failure. It is a boundary-shaping problem:
the current raw direction creates the right low-tail movement, but the admissible
normal-retained part undershoots the deficit component.

## Interpretation

M937/M938 show that controlled fusion has materially more leverage than
actor_mean-only:

```text
M934 alpha 1.0 low_tail_fraction: 0.34130
M937/M938 alpha 1.0 low_tail_fraction: 0.04534
```

But the current raw direction is not admissible:

```text
normal-retained alphas stop around 0.15;
tail_lift_pass begins around 0.25;
there is no exact overlap on the fine grid.
```

Because alpha `0.15` is close on p10 and fraction but misses deficit, the next
step should not widen the trainable surface yet. It should design a
boundary-aware controlled-fusion objective that trains directly at the
normal-retained boundary alphas.

## Decision

Do not run exact compatibility, replay, PPO, or promotion from M938.

Next blocker:

```text
m939-v4-public-base-controlled-fusion-boundary-objective-design
```

M939 should design an interpolation-aware controlled-fusion objective focused on
alpha `0.125` to `0.175`, with stronger deficit shaping and explicit normal
retention penalties, before any wider trainable surface is considered.
