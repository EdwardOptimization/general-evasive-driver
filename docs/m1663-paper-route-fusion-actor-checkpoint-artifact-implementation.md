# M1663 Paper-Route Fusion Actor Checkpoint Artifact Implementation

## Summary

M1663 implements and runs the bounded checkpoint-artifact materialization
admitted by M1662.

Decision:

```text
fusion_actor_checkpoint_artifact_public_pass_route_to_audit
```

The run materialized exactly one alpha `0.2` `fusion_actor` repaired checkpoint
artifact, recorded lineage and checksums, reproduced the M1660 objective-sanity
metrics, and kept replay/PPO/training/promotion/private-holdout/actor-input and
level3 guardrails blocked.

This is still an objective-sanity artifact. It is not replay, behavior,
promotion, private-holdout, paper-level, or level3 self-ID evidence.

## Implementation

Added:

```text
src/autodrift/fusion_actor_checkpoint_artifact.py
tests/test_fusion_actor_checkpoint_artifact.py
```

Extended:

```text
src/autodrift/fusion_actor_proposal_repair.py
```

The existing candidate repair routine now has default-off checkpoint artifact
arguments. Default M1660 behavior remains no-checkpoint; M1663 explicitly
allows one artifact.

Allowed materialized scope:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

Selected artifact candidate:

```text
alpha: 0.2
base: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
proposal: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt
artifact: runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
```

Alpha `0.4` and alpha `1.0` were not materialized.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_fusion_actor_checkpoint_artifact.py tests/test_fusion_actor_proposal_repair.py
```

Result:

```text
6 passed in 2.10s
```

Official M1663 command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.fusion_actor_checkpoint_artifact \
  --base-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --proposal-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt \
  --candidate-summary runs/m1660_fusion_actor_proposal_repair/candidate_summary.csv \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --run-dir runs/m1663_fusion_actor_checkpoint_artifact \
  --selected-alpha 0.2
```

Artifacts:

```text
runs/m1663_fusion_actor_checkpoint_artifact/summary.json
runs/m1663_fusion_actor_checkpoint_artifact/artifact_metadata.json
runs/m1663_fusion_actor_checkpoint_artifact/checksums.sha256
runs/m1663_fusion_actor_checkpoint_artifact/candidate_summary.csv
runs/m1663_fusion_actor_checkpoint_artifact/guardrail_summary.csv
runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
```

## Result

Aggregate:

```text
passes_public_smoke_gates: true
result_class: fusion_actor_checkpoint_artifact_public_pass
selected_alpha: 0.2
checkpoint_artifact_count: 1
unexpected_checkpoint_artifact_count: 0
artifact_label: objective_sanity_artifact_only
```

Objective reproduction:

```text
initial_positive_exact_residual_mean: 0.0012401377316564322
repaired_positive_exact_residual_mean: 0.0007376365829259157
positive_exact_residual_reduction_ratio: 0.40519785496674926
accepted_backtracking_step_count: 1
candidate_public_pass: true
```

Checksums:

```text
base_checkpoint_sha256: fca7dded51cc9137a38511926700eeb215363bdb54991c727d6c4bb7620fd729
proposal_checkpoint_sha256: 0ae858cf7f7ac1808b288dd4585c2423b3cc8216661851dbbcbfe59cc108eec4
artifact_sha256: c7829fc0596bd6658440fd343282a4cbb2907a37b6b30424698c2e29d0b8c191
git_commit: e1cfe2874cb6124f391c0994663732d8754ca781
```

Guardrails:

```text
excluded_parameter_delta_violation_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

## Supported Claims

M1663 supports:

```text
the alpha 0.2 fusion_actor repaired candidate can be materialized as one checkpoint artifact;
the artifact reproduces M1660 alpha 0.2 objective-sanity metrics;
artifact lineage and checksums are recorded;
the artifact is labeled objective_sanity_artifact_only;
closed-loop replay and promotion remain blocked until audit.
```

## Unsupported Claims

M1663 does not support:

```text
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to result audit:

```text
m1664-paper-route-fusion-actor-checkpoint-artifact-result-audit
```

M1664 must audit the artifact, metadata, checksums, and guardrails before any
replay/proof gate design.
