# M3036 Active Safety Driver v1 Baseline Contract Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m3035_baseline_contract_route_to_m3037_baseline_measurement_table_materialization`
- audited summary: `runs/m3035_engineering_controller_active_safety_driver_v1_baseline_contract_materialization_preflight/summary.json`
- audited doc: `docs/m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight.json`
- next: `m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight`

M3036 accepts M3035 as complete and claim-safe baseline-contract
materialization. It does not execute, train, validate, rank, promote, mutate
checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or
claim driver performance.

## Audited M3035 Evidence

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
baseline candidate rows: 2
benchmark role rows: 17
benchmark role nonzero rows: 17
metric contract rows: 31
metric rows available now: 25
metric rows requiring future instrumentation: 6
exclusion rule rows: 11
actor contract guard rows: 9
actor contract guard pass: true
claim boundary rows: 25
claim boundary pass: true
M3015 episode rows: 32
M3015 diagnostic success/collision/offtrack/speed-floor rows: 3 / 5 / 23 / 2
M3018 localization rows: 32
M3022 objective family rows: 4
M3032 target tensor rows: 29
M3032 zero-target success guards: 3
actor observation/action: 72/action 3
environment reset/step/rollout: false
training/validation/ranking/promotion/checkpoint mutation: false
driver-performance/current-sim/HF/FW-vs-GRU/paper/self-ID claims: false
```

The materialized contract separates:

```text
baseline candidates:
  route_a_candidate_m2655_mitigation_preserving
  route_a_parent_l3_online_gru

benchmark roles:
  ordinary_avoidance
  stable_aes
  aeb_infeasible_evasive_steering
  hidden_dynamics_robustness
  recovery_and_stability

metric families:
  safety
  clearance
  stability
  recovery
  actuation
  robustness
  runtime
  unavoidable_mitigation
```

## Supported Claims

Supported:

```text
M3035 materialized the Active Safety Driver v1 baseline contract.
M3035 preserved actor 72/action 3.
M3035 registered M3036 as the result-audit follow-up.
M3035 turned the M3034 design into machine-readable candidate, role, metric,
exclusion, actor-guard, claim-boundary, gate, summary, and doc artifacts.
M3035 preserved the M3015 32-row closed-loop denominator as input context.
M3035 preserved M3032 target tensors as offline target context only.
```

## Rejected Claims

Rejected:

```text
driver performance
validation result
current-sim verdict
high-fidelity validation readiness or result
repair success
checkpoint ranking
winner selection
checkpoint promotion
target tensor quality
residual fitting readiness
paper evidence
finite-window-vs-GRU conclusion
full active-safety driver completion
level3 self-identification
```

## Failure Taxonomy Summary

```text
contract_violation:
  not observed; actor guards pass and no forbidden actor labels are exposed.

lineage_invalid:
  not observed; M3035 reads M3034/M3015/M3018/M3022/M3032 artifacts and
  registers this M3036 audit.

metric_artifact:
  controlled; row counts and metric family counts are explicit, but no
  baseline aggregate table exists yet.

scenario_sampling_failure:
  not resolved by M3035; the next route must show the measurable denominator
  and role split before any training or architecture comparison.

behavior_regression:
  not measured by M3035.

objective_overfit:
  reduced; target tensors and self-ID proof rows are explicitly excluded from
  active-safety baseline verdicts.

proof_washout:
  controlled; self-ID remains auxiliary diagnostic evidence only.

seed_fragility:
  not measured by M3035.
```

## Public Gate Overfit Risk

Risk is medium. M3035 is a contract materializer, so it cannot overfit policy
behavior. The remaining risk is process-local: continuing with another pure
audit would delay the active-safety measurement table. M3036 therefore routes
directly to a baseline measurement table materialization milestone, not another
design-only gate.

## Next Branch Decision

Decision:

```text
accept_m3035_baseline_contract_route_to_m3037_baseline_measurement_table_materialization
```

Next milestone:

```text
m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight
```

M3037 must create the official Active Safety Driver v1 baseline measurement
tables from the accepted M3035 contract and the already executed M3015
closed-loop rows. It may record safety, clearance, stability, recovery,
actuation, role split, and candidate aggregate metrics. It must not rerun
environments, train, validate, rank, promote, select a winner, claim driver
performance, or use M3032 target tensors as closed-loop evidence.

## Boundary

M3036 does not:

```text
execute environments
train PPO or BC
validate
rank controllers
promote checkpoints
mutate checkpoints or configs
change actor inputs
claim driver performance
claim current-sim or high-fidelity verdict
claim finite-window-vs-GRU result
claim paper-level evidence
claim self-ID evidence
```
