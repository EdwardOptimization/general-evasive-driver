# M1830 Executable V2 Reset-Time AES Sampler Diagnostic Design

- status: completed
- decision: `reset_time_aes_sampler_diagnostic_design_admit_implementation`
- branch: `paper_route_executable_v2_reset_time_aes_sampler_diagnostic`
- reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1829 pivoted away from broad repaired reset reruns because M1828 showed a
specific mismatch:

```text
M1825 offline repair planner accepted AES candidates
M1828 reset-time sampler still failed 24/24 AES rows
M1828 AEB sparse source passed 12/12 rows
```

M1830 designs a diagnostic that can explain that mismatch before any further
source repair.

## Diagnostic Targets

Target only the two persistent AES failure sources:

| target | source | label | hidden bucket | timing/lateral bucket | M1828 result |
| --- | --- | --- | --- | --- | --- |
| `aes_nominal_medium_center` | `m1811-stable-bp-000` / `m1771-bp1-00` | `aes_feasible` | `nominal` | `medium/center` | 0/12 reset success |
| `aes_friction_late_center` | `m1811-stable-bp-001` / `m1771-bp1-02` | `aes_feasible` | `friction_step` | `late/center` | 0/12 reset success |

The diagnostic should use:

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

## Required Comparators

The diagnostic must compare the M1825 no-reset repair proxy against the actual
reset-time sampler path.

### Offline Proxy

Reuse or reproduce the M1823/M1825 density logic:

```text
label_density(
  speed grid,
  mu grid,
  obstacle distance grid,
  obstacle half-width grid,
  classify_obstacle_scenario(...)
)
```

Record the selected repair candidate, candidate ranges, attempt budget, and
offline density.

### Reset-Time Attempt Replay

For each target source/profile group, reproduce the reset-time obstacle sampler
conditions closely enough to expose rejection reasons:

```text
sample_vehicle_params(...)
sample speed_ref
sample initial beta / reset pose order when needed
sample obstacle distance / half-width attempts
classify_obstacle_scenario(speed_ref, params.mu, distance, half_width, config)
apply allowed_labels
apply require_aeb_infeasible
apply max_threshold_score
apply min_time_after_friction_step / obstacle-aligned friction-step gate
```

The tool may instantiate `AutoDriftEnv` only in a reset-only diagnostic mode in
later execution. M1830 itself does not run reset.

## Required Output Tables

The implementation should write:

```text
summary.json
aes_source_diagnostic_targets.csv
offline_density_rows.csv
reset_time_attempt_summary.csv
reset_time_reject_reason_counts.csv
reset_time_label_counts.csv
reset_time_candidate_examples.csv
claim_boundary.csv
```

Minimum columns:

```text
target_id
v2_panel_spec_id
profile_name
source_v1_bounded_panel_spec_id
source_scenario_spec_id
hidden_dynamics_bucket
repair_candidate
attempt_budget
speed_ref
initial_mu
distance_range
half_width_range
attempt_count
label_counts
accepted_count
reject_allowed_label_count
reject_aeb_feasible_count
reject_threshold_count
reject_friction_timing_count
offline_density
reset_time_density
dominant_reject_reason
```

Candidate examples should include a small bounded sample of rejected and
accepted attempts with:

```text
speed_ref
initial_mu
obstacle_distance
obstacle_half_width
label
threshold_score
time_to_obstacle
time_after_friction_step
accepted
reject_reason
```

## Expected Failure Explanations

The diagnostic should be able to distinguish at least these cases:

1. `no_aes_label_mass`: reset-time sampled candidates rarely or never classify
   as `aes_feasible`.
2. `aeb_gate_dominates`: candidates that would otherwise be acceptable are
   mostly `aeb_feasible` and rejected by `require_aeb_infeasible`.
3. `threshold_filter_dominates`: `max_threshold_score` removes otherwise valid
   candidates.
4. `friction_timing_filter_dominates`: friction-step timing constraints remove
   otherwise valid candidates.
5. `offline_reset_mu_mismatch`: M1825 density used a different effective `mu`
   distribution than reset-time classification.
6. `offline_reset_speed_mismatch`: M1825 density used a different effective
   speed distribution than reset-time classification.
7. `attempt_budget_insufficient`: valid candidates exist but are too sparse for
   the configured attempt budget.

## Implementation Route

Route to:

```text
m1831-executable-v2-reset-time-aes-sampler-diagnostic-implementation
```

M1831 should implement the diagnostic helper with focused tests only. It should
not run project artifacts or additional reset preflights. After implementation,
a later execution-design milestone can decide whether to run the diagnostic on
M1825/M1828 artifacts.

## Guardrails

- environment reset started: `false`
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

- reset-time AES sampler diagnostic design;
- implementation route and expected artifacts.

Unsupported:

- reset-time diagnostic result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
