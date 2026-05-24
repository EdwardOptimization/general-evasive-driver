# M545 L3 Recurrent Recipe Repair Design

## Purpose

M545 designs a controlled repair path for the L3 online-GRU recurrent recipe
after M543/M544 showed that the seed-3540 L3 variance run regressed badly
against the finite-window L2 baseline.

This milestone is design-only. It does not train, tune, evaluate public rows, or
promote a checkpoint.

## Starting Evidence

M544 established the important boundary:

- the P0 human-view/no-wheel/no-oracle actor contract is intact;
- the L2/L3 config differences are exactly the intended finite-window versus
  online-GRU differences;
- L3 can reach a high route return early, with `best_return = 52.598733` at
  step `1792`;
- final L3 performance collapses, with `last4_return_mean = 23.259713` and
  final return `15.771149`;
- L2 improves later and remains strong, with `last4_return_mean = 44.089672`;
- M543 public frozen-source eval shows broad L3 regression: L3-L2 paired
  success delta `-0.195633`, collision delta `+0.190731`, margin delta
  `-0.793024`, and `423` L2-completed to L3-collision terminal pairs.

The current diagnosis is therefore:

```text
valid P0 contract
not enough evidence that online-GRU is weak
confirmed evidence that the current L3 optimization/checkpoint recipe is weak
```

## Repair Principles

The repair branch must keep these constraints:

1. Preserve the P0 actor input contract. No hidden parameters, wheel channels,
   oracle labels, TTC, path/reference variables, or rule answers may enter the
   actor.
2. Preserve L2 as a serious finite-window baseline. L3 repair is allowed as a
   diagnostic branch, but it cannot be compared as final evidence until the
   repaired recipe is frozen and re-matched against L0/L2.
3. Do not use public frozen-source rows for checkpoint selection. Public rows
   can diagnose repaired candidates after a route-health screen, but they cannot
   be treated as private evidence.
4. Select checkpoints by a pre-registered route rule before any public
   frozen-source eval.
5. Do not promote any checkpoint in the repair-design or repair-config stages.

## Approved Repair Controls

M546 should implement an L3-only repair config family that changes only
optimization and checkpoint-selection controls. The environment, task
distribution, observation contract, and history level stay identical to
`configs/ppo_m541_matched_l3_variance_4096.json`.

Approved controls:

- add `checkpoint_interval_steps = 512`;
- lower `learning_rate`;
- optionally lower `max_grad_norm`;
- keep `total_steps = 4096`, `rollout_steps = 64`, `num_envs = 4`,
  `update_epochs = 2`, `minibatch_size = 128`, `hidden_size = 64`,
  `eval_episodes = 5`, and seed `3540` for the first repair route pilot.

Disallowed controls:

- changing environment sampler ranges;
- changing reward terms;
- changing obstacle/perception settings;
- changing actor inputs or adding wheel/privileged fields;
- changing L0/L2 configs as a hidden response to an L3 result;
- selecting a checkpoint after inspecting public frozen-source outcome rows.

## Candidate Configs

M546 should add these diagnostic configs:

| Candidate | Intent | Changes From M541 L3 |
| --- | --- | --- |
| `fast_select` | test whether early-peak checkpoint selection alone repairs the route failure | `checkpoint_interval_steps = 512` |
| `lr1e4` | reduce recurrent update aggressiveness | `learning_rate = 0.0001`, `max_grad_norm = 0.25`, `checkpoint_interval_steps = 512` |
| `lr5e5` | more conservative recurrent update | `learning_rate = 0.00005`, `max_grad_norm = 0.25`, `checkpoint_interval_steps = 512` |

These configs are diagnostic. They do not create a fair final L3-vs-L2 claim
until a repaired recipe is frozen and re-run against matched L0/L2 controls.

## Checkpoint Selection Rule

For each L3 repair run, select the candidate checkpoint before public eval using
only training-route artifacts and intermediate checkpoint metadata.

Selection rule:

1. Evaluate all available interval checkpoints plus the final checkpoint on the
   same route eval protocol.
2. Select the checkpoint with highest route `return_mean`.
3. Break ties by lower `termination_rate`.
4. Break remaining ties by lower lateral RMSE.
5. If all interval checkpoints have `termination_rate = 1.0` and route
   `return_mean <= 25.0`, reject the candidate as route-unhealthy.

This rule is intentionally simple. It exists to prevent the M544 failure mode
where an early useful recurrent policy is overwritten by the final checkpoint.

## Route-Health Gate

A repaired L3 candidate can proceed to public frozen-source diagnostics only if
the selected route checkpoint satisfies:

```text
return_mean > 25.0
termination_rate < 1.0
valid P0 history_baseline metadata
selected by the pre-registered route rule above
```

If no candidate passes this route-health gate, classify the repair attempt as
`training_instability` and do not spend public eval budget.

## Public Diagnostic Gate

After route health passes, evaluate the selected L3 candidate on the same public
M543 frozen-source natural surfaces and compare it against the M542 L0/L2
reference rows.

Minimum continuation rule:

```text
L3 - L0 paired success delta > 0
L3 - L0 paired clearance-margin delta > 0
```

If L3 recovers above L0 but remains behind L2, classify the result as:

```text
finite-window history remains competitive under the current task distribution
```

If L3 remains below L0, classify the result as `training_instability` and audit
the recurrent sequence handling or actor update recipe before running more
seeds.

## Later Re-Matching Boundary

If an L3 repair candidate passes route health and public diagnostics, do not
claim an architecture win yet. The next fair step is to freeze the repaired L3
recipe, construct matched L0/L2 counterparts if the recipe changes any generic
PPO controls, and repeat the staged variance ladder.

The clean claim boundary remains:

```text
route repair -> public diagnostics -> freeze recipe -> matched multi-seed run
-> public paired audit -> fresh holdout only after recipe freeze
```

## M546 Admission

M545 admits M546:

```text
m546-l3-recurrent-repair-config-family
```

M546 should implement the repair configs and tests only. It should not train or
promote a checkpoint.

## Decision

```text
l3_recurrent_repair_design_admit_m546_config_family
```
