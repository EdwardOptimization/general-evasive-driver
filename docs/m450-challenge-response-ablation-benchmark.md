# M450 Challenge Response Ablation Benchmark

M450 attempted to benchmark M399 response/history ablations on the M449
challenge configs. Both benchmark commands failed during scenario sampling
before policy evaluation. No training, PPO, checkpoint promotion, threshold
relaxation, or actor input/output change occurred.

## Commands Attempted

Near-threshold:

```text
runs/m450_near_threshold_ablation_seed9900
```

Late high-energy:

```text
runs/m450_late_high_energy_ablation_seed9900
```

Both commands used:

```text
episodes = 128
seed = 9900
policies = heuristic + M399 normal/reset/zero-current/zero-all/no-action
```

## Failure

Both runs failed at `env.reset()` with:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

This happened before any checkpoint policy result was produced. Therefore M450
cannot answer whether the challenge configs reveal response-history dependence.

## Interpretation

M449 proved the challenge configs can run on seed block `9800`, but M450 shows
they are not robust enough across fresh seed blocks. The issue is not the actor,
PPO, or the self-ID hypothesis. It is the scenario generator: the filters are
still tight enough that some seed blocks cannot find valid AEB-infeasible,
threshold-constrained obstacle scenarios within the configured sampling budget.

This is a useful negative result. It prevents treating the M449 configs as a
stable generalization benchmark.

## Harness Update

This failure does not fit the existing taxonomy cleanly, so M450 extends the
research process failure types with:

```text
scenario_sampling_failure
```

This is for config/scenario-generation failures that occur before training or
policy evaluation.

## Decision

M450 is a rejected diagnostic attempt:

- no benchmark result is available;
- both challenge configs fail seed-block robustness;
- no checkpoint is promoted;
- actor inputs remain unchanged.

Admit:

```text
m451-challenge-config-sampling-robustness-repair
```

M451 should create robust replacement challenge configs rather than mutating
the M449 artifacts in place. It should validate sampling across multiple seed
blocks before rerunning ablation or policy-difference diagnostics.
