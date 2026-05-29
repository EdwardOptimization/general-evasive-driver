# M1497 Paper-Route Go/No-Go Profile Three-Seed Public Pilot

## Summary

M1497 runs the full 12-profile go/no-go matrix as one fixed-budget, three-seed
public pilot.

Decision:

```text
go_no_go_three_seed_public_pilot_completed_route_to_stop_rule_audit
```

This milestone does not promote, use private holdout, export corpus, change
actor inputs, claim profile superiority, claim paper-level evidence, or claim
level3 self-identification.

## Completion Audit

The pilot completed cleanly:

```text
result_class: corrected_profile_pilot_completed
run_dir: runs/m1497_go_no_go_profile_three_seed_public_pilot
profile_count: 12
main_profile_count: 7
diagnostic_profile_count: 5
total_seed_runs: 36
completed_seed_runs: 36
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
runtime_seconds: 260.3160450430587
```

The shared public evaluation block was:

```text
training_seed_base: 149700
training_seed_offsets: [0, 1, 2]
eval_seed_base: 149800
eval_episodes: 64
device: cpu
```

So M1497 satisfies its runtime and artifact criteria.

## Aggregate Results

Three-seed aggregate trends:

```text
L0_current_masked:
  success/collision/margin: 0.177083 / 0.718750 / 0.260532

L1_one_step:
  success/collision/margin: 0.296875 / 0.593750 / 0.412606

L2_window_13:
  success/collision/margin: 0.166667 / 0.739583 / 0.147432
L2_window_13_current_tiled:
  success/collision/margin: 0.151042 / 0.750000 / 0.203557

L2_window_25:
  success/collision/margin: 0.182292 / 0.713542 / 0.235919
L2_window_25_current_tiled:
  success/collision/margin: 0.130208 / 0.770833 / 0.196534

L2_window_50:
  success/collision/margin: 0.182292 / 0.713542 / 0.235935
L2_window_50_current_tiled:
  success/collision/margin: 0.130208 / 0.770833 / 0.196539

L2_window_100:
  success/collision/margin: 0.182292 / 0.713542 / 0.235935
L2_window_100_current_tiled:
  success/collision/margin: 0.130208 / 0.770833 / 0.196539

L3_online_gru:
  success/collision/margin: 0.286458 / 0.640625 / 0.480487
L3_reset_control_corrected:
  success/collision/margin: 0.317708 / 0.604167 / 0.502408
```

## Stop-Rule Audit Input

M1496 admitted M1497 with this stop rule:

```text
If M1497 repeats both patterns:
1. L2 current-tiled controls remain close to L2 normal;
2. L3 online does not beat corrected reset-control;
then M1498 must stop standard profile-scaling and route to decisive T4/T5 task
evidence, L3 training-recipe repair, or a negative/conditional standard-profile
verdict.
```

M1497 supplies the evidence needed for M1498:

```text
L2 13 normal - current_tiled success delta:  0.015625
L2 25 normal - current_tiled success delta:  0.052083
L2 50 normal - current_tiled success delta:  0.052083
L2 100 normal - current_tiled success delta: 0.052083

L3 online - reset success delta: -0.031250
L3 online - reset collision delta: 0.036458
L3 online - reset mean-margin delta: -0.021921
```

This is not paper-grade architecture ranking by itself. It is enough to trigger
the pre-registered M1498 audit because the standard fixed-budget profile pilot
again does not support a clear older-history or online-GRU advantage.

## Classification

M1497 classifies as:

```text
runtime_completion: pass
public_trend_matrix: produced
private_holdout_used: false
promotion_allowed: false
profile_superiority_claim_allowed: false
self_id_claim_allowed: false
finite_window_history_necessity: not_supported_by_three_seed_public_pilot
online_gru_hidden_advantage: not_supported_by_three_seed_public_pilot
current_frame_substitution_risk: high
standard_profile_scaling_stop_rule: triggered_for_audit
```

The right conclusion is conservative:

```text
The standard public profile matrix is useful as a baseline, but further scaling
of the same profile pilot is not currently the highest-leverage path for
proving level3 recurrent self-identification.
```

## Next Route

Route to:

```text
m1498-paper-route-go-no-go-three-seed-result-audit
```

M1498 must decide whether to:

```text
1. pivot to decisive T4/T5 same-current/history-necessary task evidence;
2. repair L3 training recipe before another profile comparison;
3. record a negative/conditional verdict for standard-distribution
   self-identification evidence.
```

No M1497 checkpoint is promoted.

## Guardrails

```text
replay_started: false
candidate_replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
profile_specific_tuning: false
actor_input_contract_changed: false
training_corpus_exported: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
```
