# M1821 Executable V2 Stable Source Targeted Reset Feasibility Result Audit

- status: completed
- decision: `stable_source_targeted_reset_failure_audit_route_to_sampler_repair_design`
- source result: `runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/summary.json`
- additional reset run: `false`
- rollout/training/replay/PPO: `false`

## Result Summary

M1820 is a clean negative targeted reset result:

```text
attempted_spec_count=36
reset_success_count=10
sampling_failure_count=26
guardrail_violation_count=0
```

No rollout, policy action, measured execution, training, replay, PPO, ranking,
paper-level, or level3 self-ID claim was made.

## Failure Distribution

Requested label distribution:

```text
aes_feasible: 24 failed / 24 attempted
aeb_feasible: 10 passed, 2 failed / 12 attempted
```

Hidden-bucket failure distribution:

```text
nominal: 12 failures
friction_step: 12 failures
brake_variation: 2 failures
```

Error class:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

This means:

- `m1811-stable-bp-000` / nominal / `aes_feasible` is systematic failure.
- `m1811-stable-bp-001` / friction_step / `aes_feasible` is systematic failure.
- `m1811-stable-bp-002` / brake_variation / `aeb_feasible` is sparse seed
  failure: 10 successful reset seeds, 2 failures.

## Adapter/Profile Merge Audit

The converted M1816 payload preserves the intended materialized obstacle
settings. Representative rows contain:

```text
m1811-stable-bp-000: allowed_labels=["aes_feasible"], require_aeb_infeasible=true, max_sample_attempts=1000
m1811-stable-bp-001: allowed_labels=["aes_feasible"], require_aeb_infeasible=true, max_sample_attempts=1000
m1811-stable-bp-002: allowed_labels=["aeb_feasible"], require_aeb_infeasible=false, max_sample_attempts=1000
```

The M1792 reset path uses `env_config_for_executable_profile`, which starts from
`executable_spec["env_config"]` and only applies profile-level history length
and observation-contract fields. It does not replace the obstacle sampler
configuration. Therefore the dominant failure is unlikely to be a profile merge
overwriting materialized obstacle config.

## Classification

Failure type:

```text
scenario_sampling_failure
```

Subclasses:

```text
systematic_aes_sampler_infeasibility: 24 rows
sparse_aeb_seed_sampling_failure: 2 rows
```

The M1811 materialization patch changed labels and `require_aeb_infeasible`, but
it kept the target source obstacle ranges. For the two `aes_feasible` source
specs, those ranges appear too restrictive to sample any matching scenario even
with `max_sample_attempts=1000`.

## Repair Route

Route to:

```text
m1822-executable-v2-stable-source-targeted-reset-sampler-repair-design
```

The repair should be source-level, not profile-specific. It should design a
no-reset repair plan for the materialized stable sources before rerunning reset:

- repair the two systematic `aes_feasible` materialized source configs by
  widening or reconstructing obstacle sampler ranges so `aes_feasible` can be
  sampled;
- handle the sparse `aeb_feasible` source as either a seed-fragility case or a
  modest sampler-attempt/range issue;
- preserve all 12 profile controls;
- keep labels metadata-only and outside actor input;
- keep measured execution and controller-family ranking blocked until targeted
  reset feasibility passes.

## Guardrails

- additional environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1820 reset failure is localized as sampling failure;
- `aes_feasible` failures are systematic for the two repaired AES sources;
- `aeb_feasible` failure is sparse over the tested seeds;
- source-level sampler repair design is the next step.

Unsupported:

- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
