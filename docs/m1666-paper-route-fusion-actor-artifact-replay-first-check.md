# M1666 Paper-Route Fusion Actor Artifact Replay First Check

## Summary

M1666 implements and runs the first public replay checks for the M1663 alpha
`0.2` `fusion_actor` checkpoint artifact.

Decision:

```text
fusion_actor_artifact_first_check_failed_route_to_audit
```

This is a clean negative result. The artifact checksum and P0 actor contract
passed, replay executed without errors, and no full-stack/PPO/training/
promotion/private-holdout shortcuts occurred. Both first-check replay surfaces
failed because the normal-history branch regressed strongly.

M1666 does not admit repair. It routes to M1667 failure audit.

## Implementation

Added:

```text
src/autodrift/fusion_actor_artifact_replay_gate.py
tests/test_fusion_actor_artifact_replay_gate.py
```

The wrapper performs:

```text
Stage 0: checkpoint checksum and P0 actor-contract sanity
Stage 1: M183/M170 and M267/M264 public boundary-outcome replay checks
```

It does not run full-stack replay.

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_fusion_actor_artifact_replay_gate.py
```

Result:

```text
4 passed in 2.00s
```

Official command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.fusion_actor_artifact_replay_gate \
  --checkpoint runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt \
  --artifact-summary runs/m1663_fusion_actor_checkpoint_artifact/summary.json \
  --run-dir runs/m1666_fusion_actor_artifact_replay_first_check \
  --mode first_check
```

Artifacts:

```text
runs/m1666_fusion_actor_artifact_replay_first_check/summary.json
runs/m1666_fusion_actor_artifact_replay_first_check/checkpoint_sanity.json
runs/m1666_fusion_actor_artifact_replay_first_check/first_check_gate_summary.csv
runs/m1666_fusion_actor_artifact_replay_first_check/guardrail_summary.csv
runs/m1666_fusion_actor_artifact_replay_first_check/replay/m183_m170/
runs/m1666_fusion_actor_artifact_replay_first_check/replay/m267_m264/
```

## Checkpoint Sanity

Stage 0 passed:

```text
checkpoint_sanity_pass: true
artifact_sha256_match: true
p0_actor_contract_pass: true
obs_dim: 72
actor_encoder: human_view_online_gru
artifact_label: objective_sanity_artifact_only
```

## Replay Result

Aggregate:

```text
first_check_pass: false
m183_m170_first_check_pass: false
m267_m264_first_check_pass: false
replay_execution_error_count: 0
result_class: fusion_actor_artifact_first_check_m183_m170_failure
```

M183/M170:

```text
rows: 17
baseline_success_drop_count: 17
candidate_success_drop_count: 0
normal_success_delta: -1.0
normal_margin_mean_delta: -0.011979825763062477
margin_gap_mean_delta: -0.00040754210244511
success_drop_count_delta: -17
normal_success_retention_pass: false
normal_margin_retention_pass: false
wrong_history_gap_retention_pass: true
success_drop_count_retention_pass: false
gate_pass: false
```

M267/M264:

```text
rows: 17
baseline_success_drop_count: 17
candidate_success_drop_count: 2
normal_success_delta: -0.8823529411764706
normal_margin_mean_delta: -0.01067500028918613
margin_gap_mean_delta: -0.0006663758373334286
success_drop_count_delta: -15
normal_success_retention_pass: false
normal_margin_retention_pass: false
wrong_history_gap_retention_pass: true
success_drop_count_retention_pass: false
gate_pass: false
```

Failure counts:

```text
proof_washout_count: 2
behavior_regression_count: 2
lineage_invalid_count: 0
contract_violation_count: 0
metric_artifact_count: 0
```

Interpretation:

```text
wrong-history branches remain failing, but normal-history branches fail too;
therefore success-drop proof collapses mainly because the candidate loses normal-branch behavior.
```

## Guardrails

```text
full_stack_replay_used_count: 0
ppo_used_count: 0
training_started_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

## Supported Claims

M1666 supports:

```text
the M1663 artifact loads and satisfies P0 actor contract;
the first public replay checks execute cleanly;
the artifact fails M183/M170 and M267/M264 first-check replay;
the failure is behavior/proof retention regression, not lineage or contract failure.
```

## Unsupported Claims

M1666 does not support:

```text
full-stack replay;
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to failure audit:

```text
m1667-paper-route-fusion-actor-artifact-first-check-failure-audit
```

M1667 must classify the negative result and decide whether to stop the artifact
route, design a behavior-retention repair, refresh sources, or synthesize the
branch. No repair or PPO is admitted before that audit.
