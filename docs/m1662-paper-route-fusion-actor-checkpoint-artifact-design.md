# M1662 Paper-Route Fusion Actor Checkpoint Artifact Design

## Summary

M1662 designs the checkpoint-artifact preflight admitted by M1661. It does not
write a checkpoint, rerun repair, run replay, run PPO, train, promote, use
private holdout, change actor inputs, or claim paper-level or level3
self-identification evidence.

Decision:

```text
fusion_actor_checkpoint_artifact_design_admit_primary_artifact_implementation
```

The next safe step is a single bounded artifact materialization over the M1660
primary alpha `0.2` candidate. Alpha `0.4` and alpha `1.0` remain diagnostic
evidence only for now.

## Candidate Selection

Materialize exactly one candidate first:

```text
candidate: alpha_0_2
proposal_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt
base_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
source_result: runs/m1660_fusion_actor_proposal_repair/candidate_summary.csv
```

Reason:

```text
alpha 0.2 is the primary M1660 candidate;
it passed the public objective-sanity gate;
it has the smallest selected proposal delta;
it reduced exact residual by 0.40519785496674926;
it needs only one accepted backtracking step;
it is the least aggressive artifact candidate before closed-loop replay audit.
```

Do not materialize alpha `0.4` or alpha `1.0` in the first artifact milestone.
They are useful stress diagnostics, but writing multiple repaired checkpoints at
once would blur lineage and make replay failure attribution harder.

## Artifact Materialization Contract

M1663 may run one deterministic materialization command whose only purpose is
to reproduce the M1660 in-memory alpha `0.2` repair and write it to disk.

Allowed trainable scope:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

All other parameters must remain bitwise or numerically unchanged from the
alpha `0.2` proposal checkpoint within the implementation's recorded tolerance.

Required output layout:

```text
runs/m1663_fusion_actor_checkpoint_artifact/
  summary.json
  artifact_metadata.json
  candidate_summary.csv
  guardrail_summary.csv
  checksums.sha256
  checkpoints/
    alpha_0_2_fusion_actor_repaired.pt
```

Required metadata:

```text
artifact_id
artifact_path
artifact_sha256
git_commit
base_checkpoint
base_checkpoint_sha256
proposal_checkpoint
proposal_checkpoint_sha256
source_m1660_summary
source_m1660_candidate_summary
source_m1660_guardrail_summary
selected_alpha
trainable_scope
feature_mode
repair_algorithm
repair_args
initial_positive_exact_residual_mean
repaired_positive_exact_residual_mean
positive_exact_residual_reduction_ratio
accepted_backtracking_step_count
excluded_parameter_delta_max
actor_input_contract_changed_count
checkpoint_artifact_count
private_holdout_used_count
promoted_count
```

The artifact must be labeled as:

```text
objective_sanity_artifact_only
```

It must not be labeled as a promoted base, replay-passing checkpoint,
generalization result, paper result, or level3 self-ID result.

## Reproduction Thresholds

M1663 should compare the materialized result against M1660 alpha `0.2`.

Minimum pass thresholds:

```text
selected_alpha == 0.2
checkpoint_artifact_count == 1
candidate_public_pass == true
positive_exact_residual_reduction_ratio >= 0.25
excluded_parameter_delta_violation_count == 0
diagnostic_rows_used_as_positive_count == 0
donor_plus_action_used_as_loss_target_count == 0
training_started_count == 0
ppo_used_count == 0
promoted_count == 0
private_holdout_used_count == 0
actor_input_contract_changed_count == 0
level3_self_id_claim_count == 0
```

Expected reference values from M1660 alpha `0.2`:

```text
initial_positive_exact_residual_mean: 0.0012401377316564322
repaired_positive_exact_residual_mean: 0.0007376365829259157
positive_exact_residual_reduction_ratio: 0.40519785496674926
accepted_backtracking_step_count: 1
```

If exact reproduction differs, M1663 must record the delta and classify whether
the difference is deterministic-tolerance noise, implementation drift, or a
failed materialization.

## Guardrails

M1663 is allowed to write exactly one checkpoint artifact. Everything else
remains blocked:

```text
no replay gates;
no closed-loop evaluation;
no PPO;
no training curriculum;
no promotion;
no private holdout;
no actor input change;
no new positive rows;
no diagnostic-row role changes;
no donor-plus action as target;
no paper-level claim;
no level3 self-identification claim.
```

The implementation must also record that the checkpoint was produced from
public fixed-tensor objective-sanity evidence. This keeps public overfit risk
visible before any replay gate.

## Post-Artifact Audit

M1663 may not route directly to replay. If it writes the artifact, the next
milestone must be a result audit:

```text
m1664-paper-route-fusion-actor-checkpoint-artifact-result-audit
```

M1664 must verify:

```text
exactly one checkpoint artifact exists;
artifact checksum and lineage are complete;
the artifact reproduces M1660 alpha 0.2 objective-sanity evidence;
excluded-parameter guardrails are clean;
no replay/PPO/training/promotion/private-holdout shortcut occurred;
the artifact remains objective-sanity evidence only.
```

Only after M1664 may a later milestone design replay/proof gates for the
artifact.

## Unsupported Claims

M1662 does not support:

```text
checkpoint artifact generation;
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Admit exactly one bounded implementation:

```text
m1663-paper-route-fusion-actor-checkpoint-artifact-implementation
```

M1663 must implement artifact materialization only for the alpha `0.2` primary
candidate, write the required metadata/checksums, and stop before replay.
