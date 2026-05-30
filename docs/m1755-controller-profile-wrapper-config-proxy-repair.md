# M1755 Controller Profile Wrapper Config Proxy Repair

- status: completed
- decision: `wrapper_config_proxy_repair_admit_revised_execution_rerun`
- parent audit: `docs/m1754-paper-route-task-quality-revised-scenario-taxonomy-execution-failure-audit.md`
- no full rollout: true
- training/replay/PPO: false

## Summary

M1755 repairs the dominant M1753 failure by adding a `config` proxy property to
`ControllerProfileObservationWrapper`. This lets `run_episode_with_policy`
compute logging-only outcome metrics through masked/current-tiled wrapped envs
without changing actor inputs, rewards, dynamics, termination behavior, profile
configs, seeds, or scenario specs.

## Evidence

Before the fix, focused tests reproduced the M1753 failure:

```text
2 failed
AttributeError: 'ControllerProfileObservationWrapper' object has no attribute 'config'
```

After the fix:

```text
2 passed
```

The repaired path is covered by:

- `test_profile_runtime_wrapper_exposes_base_env_config`
- `test_wrapped_env_episode_outcome_metrics_use_base_config`

## Change

`ControllerProfileObservationWrapper.config` now returns the wrapped base env
config:

```text
wrapped.config is wrapped.env.config
```

This is a wrapper/evaluator compatibility fix only. Observation masking behavior
is unchanged.

## Validation

Focused red/green tests:

```text
2 passed
```

Affected tests:

```text
37 passed
```

Full test suite:

```text
1709 passed, 4 warnings
```

Compile check:

```text
python -m compileall -q src tests
```

Research validation:

```text
passed
```

## Guardrails

- full rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Admit M1756 revised execution rerun using the same M1753 protocol and seed base,
writing to a fresh output directory. The single M1753 sampling failure remains
unrepaired and should be re-evaluated after the wrapper issue is removed.
