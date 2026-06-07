# M3072 Active Safety Driver v1 Direct-Action Multi-Failure Repair Contract Result Audit

## Summary

- status: completed
- decision: `accept_m3071_repair_contract_claim_safe_route_to_m3073_bounded_repair_fitting_preflight`
- audited milestone: `m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight`
- M3071 status/gate matrix: True / True
- measurement rows preserved: 32/32
- repair contract rows: 1
- loss family rows: 6
- row admission rows: 32
- guard family rows: 9
- claim boundary rows: 23
- requirement families preserved: 7
- success/collision/offtrack/speed-too-low: 8 / 4 / 16 / 5
- actor/action contract: obs72 to action3 `[steer, throttle, brake]`
- runtime base policy required: False

## Audit Finding

M3072 accepts M3071 as complete and claim-safe repair-contract materialization. The accepted evidence is limited to artifact completeness, row preservation, requirement-family preservation, actor-contract preservation, and claim-boundary preservation.

M3072 does not interpret M3071 as target quality, fitted policy quality, validation, ranking, promotion, repair success, driver performance, current-sim verdict, high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

Accepted artifacts:

```text
summary.json
direct_action_repair_contract_rows.csv
direct_action_loss_family_rows.csv
direct_action_row_admission_rows.csv
direct_action_guard_family_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m3071-...
```

Rejected shortcuts:

```text
rollout, fitting, training, validation, ranking, promotion, checkpoint mutation, profile tuning, performance verdict, repair-success claim, target-quality claim, self-ID claim
```

## Next Route

M3072 selects exactly one continuation route:

```text
m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-preflight
```

The route is admitted only as a bounded offline fit-or-fail-closed preflight. It must preserve obs72/action3 direct-action semantics, keep target labels and provenance actor-invisible, forbid hidden oracle/TTC inputs, avoid runtime base-policy dependency, and register a result audit before any rollout, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID claim.

Follow-up manifest:

```text
experiments/manifests/m3073-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-bounded-fitting-preflight.json
```
