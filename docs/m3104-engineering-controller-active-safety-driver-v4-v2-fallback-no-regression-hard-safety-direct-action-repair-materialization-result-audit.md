# M3104 Active Safety Driver v4 No-Regression Materialization Result Audit

## Audit Decision

- decision: `accept_m3103_materialization_route_to_m3105_full_fresh_measurement`
- audit status: `accepted`
- M3103 status_pass: `True`
- M3103 gate_matrix_pass: `True`
- required artifacts present: `True`
- rule rows: `5`
- no-regression guard rows: `4`
- actor-input exclusion rows: `10`
- claim-boundary rows: `21`
- selected next action: `m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight`

## Evidence Summary

M3103 materialized a v4 v2-fallback no-regression direct-action repair package after M3102 rejected continuing the M3100 v3 overlay as-is. The materialized package preserves the deployable actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3103 wrote:

```text
direct_action_policy_config.json
safety_reflex_rule_rows.csv
no_regression_guard_rows.csv
actor_input_exclusion_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
M3104 follow-up manifest
```

The no-regression guards explicitly cover M3095 speed-floor preservation and the two M3100 same-row regressions:

```text
m3100-same-row-comparison-0014
m3100-same-row-comparison-0048
```

Probe outputs are runtime-API checks only, not measurement:

```text
low_speed_probe_throttle: 0.3700000047683716
local_high_speed_obstacle_probe_brake: 0.5479999780654907
local_high_speed_edge_probe_brake: -0.46895238757133484
```

M3103 ran no environment reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

## Supported Claims

- M3103 is a complete and claim-safe v4 materialization artifact set for audit.
- The v4 materialization is based on the M3095/v2 fallback route and disables the M3100-style global high-speed throttle suppression pattern.
- The materialization includes explicit no-regression guard artifacts for the M3095 speed-floor surface and the two observed M3100 regression rows.
- The branch can move to a bounded full-fresh measurement preflight because materialization artifacts and claim boundaries are complete.

## Rejected Claims

- M3103 is not a measurement result.
- M3103 is not a validation result.
- M3103 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3103 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- No probe value proves collision/offtrack repair; M3105 must measure the full denominator before any behavior interpretation.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action/base-policy-free and hidden-input gates pass.
- `lineage_invalid`: not observed; M3103 routes from accepted M3102/M3100/M3095/M3093 artifacts and registers M3104.
- `metric_artifact`: not observed; summary, config, rule, no-regression, exclusion, claim, doc, and gate artifacts are present.
- `scenario_sampling_failure`: not applicable; M3103 is materialization-only and runs no denominator.
- `behavior_regression`: unresolved; materialization guards are present, but only M3105 measurement can test behavior.
- `objective_overfit`: active risk if no-regression guards become row-specific overfit rather than bounded actor-visible constraints.
- `proof_washout`: active risk if materialization completeness is mistaken for repair evidence.
- `seed_fragility`: unresolved; no broader validation should run before full-fresh measurement and audit.

## Public Gate Overfit Risk

Risk is medium. M3103 materializes explicit guards for known regressions, which is necessary after M3100, but those guards are still artifact-level constraints. The next route must measure the complete 64-row denominator and compare against M3095, M3100, and M3090 before any broader interpretation.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight
```

M3105 should execute the v4 direct-action repair over the complete M3084 denominator and write same-row comparison artifacts against M3095, M3100, and M3090. It must preserve obs72/action3 direct action, keep all hidden/oracle inputs forbidden, and make no validation, ranking, promotion, driver-performance, repair-success, current-sim verdict, high-fidelity, paper, full-driver, robustness-result, or self-ID claim.

## Boundary

M3104 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
