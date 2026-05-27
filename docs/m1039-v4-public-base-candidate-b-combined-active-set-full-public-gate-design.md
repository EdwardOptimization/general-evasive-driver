# M1039 V4 Public Base Candidate B Combined Active-Set Full Public Gate Design

## Purpose

M1039 designs the full public proof/generalization/behavior gate for the M1038
first-replay candidate.

M1039 is design only. It does not run full gates, train, run PPO, use private
holdout, change actor inputs, or promote.

## Candidate And Baseline

Baseline is the current public-gate base, Candidate B:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Candidate is the M1038 selected first-replay checkpoint:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

M1038 evidence:

```text
result_class: candidate_b_combined_active_set_projection_first_replay_candidate
source: base_row16x4_s40
alpha: 0.15
M997 exact: pass
M297/M270 exact: pass
M267/M264 first replay: pass, row15 retained
M183/M170 first replay: pass, row16 retained
ppo_used: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

This is enough to justify a full public gate. It is not promotion evidence by
itself.

## Important Contract Difference From M1019

M1019's older exact contract only allowed `actor_mean.*` to change. That is not
the right contract for M1038.

M1038 changed exactly:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

M1040 should therefore use this allowed trainable surface:

```text
allowed changed parameter prefixes:
  actor_mean.
  response_context_fusion.0.
```

Still forbidden:

```text
actor input config changes
response encoder changes
context encoder changes
GRU/recurrent changes
critic changes
log_std changes
environment changes
```

If the old M1019 contract is reused without this update, M1040 will produce a
false `contract_artifact`.

## Gate Tiers For M1040

### Tier 0: Contract And Exact Retention

M1040 must recompute, not reuse cached M1038 rows:

```text
actor input signature equals Candidate B
changed parameter names are a subset of the allowed surface
M997 temporal exact retention passes
M297/M270 exact no-regression passes
combined active-set anchor family losses are reported
```

M997 thresholds:

```text
weighted_total_loss <= M1000 base - 0.001
weighted_normal_sequence_nll <= M1000 base + 0.005
weighted_temporal_preference_loss <= M1000 base + 0.005
weighted_logp_gap_mean >= M1000 base - 0.050
temporal_logp_gap_p10 >= M1000 base - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
```

M297/M270 thresholds:

```text
exact_m297_delta_vs_candidate_b <= 1e-7
exact_m270_delta_vs_candidate_b <= 1e-7
```

### Tier 1: Six Public Replay Surfaces

Run selected candidate against Candidate B on:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Use the same replay tolerances:

```text
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
max_continuation_steps: 60
env_config: configs/m121_human_view_zero_obstacle_relvel.json
```

Hard row checks:

```text
M267/M264 row15:
  normal_success true
  wrong_history_success false
  success_drop true

M183/M170 row16:
  normal_success true
  wrong_history_success false
  success_drop true
```

### Tier 2: Source-Diverse Public Diagnostics

Run the public source-diverse diagnostic bundle used in recent public-base gates:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

These are public diagnostics, not private holdout.

### Tier 3: Fresh Public And Moderate-OOD Evaluation

Run fresh public randomized evaluations not used to select M1038:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
episodes: 256
seeds: 103900, 103901
policies: Candidate B, M1038 selected candidate
```

Run moderate-OOD:

```text
config: configs/eval_m574_moderate_ood_l3.json
episodes: 128
seeds: 103920
policies: Candidate B, M1038 selected candidate
```

Pass rule:

```text
candidate success_rate >= base success_rate - 0.01
candidate termination_rate <= base termination_rate + 0.01
candidate min_clearance_margin_mean >= base margin_mean - 0.005
candidate collision_rate <= base collision_rate + 0.01
```

### Tier 4: Behavior And Ablation Retention

Run behavior seeds:

```text
9505
9506
103930
103931
```

Episodes per seed:

```text
80
```

Policies:

```text
Candidate B
M1038 selected candidate
M1038 selected candidate @ reset_recurrent_state
M1038 selected candidate @ zero_all_response
```

Pass rule:

```text
candidate normal success >= base success - 0.01
candidate normal termination <= base termination + 0.01
candidate normal success >= candidate reset success >= candidate zero_all success
```

This is not a paper-level self-ID proof. It is a retention guard against losing
response-history dependence.

## Result Classes For M1040

M1040 should classify:

```text
candidate_b_combined_active_set_full_public_gate_candidate
candidate_b_combined_active_set_full_public_gate_exact_failed
candidate_b_combined_active_set_full_public_gate_contract_artifact
candidate_b_combined_active_set_full_public_gate_public_replay_washout
candidate_b_combined_active_set_full_public_gate_source_diagnostic_failed
candidate_b_combined_active_set_full_public_gate_generalization_regression
candidate_b_combined_active_set_full_public_gate_behavior_regression
```

Only `candidate_b_combined_active_set_full_public_gate_candidate` should route
to a separate promotion audit. M1040 itself must not promote.

## Required M1040 Artifacts

```text
runs/m1040_candidate_b_combined_active_set_full_public_gate/summary.json
runs/m1040_candidate_b_combined_active_set_full_public_gate/exact_contract_summary.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/proof_replay_summary.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/source_diverse_summary.json
runs/m1040_candidate_b_combined_active_set_full_public_gate/fresh_randomized_eval_summary.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/ood_eval_summary.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/generalization_comparison.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/behavior_summary.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/behavior_comparison.csv
runs/m1040_candidate_b_combined_active_set_full_public_gate/route_decision.csv
```

## Forbidden Shortcuts

M1039 and M1040 must not:

- run PPO;
- promote directly;
- use private holdout;
- change actor inputs;
- drop old public replay surfaces;
- skip M297/M270 because M997 passes;
- skip fresh public or moderate-OOD evaluation;
- claim paper-level evidence from a public gate.

## Decision

```text
candidate_b_combined_active_set_full_public_gate_design_admit_m1040_gate
```

Next:

```text
m1040-v4-public-base-candidate-b-combined-active-set-full-public-gate
```
