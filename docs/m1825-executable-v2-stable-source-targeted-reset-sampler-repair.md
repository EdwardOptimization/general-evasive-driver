# M1825 Executable V2 Stable Source Targeted Reset Sampler Repair

- status: completed
- decision: `stable_source_targeted_reset_sampler_repair_pass_route_to_result_audit`
- source result: `runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/summary.json`
- no-reset repair planner run: `true`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Result Summary

M1825 ran the M1824 pre-registered no-reset source-level sampler repair planner
over the M1816 targeted reset payload and M1820 reset rows.

```text
result_class=targeted_reset_sampler_repair_planner_pass
input_spec_count=36
input_reset_row_count=36
repair_target_source_count=3
systematic_source_count=2
sparse_source_count=1
profile_control_count=12
repaired_executable_spec_count=36
reset_ready_spec_count=36
labels_enter_actor_input_count=0
ranking_admissible_by_default_count=0
guardrail_violation_count=0
```

No environment reset, rollout, policy action, measured execution, training,
replay, PPO, ranking, private holdout, paper-level, or level3 self-ID claim was
made.

## Repair Targets

The planner found the same three source-level repair targets identified by
M1821/M1822:

| repair target | source key | label | class | attempted profiles | reset successes | sampling failures |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `repair-000` | `m1811-stable-bp-000` | `aes_feasible` | `systematic` | 12 | 0 | 12 |
| `repair-001` | `m1811-stable-bp-001` | `aes_feasible` | `systematic` | 12 | 0 | 12 |
| `repair-002` | `m1811-stable-bp-002` | `aeb_feasible` | `sparse` | 12 | 10 | 2 |

The repaired payload preserves all 12 profile controls for each source target,
so the output remains a 36-row executable-v2 reset-validation candidate.

## Representative Repairs

Representative repaired rows show source-level sampler changes only:

```text
m1811-stable-bp-000::L0_current_masked
  label=aes_feasible
  repair_class=systematic
  candidate=aes_medium_band
  density=0.0035555555555555557
  max_sample_attempts=10000

m1811-stable-bp-001::L0_current_masked
  label=aes_feasible
  repair_class=systematic
  candidate=original_attempts
  density=0.043555555555555556
  max_sample_attempts=10000

m1811-stable-bp-002::L0_current_masked
  label=aeb_feasible
  repair_class=sparse
  candidate=aeb_wide_search_band
  density=0.5511111111111111
  max_sample_attempts=5000
```

Labels remain metadata-only and do not enter actor input. Controller-family
ranking remains blocked by default.

## Output Artifacts

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/summary.json
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/source_sampler_repair_targets.csv
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/source_sampler_repair_specs.json
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/source_sampler_repair_specs.csv
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/source_sampler_repair_matrix.csv
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/source_sampler_repair_claim_boundary.csv
```

## Follow-Up

Route to:

```text
m1826-executable-v2-stable-source-targeted-reset-sampler-repair-result-audit
```

M1826 should audit the M1825 repaired payload and decide whether to design a
reset-only preflight over:

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
```

M1826 must not run reset.

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

- source-level sampler repair planner execution passed;
- repaired 36-row targeted reset payload exists;
- labels remain outside actor input;
- profile controls remain preserved;
- ranking remains blocked.

Unsupported:

- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
