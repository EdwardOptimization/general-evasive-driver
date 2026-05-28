# M1348 Paper-Route Materialized Source-History Pair-Group Limited Replay Preflight Design

## Summary

M1348 designs the limited public replay preflight for the M1346 candidate after
M1347 audited it as objective-positive but non-promotable.

Decision:

```text
materialized_source_history_limited_replay_preflight_design_admit_two_surface_preflight
```

This is design-only. It does not run replay, train, run PPO, use private
holdout, change actor inputs, or promote a checkpoint.

## Candidate And Base

Base:

```text
label: m1154_base
checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Candidate:

```text
label: m1346_pair_group
checkpoint:
  runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
```

Known M1346 objective evidence:

```text
combined_loss_mean: 6.8847534022 -> 1.9998926339
group_min_joint_margin_mean: -6.8026667906 -> -1.1251848645
eval fold 4 group_min_joint_margin_mean: -6.4443958161 -> -1.2625397266
one_sided_conflict: 684 -> 605
all_rows_both_directional: 0 -> 27
both_negative: 4 -> 26
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
```

This objective evidence is not replay proof.

## Tooling Decision

Do not use `autodrift.capability_step_temporal_sequence_public_replay_gate`
directly for M1349.

Reason:

```text
that wrapper assumes M997 temporal exact retention and actor_mean-only
candidate mutations; M1346 changes response_context_fusion + actor_mean and is
admitted by M1336/M1339/M1342 materialized source-history metrics instead.
```

Use the lower-level replay gate directly:

```text
autodrift.boundary_outcome_replay_gate
```

This gate only needs:

```text
base checkpoint;
candidate checkpoint;
public boundary-outcome corpus;
env config;
baseline and candidate labels;
standard replay tolerances.
```

## M1349 Gate Order

M1349 should be a two-surface preflight, not full public replay.

### Tier 0: Contract And Mutation Guard

Check:

```text
base/candidate actor input config equal;
candidate actor_encoder remains canonical 72-value human-view online recurrent;
candidate changed parameters are only:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
log_std unchanged;
no actor-input expansion;
no private holdout;
no PPO;
no promotion.
```

Tier 0 should reuse M1346 `parameter_delta.json` and verify the candidate
checkpoint remains loadable.

### Tier 1: First Replay Surface

Run M267/M264 first because it is the current-family wrong-history proof surface
most directly related to the M1346 source-history objective.

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m1154_base=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m1346_pair_group=runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt \
  --corpus-csv runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --baseline-policy m1154_base \
  --candidate-policy m1346_pair_group \
  --max-continuation-steps 60 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1349_materialized_source_history_limited_replay_preflight/m267_m264
```

Pass requires:

```text
gate_pass: true
normal_success_delta >= 0
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
success_drop_count_delta >= 0
```

If M267/M264 fails, stop M1349 and route to objective tradeoff repair or replay
failure audit. Do not run broad replay after a first-surface proof washout.

### Tier 2: Boundary-Cliff Replay Surface

Only if M267/M264 passes, run M183/M170. This is the historical row16
normal-branch cliff surface.

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m1154_base=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m1346_pair_group=runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt \
  --corpus-csv runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --baseline-policy m1154_base \
  --candidate-policy m1346_pair_group \
  --max-continuation-steps 60 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1349_materialized_source_history_limited_replay_preflight/m183_m170
```

Pass uses the same replay tolerances.

If M183/M170 fails after M267/M264 passes, classify the result as a
boundary-cliff proof washout and route to replay-aware active-set repair. Do not
run PPO.

## M1349 Summary Artifact

M1349 should write a manual or wrapper-generated summary:

```text
runs/m1349_materialized_source_history_limited_replay_preflight/summary.json
```

Required fields:

```text
run_type: materialized_source_history_limited_replay_preflight
base_checkpoint
candidate_checkpoint
contract_pass
allowed_parameter_scope_pass
m267_m264_gate_pass
m183_m170_gate_pass
preflight_pass
failure_types
next_blocker
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Blocked Routes

Do not:

```text
run PPO;
promote M1346;
use private holdout;
run full public replay before the two-surface preflight;
skip M267/M264;
skip M183/M170 if M267/M264 passes;
change actor inputs;
claim driver performance;
claim paper-level self-identification.
```

## Decision

M1348 admits:

```text
m1349-paper-route-materialized-source-history-pair-group-limited-replay-preflight
```

M1349 may run the two lower-level replay commands above and write a summary. It
must stop at the first failed proof surface and must not promote even if both
surfaces pass.
