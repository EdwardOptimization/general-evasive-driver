# M3074 Active Safety Driver v1 Direct-Action Multi-Failure Repair Bounded Fitting Result Audit

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `accept_m3073_repair_fit_claim_safe_route_to_m3075_closed_loop_measurement_preflight`
- audited milestone: `m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-preflight`
- next route: `m3075-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-preflight`

M3074 accepts M3073 only as a complete and claim-safe offline direct-action
repair fitting artifact. It accepts artifact completeness, direct-action
candidate shape, actor-contract preservation, side-effect guards, and
claim-boundary preservation. It does not accept M3073 as target quality, fitted
policy quality, closed-loop repair success, validation result, ranking,
promotion, driver-performance verdict, current-sim verdict, high-fidelity
readiness, paper evidence, finite-window-vs-GRU evidence, full-driver
completion, or self-ID evidence.

## Synthesis Questions

### evidence_summary

Accepted M3073 facts:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
repair fitting dataset rows: 24
fit rows: 18
internal-accounting rows: 6
fit samples: 2128
all-accounting samples: 2692
masked recovery steps: 768
final repair fit weighted MSE: 0.00021525553328820269
M3065 parent fit weighted MSE: 0.0002183983045141296
all-repair accounting weighted MSE: 0.002601863211948731
final predicted action abs max: 1.0
candidate artifact: runs/m3073_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight/candidate_direct_action_repair_reflex_layer.npz
linear_weight: 72 x 3
linear_bias: 3
observation_dim: 72
action_dim: 3
action_low/action_high: [-1.0, -1.0, -1.0] / [1.0, 1.0, 1.0]
output_semantics: direct_action_clipped
output_components: steer; throttle; brake
runtime base policy required: false
```

M3073 also writes the required audit surfaces:

```text
repair_fitting_dataset_rows.csv: 24 rows
repair_split_rows.csv: 2 rows
repair_mask_weight_rows.csv: 24 rows
repair_loss_trace_rows.csv: 4 rows
repair_target_quality_boundary_rows.csv: 5 rows
repair_actor_input_exclusion_rows.csv: 16 rows
repair_checkpoint_side_effect_guard_rows.csv: 12 rows
claim_boundary_rows.csv: 15 rows
gate_matrix.csv: 22 rows
```

The actor-visible contract is preserved:

```text
input: observation vector shape 72
runtime base policy: none
raw action: obs72 @ linear_weight + linear_bias
final action: clip(raw action, action_low, action_high)
output: [steer throttle brake]
forbidden actor inputs: target/provenance/source/route/outcome/progress/verdict labels, hidden oracle values, TTC, and paper labels
```

M3073 is a useful fitting artifact because it produces one bounded repaired
candidate under the M3071 multi-failure contract. The loss numbers remain
offline trainer-side accounting. They are not evidence that closed-loop
collision, offtrack, clearance, stability, recovery, or robustness metrics have
improved.

### supported_claims

M3074 supports only these bounded claims:

```text
M3073 produced complete offline repair fitting artifacts
M3073 produced one obs72-to-action3 direct_action_clipped candidate artifact
M3073 candidate output remains [steer throttle brake]
M3073 does not require a runtime base policy
M3073 preserved target/provenance/TTC/oracle exclusion from actor inputs
M3073 did not mutate or promote parent checkpoints or parent candidate artifacts
M3073 preserved claim boundaries against validation, ranking, promotion, performance, repair-success, paper, finite-window-vs-GRU, full-driver, and self-ID claims
M3073 is admissible for a bounded same-denominator closed-loop measurement preflight
```

### falsified_claims

M3074 rejects these claims:

```text
offline repair fitting loss proves target quality
offline repair fitting loss proves fitted policy quality
M3073 repairs the M3067 closed-loop failure surface
M3073 is ready for ranking, winner selection, promotion, validation, or driver-performance verdict
M3073 establishes a current-sim verdict, high-fidelity readiness, paper result, finite-window-vs-GRU conclusion, full-driver completion, or level3 self-ID result
```

The all-accounting loss surface also prevents any shortcut comparison claim:
M3073 is close to the parent fit on the fit split, but that is still not a
closed-loop safety metric. M3075 must measure the repaired candidate on the
same denominator before any behavior interpretation.

### failure_taxonomy_summary

The M3073 evidence is contract-clean but behavior-unmeasured:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: active risk if offline fitting loss is reported as behavior quality
scenario_sampling_failure: unresolved because M3073 runs no closed-loop episodes
behavior_regression: unresolved until M3075 measures collision/offtrack/clearance/stability/recovery/robustness rows
objective_overfit: active risk because the fit objective is derived from a fixed repair contract
proof_washout: active risk if future reports hide unchanged or worsened collision/offtrack/speed-floor rows
seed_fragility: unresolved because M3073 is not a fresh or holdout measurement
```

The audit does not find an artifact blocker. The next scientific blocker is
closed-loop measurement under the preserved direct-action actor contract.

### public_gate_overfit_risk

Risk is medium. M3073 is fitted against the fixed M3061/M3071-derived artifact
surface and reports trainer-side losses. The repair candidate may simply match
the offline targets without improving collision, offtrack, clearance,
stability, recovery, or robustness. The next milestone must preserve the same
denominator used by M3067, report all row outcomes, and avoid ranking or
promotion.

### next_branch_decision

Decision:

```text
accept_m3073_repair_fit_claim_safe_route_to_m3075_closed_loop_measurement_preflight
```

M3075 should run a bounded same-denominator current-sim measurement preflight
for the M3073 repaired direct-action candidate as the full obs72-to-action3
actor. It must use the candidate directly:

```text
final_action = clip(obs72 @ linear_weight + linear_bias, action_low, action_high)
```

M3075 may write measurement episode rows, metric summary rows, direct-action
adapter guards, actor-contract guards, side-effect guards, claim-boundary rows,
gate rows, summary, doc, and an M3076 result-audit manifest. It must not
validate, rank, select a winner, promote, mutate checkpoints, tune the
denominator after seeing rows, or claim repair success, driver performance,
current-sim verdict, high-fidelity validation, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

## Boundary

M3074 does not run reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It only audits M3073, resets the repair branch
via workflow synthesis decision `continue`, and registers M3075.
