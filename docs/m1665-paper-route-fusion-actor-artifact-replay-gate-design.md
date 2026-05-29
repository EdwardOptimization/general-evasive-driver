# M1665 Paper-Route Fusion Actor Artifact Replay Gate Design

## Summary

M1665 designs staged public replay gates for the M1663 alpha `0.2`
`fusion_actor` checkpoint artifact. It does not run replay, PPO, training,
promotion, private holdout, actor-input changes, or level3 claims.

Decision:

```text
fusion_actor_artifact_replay_gate_design_admit_first_check_implementation
```

The next step should be a bounded first-check replay implementation. It should
verify checkpoint load and P0 actor contract, then run only the minimal public
proof checks needed to determine whether the objective-sanity artifact is worth
full-stack replay.

## Artifact Under Test

```text
artifact_checkpoint:
  runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt

artifact_sha256:
  c7829fc0596bd6658440fd343282a4cbb2907a37b6b30424698c2e29d0b8c191

artifact_label:
  objective_sanity_artifact_only
```

The artifact was created from public exact tensors. Replay gates must therefore
be treated as public proof/retention checks, not promotion or paper evidence.

## Replay Gate Stages

### Stage 0: Load And Contract Sanity

M1666 must first verify:

```text
checkpoint exists;
sha256 matches c7829fc0596bd6658440fd343282a4cbb2907a37b6b30424698c2e29d0b8c191;
checkpoint loads with load_actor_critic_checkpoint;
actor_encoder is P0 human-view no-wheel online GRU;
actor observation frame remains 72 dim;
no wheel/slip/privileged actor inputs are present;
artifact metadata label remains objective_sanity_artifact_only.
```

If Stage 0 fails, stop before replay and classify:

```text
lineage_invalid
contract_violation
metric_artifact
```

as appropriate.

### Stage 1: First Public Proof Checks

M1666 should then run the smallest public replay checks:

```text
M183/M170 first-check replay
M267/M264 first-check replay
```

Rationale:

```text
M183/M170 protects the old fragile row16/terminal-margin surface;
M267/M264 protects the current-family rejected-history proof surface;
these two checks cover the main historical failure modes before full-stack cost.
```

Pass criteria:

```text
checkpoint_sanity_pass == true
m183_m170_first_check_pass == true
m267_m264_first_check_pass == true
replay_execution_error_count == 0
promotion/private_holdout/PPO/training counts == 0
```

Failure taxonomy:

```text
proof_washout:
  wrong-history or protected proof row no longer has required success-drop or margin relation

behavior_regression:
  normal-history branch collides or loses required terminal margin

lineage_invalid:
  artifact checksum, metadata, or parent checkpoint does not match M1663

contract_violation:
  actor input contract or checkpoint architecture is not P0 human-view no-wheel 72-dim online-GRU

metric_artifact:
  replay cannot be trusted because required rows, seeds, or metrics are missing
```

### Stage 2: Full Public Stack, Later Only

If M1666 first-check passes and an audit accepts it, a later milestone may
design full-stack replay. That later design should include:

```text
old public replay surfaces;
current-family rejected-history replay surface;
protected-key/protected-surface diagnostics;
behavior seeds;
termination reason histogram;
artifact-vs-base comparison;
mandatory result audit before PPO or promotion.
```

M1665 does not admit Stage 2 execution.

## M1666 Output Contract

M1666 should write:

```text
runs/m1666_fusion_actor_artifact_replay_first_check/
  summary.json
  checkpoint_sanity.json
  first_check_gate_summary.csv
  replay_rows.csv
  guardrail_summary.csv
```

Required summary fields:

```text
checkpoint_sanity_pass
artifact_sha256_match
p0_actor_contract_pass
m183_m170_first_check_pass
m267_m264_first_check_pass
first_check_pass
replay_execution_error_count
proof_washout_count
behavior_regression_count
lineage_invalid_count
contract_violation_count
metric_artifact_count
ppo_used_count
training_started_count
promoted_count
private_holdout_used_count
actor_input_contract_changed_count
level3_self_id_claim_count
```

M1666 must route to a result audit regardless of pass/fail.

## Route Logic

If M1666 passes:

```text
route to first-check result audit;
audit may then admit full public replay-stack design.
```

If M1666 fails:

```text
route to first-check result audit;
audit classifies proof_washout / behavior_regression / lineage_invalid /
contract_violation / metric_artifact;
no repair or PPO may start before that audit.
```

## Unsupported Claims

M1665 does not support:

```text
replay execution;
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Admit exactly one bounded first-check implementation:

```text
m1666-paper-route-fusion-actor-artifact-replay-first-check
```

M1666 may execute Stage 0 and Stage 1 only. It must stop before full-stack
replay, PPO, promotion, or private holdout.
