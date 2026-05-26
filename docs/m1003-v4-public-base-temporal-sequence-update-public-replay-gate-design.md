# M1003 V4 Public Base Temporal Sequence Update Public Replay Gate Design

## Purpose

M1003 designs the no-training public replay/proof gate for M1002 exact temporal
objective candidates.

This milestone does not run replay, train, run PPO, use private holdout, or
promote a checkpoint.

## Candidate Set

M1002 exact gate produced five candidates:

```text
alpha 0.010
alpha 0.020
alpha 0.050
alpha 0.100
alpha 0.200
```

Primary exact candidate:

```text
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
```

Base checkpoint:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Candidate ranking:

```text
1. alpha 0.200
2. alpha 0.100
3. alpha 0.050
4. alpha 0.020
5. alpha 0.010
```

Rationale:

```text
alpha 0.200 has the best exact weighted total loss while satisfying normal
retention, temporal gap, and action-drift trust-region gates.
```

## Gate Structure

M1004 should implement a no-training gate with three tiers.

### Tier 1: Contract And Exact Retention

For each candidate alpha:

```text
actor input config equals M974 base
only actor_mean differs from M974
M1000 exact objective evaluator runs on M997 corpus
weighted_total_loss <= M1000 base - 0.001
weighted_normal_sequence_nll <= M1000 base + 0.005
weighted_temporal_preference_loss <= M1000 base + 0.005
weighted_logp_gap_mean >= M1000 base - 0.050
temporal_logp_gap_p10 >= M1000 base - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
```

This tier should mostly reproduce M1002, but it prevents stale or manually
modified checkpoints from entering replay.

### Tier 2: M267/M264 Preflight

Run full M267/M264 replay first for candidates in exact rank order:

```text
surface:
  runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv

required:
  success_drop_count remains 17 / 17
  max_success_drop_count_regression == 0
  max_normal_success_drop == 0.0
  max_normal_margin_regression <= 0.005
  max_margin_gap_regression <= 0.001
```

If no candidate passes M267/M264, classify:

```text
proof_washout
```

and route to temporal-objective replay-failure audit. Do not run full replay
for candidates that already fail M267/M264.

### Tier 3: Full Public Replay Gate

For the first M267/M264-passing candidate, run the six public replay surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Required pass criteria:

```text
all six public replay gates pass
failed_public_replay_surfaces == []
```

Use the same replay tolerances as recent public-base gates:

```text
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
max_continuation_steps: 60
```

## Behavior And Ablation Gate

M1004 should evaluate behavior seeds:

```text
9505
9506
```

For each seed compare:

```text
M974 base
candidate normal
candidate reset_recurrent_state
candidate zero_all_response
```

Required:

```text
candidate_success_rate >= base_success_rate
candidate_termination_rate <= base_termination_rate
candidate_success_rate >= reset_success_rate >= zero_all_success_rate
```

Behavior failure should be classified separately from proof washout:

```text
behavior_regression
```

## Temporal Corpus Retention

M1004 should rerun M1000 evaluator for the selected candidate and report:

```text
weighted_normal_sequence_nll
weighted_temporal_preference_loss
weighted_logp_gap_mean
temporal_logp_gap_p10
candidate_action_l2_mean
candidate_action_l2_max
```

The candidate must keep exact temporal gates from M1002. If it fails here, the
artifact is stale or incompatible and replay should stop.

## Diagnostics

M1004 should also run, or at minimum report if unavailable:

```text
source-diverse protected diagnostics used by recent gates
old 9944 key neighborhood diagnostic-only replay
actor-input contract check
candidate checkpoint sha256
```

Old key diagnostics should remain diagnostic-only. A single stale old key should
not override the full public replay decision unless the current source-diverse
surfaces also fail.

## Routing

If all gates pass:

```text
route_to_public_gate_promotion_audit_design
```

This does not promote. It only admits a promotion/generalization audit.

If exact gates pass but replay fails:

```text
route_to_temporal_objective_replay_failure_audit
failure_type: proof_washout
```

If behavior fails:

```text
route_to_behavior_regression_audit
failure_type: behavior_regression
```

If contract fails:

```text
route_to_contract_violation_audit
failure_type: contract_violation
```

## Blocked Routes

Do not:

```text
run PPO;
promote;
use private holdout;
skip M267/M264 preflight;
skip old public replay surfaces;
claim cross-fault wrong-history self-ID;
choose a lower alpha after seeing full replay unless the decision rule is
pre-registered in M1004.
```

## Decision

```text
temporal_sequence_public_replay_gate_design_admit_m1004
```

Next:

```text
m1004-v4-public-base-temporal-sequence-update-public-replay-gate
```
