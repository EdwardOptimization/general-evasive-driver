# M890 V4 Enriched Pair-Delta Replay Proof Gate Audit

## Purpose

M890 audits the M889 proof-gate positive result and chooses the next route.

M890 is audit-only:

```text
no training
no replay execution
no PPO
no promotion
```

## Evidence Summary

M889 candidate:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
```

Baseline:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M889 passed:

```text
exact objective recheck
six replay/proof surfaces
behavior seeds 9505 and 9506
```

Key results:

```text
exact rows reconstructed: 247 / 247
exact split deltas versus M568/M883: all nonpositive
replay gates passed: 6 / 6
replay gates failed: 0
candidate success-drop regressions: 0
behavior success mean: 0.8125
behavior termination mean: 0.1875
behavior clearance delta versus M568: +0.0004892324201435372
behavior return delta versus M568: -0.003998606511459002
```

## Supported Claims

M889 supports this claim:

```text
For the M886 seed-10886 objective-only actor-coupling update, alpha_0_1
preserves the registered M568-relative exact objective, replay/proof, and
behavior-retention gates.
```

This is meaningful because it connects the M883/M886 one-step exact objective
to closed-loop replay surfaces without immediate proof washout.

## Unsupported Claims

M889 does not support these claims:

```text
the checkpoint is a new public-gate driver base
the objective recipe is repeat-stable
the update improves driver performance in a meaningful way
the result generalizes to fresh source distributions
PPO continuation is now safe
```

Reasons:

- the branch is rooted at the M568 diagnostic BC checkpoint, not the latest
  public-gate driver base;
- M889 is a single objective-update seed;
- exact rows and replay surfaces are public workflow artifacts;
- behavior metrics are effectively retention-level;
- no fresh source/generalization distribution was evaluated.

## Routing Decision

The next step should be a fresh-seed repeat of the M886 objective-only probe.

Rationale:

- single-seed proof-gate success is not enough to trust the objective direction;
- the movement is small, so repeat stability matters more than increasing step
  size;
- replay/generalization gates should wait until at least one fresh objective
  seed reproduces exact-admissible behavior;
- PPO remains premature.

The repeat should keep the same recipe and change only optimizer/minibatch seed.
It should not tune against holdouts.

## Required Next Experiment

Next milestone:

```text
m891-v4-enriched-pair-delta-objective-only-fresh-seed-repeat
```

M891 should run:

```text
same M886 command
seed 10887
run_dir runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887
```

Pass condition:

```text
247 / 247 tensor rows reconstructed
at least one nonzero exact-admissible interpolation alpha
no exact holdout regression beyond 1e-4
actor input contract unchanged
M761 residual head unchanged
no PPO
no promotion
```

If M891 passes, then route to replay/proof gates for its selected alpha. If it
fails, audit seed fragility before adding data, increasing learning rate, or
changing objective terms.

## Decision

Decision:

```text
v4_enriched_pair_delta_replay_proof_gate_audit_route_to_fresh_seed_repeat
```

Next:

```text
m891-v4-enriched-pair-delta-objective-only-fresh-seed-repeat
```
