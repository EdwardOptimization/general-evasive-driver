# M3033 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target Tensor Materialization Result Audit

## Summary

- status: completed
- decision: `pivot_to_active_safety_driver_v1_baseline_freeze_design`
- synthesis decision: `pivot`
- audited summary: `runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight/summary.json`
- route plan: `docs/active-safety-driver-v1-route-plan.md`
- follow-up manifest: `experiments/manifests/m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design.json`
- next: `m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design`

M3033 accepts M3032 as complete and claim-safe target tensor materialization,
but rejects direct continuation into residual fitting, target quality,
training, validation, ranking, promotion, repair-success, driver-performance,
paper, current-sim verdict, high-fidelity validation, finite-window-vs-GRU,
full-driver, or self-ID claims.

The 2026-06-07 public ChatGPT share snapshot changes the route priority: the
project should now optimize for a usable actuator-level active-safety driver,
not for proving GRU self-ID or producing paper-first evidence. M3033 therefore
pivots the next milestone to Active Safety Driver v1 baseline freeze design.

## Audited M3032 Evidence

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
candidate target tensor rows: 29
success identity zero-target guard rows: 3
target tensor files: 32
target_action_delta_abs_max: 0.07999999821186066
target_loss_weight_sum: 2981.0
actor observation/action: 72/action 3
local-action search: false
environment step: false
fitting/training/validation/ranking/checkpoint mutation: false
driver-performance/paper/HF/FW-vs-GRU/full-driver/self-ID claims: false
```

M3032 target tensors are valid offline artifacts. They are not evidence that a
residual head will improve closed-loop active-safety behavior.

## Synthesis Questions

### evidence_summary

M3029-M3032 changed the artifact state from trace-backed target-source
feasibility to bounded numeric target tensor materialization:

```text
M3029: 29 target-source candidate rows and 3 success identity guards.
M3030: accepted M3029 as complete and claim-safe.
M3031: allowed one bounded target tensor materialization preflight.
M3032: materialized 29 bounded target tensor rows plus 3 zero-target guards.
```

This is useful infrastructure. It does not answer the engineering question:

```text
Can a deployable actuator-level driver reduce active-safety failures?
```

The public share review explicitly reframes the project objective as building
a usable active-safety reflex driver with `[steer, throttle, brake]` output,
while demoting GRU self-ID, finite-window evidence, horizon output, and
K-candidate heads to implementation candidates or diagnostics.

### supported_claims

Supported claims:

```text
M3032 target tensor artifacts are complete and claim-safe.
M3032 preserves actor 72/action 3.
M3032 keeps target labels and provenance actor-invisible.
M3032 keeps success identity guards as zero-target guards.
M3032 does not run search, environment stepping, fitting, training,
validation, ranking, or checkpoint mutation.
M3032 artifacts may remain offline training/materialization inputs for later
audited engineering experiments.
```

### falsified_claims

Rejected claims:

```text
target quality validated
residual fitting readiness
repair success
driver performance
current-sim verdict
paper evidence
high-fidelity validation readiness or result
finite-window-vs-GRU verdict
full active-safety driver completion
level3 self-identification
checkpoint ranking or promotion
controller/profile/candidate winner selection
```

### failure_taxonomy_summary

The active failure is not missing target tensors. The active process failure is
directional drift: the branch can keep generating clean artifacts without
forcing an engineering baseline, benchmark, or active-safety metric table.

Failure taxonomy:

```text
contract_violation: not observed in M3032.
metric_artifact: controlled; target tensor counts and gates are complete.
lineage_invalid: not observed; M3029-M3032 lineage is valid.
objective_overfit: risk remains if target tensors become another narrow fitting loop.
proof_washout: self-ID proof gates are not the mainline objective after pivot.
scenario_sampling_failure: still relevant to engineering benchmark freeze.
behavior_regression: not measured by M3032.
seed_fragility: not measured by M3032.
```

### public_gate_overfit_risk

Risk is medium. M3032 itself did not tune policy behavior or cherry-pick
controller winners, but direct continuation into fitting would keep the project
inside the same Route A repair surface. The share review indicates this is no
longer the right mainline: self-ID and paper evidence should not block an
engineering active-safety driver route.

### next_branch_decision

Decision:

```text
pivot_to_active_safety_driver_v1_baseline_freeze_design
```

Next milestone:

```text
m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design
```

M3034 should define Active Safety Driver v1 benchmark roles, candidate
baseline checkpoints, metric families, exclusion rules, guardrails, and stop
conditions before any training, architecture comparison, horizon/K-candidate
ablation, high-fidelity rollout, ranking, promotion, paper, or self-ID claim.

## Boundary

M3033 does not:

```text
fit residuals
train PPO or BC
run validation
rank controllers
promote checkpoints
change actor inputs
claim repair success
claim driver performance
claim current-sim or high-fidelity verdict
claim finite-window-vs-GRU result
claim self-ID evidence
```
