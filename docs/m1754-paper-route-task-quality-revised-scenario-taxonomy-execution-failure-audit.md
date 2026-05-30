# M1754 Paper-Route Task-Quality Revised Scenario Taxonomy Execution Failure Audit

- status: completed
- decision: `failure_audit_route_to_wrapper_config_proxy_repair`
- audited execution: `docs/m1753-paper-route-task-quality-revised-scenario-taxonomy-measured-execution.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1754 audits the failed M1753 revised public diagnostic execution. The failure
is dominated by a deterministic wrapper/evaluator plumbing issue, not by policy
behavior or the revised outcome metrics.

The next step should repair the controller-profile observation wrapper so it
proxies `env.config`. The single reset-time sampling failure should be preserved
as a known secondary issue and re-checked after the dominant wrapper failure is
removed.

## Failure Classification

M1753 summary:

```text
episode_count: 504
target_episode_count: 864
failure_count: 360
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

Dominant failure:

```text
AttributeError: 359
message: 'ControllerProfileObservationWrapper' object has no attribute 'config'
```

Affected profiles:

```text
L0_current_masked: 72
L2_window_100_current_tiled: 72
L2_window_25_current_tiled: 72
L2_window_50_current_tiled: 72
L2_window_13_current_tiled: 71
```

The root cause is clear: `run_episode_with_policy` computes outcome metrics
from `env.config`, but `ControllerProfileObservationWrapper` does not expose
that attribute. Unmasked profiles use the base `AutoDriftEnv` directly and
therefore do not hit this error.

Secondary failure:

```text
RuntimeError: 1
message: failed to sample an obstacle scenario matching the configured filters
workload_id: m1728-s4-02::L2_window_13_current_tiled
```

This should not be repaired in the same step as the wrapper bug. After the
wrapper fix, rerunning the same execution protocol will reveal whether the
sampling failure persists.

## Interpretation Boundary

The `504` completed rows are not valid controller-family evidence because five
profile families failed systematically. They may only be used to verify that
completed rows were metric-complete and guardrail-clean.

Unsupported from M1753:

- execution pass;
- controller-family ranking;
- profile comparison;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Repair Route

Admit M1755 wrapper config proxy repair:

- add a `config` proxy property to `ControllerProfileObservationWrapper`;
- add focused tests that a wrapped masked env exposes the same config as the
  base env;
- add a focused test that `run_episode_with_policy` can compute outcome metrics
  through a wrapped env;
- do not change actor inputs, rewards, dynamics, termination behavior, profile
  configs, seeds, or scenario specs;
- do not rerun the 864-cell execution inside the repair milestone.

After M1755 is audited, rerun the same M1753 execution protocol unchanged. Only
then decide whether the remaining sampling failure requires a separate sampling
repair.

## Guardrails

- full rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Route to M1755 wrapper config proxy repair before any revised execution rerun.
