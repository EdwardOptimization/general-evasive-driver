# M1664 Paper-Route Fusion Actor Checkpoint Artifact Result Audit

## Summary

M1664 audits the M1663 alpha `0.2` `fusion_actor` checkpoint artifact before
any replay gate, PPO route, training, promotion, or private-holdout use.

Decision:

```text
fusion_actor_checkpoint_artifact_audit_admit_replay_gate_design
```

The M1663 artifact is a clean objective-sanity checkpoint artifact. It has one
checkpoint file, complete metadata/checksums, clean guardrails, and exact
objective-sanity reproduction of the M1660 alpha `0.2` result. It still does
not justify replay, behavior, PPO, promotion, private-holdout, paper-level, or
level3 self-identification claims.

## Audited Artifacts

```text
runs/m1663_fusion_actor_checkpoint_artifact/summary.json
runs/m1663_fusion_actor_checkpoint_artifact/artifact_metadata.json
runs/m1663_fusion_actor_checkpoint_artifact/checksums.sha256
runs/m1663_fusion_actor_checkpoint_artifact/candidate_summary.csv
runs/m1663_fusion_actor_checkpoint_artifact/guardrail_summary.csv
runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
docs/m1663-paper-route-fusion-actor-checkpoint-artifact-implementation.md
```

Exactly one checkpoint artifact exists:

```text
runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
```

## Artifact Audit

Artifact identity:

```text
artifact_label: objective_sanity_artifact_only
artifact_id: m1663_alpha_0_2_fusion_actor_repaired
selected_alpha: 0.2
checkpoint_artifact_count: 1
unexpected_checkpoint_artifact_count: 0
artifact_exists: true
passes_public_smoke_gates: true
result_class: fusion_actor_checkpoint_artifact_public_pass
```

Lineage:

```text
base_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
proposal_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt
source_candidate_summary: runs/m1660_fusion_actor_proposal_repair/candidate_summary.csv
source_m1660_summary: runs/m1660_fusion_actor_proposal_repair/summary.json
source_m1660_guardrail_summary: runs/m1660_fusion_actor_proposal_repair/guardrail_summary.csv
git_commit: e1cfe2874cb6124f391c0994663732d8754ca781
```

Checksums:

```text
base_checkpoint_sha256: fca7dded51cc9137a38511926700eeb215363bdb54991c727d6c4bb7620fd729
proposal_checkpoint_sha256: 0ae858cf7f7ac1808b288dd4585c2423b3cc8216661851dbbcbfe59cc108eec4
artifact_sha256: c7829fc0596bd6658440fd343282a4cbb2907a37b6b30424698c2e29d0b8c191
```

Objective reproduction:

```text
initial_positive_exact_residual_mean: 0.0012401377316564322
repaired_positive_exact_residual_mean: 0.0007376365829259157
positive_exact_residual_reduction_ratio: 0.40519785496674926
accepted_backtracking_step_count: 1
candidate_public_pass: true
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

## Public-Overfit Risk

The artifact was produced from public exact tensors and a single selected
proposal candidate. Public fixed-tensor overfit risk remains high. The artifact
is now suitable for a public replay-gate design, not for direct replay,
promotion, private holdout, or paper claims.

Replay should be designed in stages:

```text
1. checkpoint load and P0 contract sanity
2. first public proof replay checks on M183/M170 and M267/M264
3. full public replay/protected/behavior stack only if first checks pass
4. result audit before any PPO, promotion, or private holdout route
```

## Supported Claims

M1664 supports:

```text
the M1663 alpha 0.2 artifact is a valid objective-sanity checkpoint artifact;
metadata and checksum lineage are complete;
exact residual reproduction matches M1660 alpha 0.2;
the next safe process step is replay-gate design.
```

## Unsupported Claims

M1664 does not support:

```text
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Route Decision

Admit design-only replay gate:

```text
m1665-paper-route-fusion-actor-artifact-replay-gate-design
```

M1665 must design the replay/proof gate sequence for the M1663 artifact. It
must not run replay, PPO, training, promotion, private holdout, actor-input
changes, or level3 claims.
