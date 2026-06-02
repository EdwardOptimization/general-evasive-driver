# M2354 Paper-Route Current-Sim Dual-Axis Candidate Pack Reset Validation Result Audit

- status: completed
- decision: `candidate_pack_reset_failure_audit_route_to_sampling_compatible_repair_design`
- manifest: `experiments/manifests/m2354-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-result-audit.json`
- audited result: `docs/m2353-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-implementation.md`
- summary: `runs/m2353_paper_route_current_sim_dual_axis_candidate_pack_reset_validation/summary.json`
- reset/rollout/policy action in M2354: `false`
- measured execution in M2354: `false`
- training/replay/PPO in M2354: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Audited Result

M2353 runs the frozen reset-only validation over the five M2350 candidate packs
and fails closed:

```text
result_class: current_sim_dual_axis_candidate_pack_reset_validation_fail
reset_attempt_count: 360
reset_success_count: 328
reset_failure_count: 32
contract_violation_count: 0
forbidden_key_violation_count: 0
metadata_caveat_rows_preserved: true
metadata_only_patch_count: 37
unresolved_patch_count: 0
guardrail_violation_count: 0
```

The failure is not caused by actor contract, forbidden keys, active config
overwrite, metadata caveat loss, rollout, policy action, ranking, or guardrail
violation.

## Failure Distribution

Pack outcomes:

```text
baseline_reference_pack: 72 / 72 success, 0 failure
g_primary_pack: 63 / 72 success, 9 failures
h_primary_pack: 71 / 72 success, 1 failure
g_h_primary_pack: 62 / 72 success, 10 failures
gh_minimal_pack: 60 / 72 success, 12 failures
```

Failure type:

```text
RuntimeError: 32
message: failed to sample an obstacle scenario matching the configured filters
```

Failure scenarios:

```text
m2277_r2_02: 3
m2277_r2_05: 3
m2277_r2_08: 3
m2277_r3_02: 3
m2277_r3_05: 3
m2277_r3_11: 3
m2277_r5_01: 3
m2277_r5_09: 3
m2277_r5_10: 3
m2277_r5_11: 3
m2277_r5_06: 1
m2277_r5_07: 1
```

Artifact-only join to M2350 patch/candidate rows:

```text
missing_patch_join: 0
missing_candidate_selection_join: 0
```

Failure by candidate axis:

```text
G: 18
GH: 11
H: 3
```

Failure by transform:

```text
timing_step_earlier: 18
timing_step_earlier+low_mu_step_toward_nominal: 3
timing_step_earlier+slow_steer_actuator_step_toward_nominal: 3
timing_step_earlier+tire_stiffness_step_toward_nominal: 2
timing_step_earlier+weak_brake_step_toward_nominal: 1
low_mu_step_toward_nominal: 3
lateral_offset_step_toward_centerline+weak_brake_step_toward_nominal: 1
lateral_offset_step_toward_centerline+slow_steer_actuator_step_toward_nominal: 1
```

Failure by timing transform:

```text
late_close -> mid: 27
early_far -> early_far: 3
mid -> mid: 2
```

Failure by patch resolution:

```text
env_config_patch: 26
mixed_env_and_metadata: 6
```

## Classification

Primary failure:

```text
scenario_sampling_failure
```

More specific subtype:

```text
sampling_incompatible_candidate_transform
```

Reason:

```text
baseline_reference_pack resets 72/72;
all failure rows join to known M2350 patch/candidate rows;
27/32 failures include late_close -> mid timing transforms;
G or GH transforms explain 29/32 failures;
metadata caveat preservation and human-view contract are clean.
```

This means the next repair should focus on sampling-compatible candidate-pack
generation, especially the G-axis timing transform, before another reset run.

## Supported Claims

M2354 supports:

- M2353 produced valid reset-validation artifacts.
- M2353 failure is a task-quality candidate-pack reset blocker.
- The baseline reference pack is reset-valid under this validator.
- M2350 metadata caveat reporting survives M2353.
- Candidate packs cannot proceed to measured execution or controller
  comparison.

## Unsupported Claims

M2354 blocks:

- all five M2350 candidate packs are reset-valid;
- scenario redesign has been executed;
- support-policy ranking;
- controller-family comparison readiness;
- winner selection;
- finite-window vs GRU comparison;
- level3 self-identification evidence;
- paper-level current-sim result.

## Next Route

Decision:

```text
route_to_sampling_compatible_candidate_pack_repair_design
```

Next milestone:

```text
m2355-paper-route-current-sim-dual-axis-candidate-pack-sampling-compatible-repair-design
```

M2355 should design a bounded no-reset repair route that keeps the five-pack
discipline while making candidate transforms sampler-compatible. It should at
least address:

```text
1. late_close -> mid timing transforms that create 27/32 reset failures;
2. low_mu nominal-neighbor H-only rows that create 3 failures;
3. two mid/mid lateral+hidden GH rows;
4. preservation of metadata caveat reporting;
5. no measured rollout, controller ranking, paper, finite-window-vs-GRU, or
   self-ID claim.
```

M2355 should not repair and run reset in the same milestone. The next reset run
must wait until a repaired pack materialization exists and is separately
pre-registered.

## Follow-Up Manifest

```text
experiments/manifests/m2355-paper-route-current-sim-dual-axis-candidate-pack-sampling-compatible-repair-design.json
```
