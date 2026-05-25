# M945 V4 Public Base Controlled Fusion Candidate Replay Gate Design

## Purpose

M944 produced a materialized exact objective candidate:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

M945 designs the next no-training closed-loop replay/proof-retention gate.
It does not execute replay, run PPO, use private holdout, or promote.

## Candidate State

Current public-gate base remains:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Primary candidate:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

Backup candidates:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0675.pt
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_07.pt
```

M944 already established:

```text
materialized_checkpoint_count: 3
exact_candidate_count: 3
primary_candidate_exact_pass: true
backup_candidate_exact_pass_count: 2
forbidden_parameter_changed: false
training_started: false
replay_used: false
ppo_used: false
promoted: false
```

## Replay Gate Scope

M946 should be a no-training replay/proof-retention implementation. It should
compare the primary candidate against M399 base.

Required proof surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Required diagnostics:

```text
source-diverse protected gate if compatible with the M399/M944 pair
old key 9944 diagnostic as diagnostic-only, not a singleton veto
input-contract check
```

Required behavior retention:

```text
public behavior seeds: 9505, 9506
candidate normal
candidate reset-hidden
candidate zero-all response/action-history ablation
```

The behavior check should retain the existing ordering:

```text
normal success >= reset success >= zero-all success
normal termination does not regress materially versus M399
```

## Acceptance Criteria

M946 can only route forward if:

```text
exact objective compatibility from M944 is retained by reference
all six replay surfaces retain normal-history success and wrong-history failure
source-diverse protected gate passes or is explicitly classified as incompatible/stale
old key 9944 remains diagnostic-only with a documented margin gap
behavior seeds 9505 and 9506 do not regress materially
actor inputs are unchanged
training_started is false
replay_used is true
ppo_used is false
promoted is false
```

M946 must not promote the candidate. A pass should only admit a follow-up
promotion/generalization design or a broader replay gate, depending on the
results.

## Failure Routing

If a replay surface fails:

```text
classify as proof_washout or behavior_regression depending on failure mode;
do not run PPO;
audit which surface and row failed;
```

If behavior seeds regress while replay rows pass:

```text
classify as behavior_regression;
route to behavior-retention audit;
```

If source-diverse protected tooling is stale or incompatible:

```text
classify as lineage_invalid or metric_artifact;
route to replay-surface refresh audit;
```

If all replay/proof/behavior checks pass:

```text
route to promotion/generalization gate design;
promotion still blocked until that design is written and executed.
```

## M946 Required Outputs

M946 should produce:

```text
runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/summary.json
runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/full_gates/
docs/m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation.md
```

The summary should include:

```text
primary_checkpoint
baseline_checkpoint
exact_candidate_reference_pass
six_public_replay_gates_pass
source_diverse_protected_status
old_key_9944_status
behavior_seed9505_success_delta
behavior_seed9506_success_delta
reset_zero_all_ordering_retained
actor_inputs_changed
training_started
replay_used
ppo_used
promoted
result_class
```

## Decision

M945 admits M946 as a no-training replay/proof-retention implementation.

Next blocker:

```text
m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation
```
