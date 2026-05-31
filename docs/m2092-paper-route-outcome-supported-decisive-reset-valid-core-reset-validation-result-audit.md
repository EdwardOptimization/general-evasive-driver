# M2092 Paper-Route Outcome-Supported Decisive Reset-Valid Core Reset Validation Result Audit and Synthesis

- status: completed
- decision: `pivot_to_public_gate_core_panel_extraction_design`
- synthesis decision: `pivot`
- audited artifact: `runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- reset/rollout/measured execution in M2092: `false`
- policy actions executed in M2092: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

The branch tried to preserve broad generated coverage, but fresh reset seeds
kept exposing public-debug scenario sampling fragility:

```text
M2085 full density-aware panel: 238/240 reset success
M2088 reduced materialized panel: 238 rows from M2085 reset-success rows
M2091 reduced fresh reset validation: 236/238 reset success
```

The stable signal is that the public-gate subset repeatedly passes:

```text
M2085 public-gate reset failures: 0/96
M2091 public-gate reset failures: 0/96
```

M2091 preserved the important boundaries:

```text
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started/replay_started/ppo_used: false
```

## M2091 Failure Audit

M2091 failed closed with:

```text
reset_attempt_count: 238
reset_success_count: 236
reset_failure_count: 2
observation_finite_count: 236
obstacle_initialized_count: 236
observation_dimension_failure_count: 0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
dynamics_quota_pass: true
source_kind_quota_pass: true
```

Both failures are public-debug generated rows:

```text
m2063-osd-osd_v0_0070_t2
m2063-osd-osd_v0_0129_t3
```

Shared failure slice:

```text
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
dynamics_band: mixed_mu
initial_speed_band: low
```

Interpretation:

```text
The 238-row reduced panel is still not fresh-seed stable.
The public-gate subset is the only currently demonstrated reset-stable core.
```

## Supported Claims

Supported:

```text
The reduced-panel branch preserved contract, metadata, and guardrails.
All 96 public-gate rows reset successfully under both M2085 and M2091.
Public-debug generated rows remain seed-fragile under fresh reset validation.
No policy-action or driver-performance claim has been made.
```

## Falsified Claims

Falsified:

```text
The 240-row generated panel is fresh reset-valid.
The 238-row reset-success-derived reduced panel is fresh reset-valid.
Continuing to preserve public-debug rows is the right near-term route to measured execution.
```

Not tested:

```text
controller-family ranking;
finite-window vs GRU;
closed-loop self-identification;
paper-level benchmark claims.
```

## Failure Taxonomy Summary

Current active failure taxonomy:

```text
scenario_sampling_failure
seed_fragility
```

Operational subtype:

```text
public-debug generated-row reset-sampling fragility
```

This is not a contract violation, metric artifact, training instability, or
behavior regression. No controller behavior has been measured in this branch.

## Public Gate Overfit Risk

Risk is medium.

The public-gate subset passing twice is useful, but it is still a public
generated panel, not private holdout or paper-valid task semantics. The correct
use is a bounded smoke/research panel for measured execution, with explicit
claim limits.

Mitigation:

```text
Extract a public-gate-only core panel.
Do not claim paper-level validity.
Do not include public-debug rows in measured execution until a redesigned distribution exists.
Run measured execution only after the public-gate panel is materialized and audited.
```

## Next Branch Decision

Decision:

```text
pivot
```

Selected next route:

```text
M2093 public-gate core panel extraction design
```

The design should:

```text
include only source_split == public_gate rows from the M2091 reset-success set;
target exactly 96 executable specs;
preserve env_config and metadata exactly;
not repair filters;
not rerun reset;
write a planned sentinel workload;
block measured execution until materialization and audit.
```

Rejected routes:

```text
another local obstacle-filter repair:
  rejected because the branch has repeated reset-validity repair without stabilizing public-debug rows.

direct measured execution on the 238-row panel:
  rejected because M2091 reset success is 236/238.

scenario-distribution redesign immediately:
  deferred because the public-gate subset is already reset-stable enough to support a bounded smoke measured panel.
```

## Next

Next milestone:

```text
m2093-paper-route-outcome-supported-decisive-public-gate-core-panel-extraction-design
```
