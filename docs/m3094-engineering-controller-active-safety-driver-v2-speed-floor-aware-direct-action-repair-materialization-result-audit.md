# M3094 Active Safety Driver v2 Speed-Floor-Aware Repair Materialization Result Audit

## Audit Decision

- decision: `accept_m3093_materialization_route_to_m3095_full_fresh_measurement`
- audit status: `accepted`
- M3093 status_pass: `True`
- M3093 gate_matrix_pass: `True`
- required artifacts present: `True`
- policy id: `m3093_speed_floor_aware_balanced_direct_action_repair_v2`
- rule rows: `5`
- actor-input exclusion rows: `10`
- claim-boundary rows: `20`
- selected next action: `m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight`

## Evidence Summary

M3093 materialized a v2 speed-floor-aware balanced direct-action repair package selected by M3092. The artifacts preserve the actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3093 wrote a direct-action policy config, 5 rule rows, 10 actor-input exclusion rows, 20 claim-boundary rows, a gate matrix, a doc, and this M3094 follow-up manifest. The low-speed probe has positive throttle 0.3700000047683716, and the urgent-obstacle probe preserves positive braking 0.4399999976158142.

These probes and artifacts support only materialization completeness and contract safety. They do not show that the M3090 behavior blockers are repaired.

## Supported Claims

- M3093 is a complete and claim-safe v2 speed-floor-aware direct-action repair materialization artifact set.
- The v2 rule/config package preserves obs72-to-action3 direct `[steer, throttle, brake]` output.
- The package uses only actor-visible ego, road, obstacle, actuator, and previous-action features already within the obs72 contract.
- The package is admissible for a bounded full-fresh measurement preflight on the same fresh denominator.

## Rejected Claims

- M3093 is not a measurement result.
- M3093 is not a validation result.
- M3093 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3093 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- The low-speed and urgent-obstacle probes are contract probes only; they are not closed-loop behavior evidence.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action/base-policy-free and hidden-input gates pass.
- `lineage_invalid`: not observed; M3093 routes from M3092/M3091/M3090 and registers M3094.
- `metric_artifact`: not observed for materialization artifacts; summary, rule rows, exclusion rows, claim rows, gate rows, doc, and audit manifest exist.
- `scenario_sampling_failure`: not applicable to M3093 materialization; M3095 must measure on the complete 64-row denominator before any behavior interpretation.
- `behavior_regression`: not evaluated by M3093; no environment rollout was run.
- `objective_overfit`: active risk if rule probes are treated as repair success.
- `proof_washout`: active risk if self-ID/GRU/paper evidence is re-centered before direct-action safety blockers are measured.
- `seed_fragility`: unresolved; M3095 must preserve the full-fresh denominator and avoid post-hoc row selection.

## Public Gate Overfit Risk

Risk is medium. M3093 is a rule/config materialization with finite bounded probes, not a closed-loop test. The materialized v2 repair is plausible because it targets M3090's largest speed-too-low blocker while preserving urgent obstacle and road-corridor branches, but this remains unmeasured.

The next route must therefore run exactly one full-fresh measurement preflight before any validation, promotion, or repair-success claim.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight
```

M3095 should execute the v2 speed-floor-aware direct-action repair as the full obs72-to-action3 action source over the complete 64-row fresh denominator, compare against M3090 same-row behavior, and record collision, offtrack, speed-floor, clearance, stability, recovery, action-pressure, actor-contract, and claim-boundary artifacts.

M3095 must not claim validation, ranking, promotion, driver performance, current-sim verdict, high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence, full-driver completion, repair success, robustness result, or self-ID.

## Boundary

M3094 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
