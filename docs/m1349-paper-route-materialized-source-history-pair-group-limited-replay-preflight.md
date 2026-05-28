# M1349 Paper-Route Materialized Source-History Pair-Group Limited Replay Preflight

## Summary

M1349 runs the first public replay proof preflight for the M1346 pair-group
objective candidate.

Result:

```text
materialized_source_history_limited_replay_preflight_m267_m264_proof_washout
```

M267/M264 failed, so M1349 stopped as pre-registered and did not run M183/M170.

## Command

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

## Result

M267/M264 comparison:

```text
rows: 17
baseline_normal_success_rate: 1.0
candidate_normal_success_rate: 0.0
normal_success_delta: -1.0
baseline_wrong_history_success_rate: 0.0
candidate_wrong_history_success_rate: 0.0
wrong_history_success_delta: 0.0
baseline_success_drop_count: 17
candidate_success_drop_count: 0
success_drop_count_delta: -17
normal_margin_mean_delta: -0.1065894892
margin_gap_mean_delta: -0.0132868003
gate_pass: false
```

Every replay retention check fails:

```text
normal_success_retention_pass: false
normal_margin_retention_pass: false
wrong_history_gap_retention_pass: false
success_drop_count_retention_pass: false
```

Terminal reasons:

```text
m1154_base normal: obstacle_completed 17 / 17
m1154_base wrong-history: collision 17 / 17
m1346_pair_group normal: collision 17 / 17
m1346_pair_group wrong-history: collision 17 / 17
```

This is not the benign failure where the candidate simply makes wrong-history
branches safe. It is a normal-branch collapse on the first current-family proof
surface.

## Stop Rule

M1348 specified:

```text
Run M267/M264 first.
If M267/M264 fails, stop and do not run M183/M170.
```

M1349 followed that rule:

```text
m183_m170_gate_ran: false
m183_m170_skipped_reason: m267_m264_failed_first_surface
```

## Interpretation

Supported:

```text
The M1346 fixed source-history objective improvement does not transfer to the
current-family closed-loop replay proof surface.
```

Supported:

```text
The M1346 update is too aggressive for closed-loop proof retention even though
its parameter mutation scope is clean.
```

Supported:

```text
The failure mode is normal-branch collision, not only loss of wrong-history
sensitivity.
```

Not supported:

```text
M1346 should be used as a PPO base.
```

Not supported:

```text
M1346 should enter full public replay or promotion gates.
```

Not supported:

```text
M1346 provides driver-performance or strong self-identification evidence.
```

## Failure Taxonomy

Primary failure:

```text
proof_washout
```

More specific diagnosis:

```text
current_family_normal_branch_collision
```

No evidence of:

```text
private_holdout_contamination
PPO contamination
promotion gate misuse
actor-input expansion
threshold relaxation
```

## Decision

Reject M1346 as a replay candidate.

Next:

```text
m1350-paper-route-materialized-source-history-pair-group-replay-failure-audit
```

M1350 should audit why the objective-positive update destroys M267/M264 normal
success. The likely next routes are:

```text
smaller trust-region/interpolation around M1346;
explicit replay-aware active-set retention for M267/M264 normal branch;
objective tradeoff repair that penalizes normal-branch collision risk;
or route back to materialized objective design if the source-current objective
is too disconnected from closed-loop replay.
```

Do not run PPO from M1346.
