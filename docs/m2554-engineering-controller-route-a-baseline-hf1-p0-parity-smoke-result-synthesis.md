# M2554 Engineering Controller Route A Baseline HF1 P0 Parity Smoke Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf2_scenario_taxonomy_mapping_design`
- manifest: `experiments/manifests/m2554-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-result-synthesis.json`
- parent audit: `docs/m2553-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-result-audit.md`
- parent materialization summary: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json`
- supporting taxonomy source: `runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json`
- supporting fixture source: `runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2555-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-design.json`
- next: `m2555-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-design`

## Evidence Summary

M2552/M2553 provide accepted source-level HF1 parity-smoke evidence:

```text
HF1 actor-visible field parity rows: 7/7 pass
P0 index coverage: 72/72
observation value-range checks: 5/5 pass
action mapping checks: 7/7 pass
external-backend boundary checks: 6/6 pass
diagnostics-exclusion checks: 33/33 pass
materialization gates: 8/8 pass
actor contract: P0 observation 72 / action 3
external high-fidelity simulation: not installed/imported/run
```

M2480/M2482 provide older taxonomy support artifacts that can be reused as
source material, not as current Route A evidence:

```text
M2480 surface-role matrix: 2 surfaces, 5 roles, 10 rows
M2480 support status: 5 supported, 5 limited_fixture
M2482 fixture catalog: 10 rows
M2482 admitted source-only fixtures: 3
M2482 current-sim limited references: 2
actor contract preserved: 72/3
scenario and feasibility labels: metadata-only
```

This is enough to continue to HF2 scenario taxonomy mapping design. It is not
enough to run a high-fidelity pilot or claim validation readiness.

## Supported Claims

Supported:

- the Route A HF1 P0 parity-smoke interface is internally consistent
- P0 actor-visible coverage is complete at `72/72`
- action mapping and diagnostics-exclusion boundaries are accepted
- external-backend checks remain boundary-only with no external runtime
- existing M2480/M2482 taxonomy material can seed a Route A HF2 mapping design
- the next bounded step should design a Route A/HF1-bound HF2 taxonomy mapping
  materialization

## Falsified Claims

Not supported, and explicitly rejected:

- high-fidelity validation readiness or result
- external simulator behavior transfer
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2480/M2482 also cannot be treated as current Route A/HF1 evidence without a
new mapping step because they predate M2552/M2553 and were framed as HF0
infrastructure.

## Failure Taxonomy Summary

No accepted M2552/M2553 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: the earlier mitigation-primary proof issue remains
  unresolved and is outside the HF1 interface branch.
- `objective_overfit`: HF1 parity-smoke and older taxonomy rows must not be
  used as ranking, validation, or public-gate tuning evidence.
- `scenario_sampling_failure`: not triggered here, but HF2 must avoid silently
  upgrading limited fixture roles into pilot-ready roles.

## Public Gate Overfit Risk

Risk is medium. HF1 parity-smoke rows are contract/infrastructure checks, not
public behavior rows, so the direct public-gate tuning risk is limited. The
risk increases if the branch overclaims `72/72` P0 coverage or M2480/M2482
taxonomy metadata as validation readiness.

The next step should therefore be a bounded HF2 mapping design that:

- reuses M2480/M2482 only as source material
- marks role support honestly as supported, limited, blocked, or reference
- keeps scenario labels and feasibility classes metadata-only
- prevents HF3 pilot admission until HF2 materialization and audit pass

## Next Branch Decision

Continue to:

```text
m2555-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-design
```

M2555 should design M2556 materialization artifacts for Route A HF2 scenario
taxonomy mapping:

- Route C role-family mapping across stable avoidable/AEB-feasible,
  stable-AES/AEB-infeasible, drift-required recovery, hidden-dynamics
  robustness, and unavoidable mitigation
- surface/fixture bindings from M2480/M2482, explicitly re-audited under
  M2552/M2553 HF1 boundaries
- metadata-only label and feasibility checks
- pilot-admission guard rows that prevent limited/reference roles from being
  promoted to HF3 pilots without materialized support
- a gate matrix that preserves P0 `72/3`, no hidden/oracle actor inputs, and no
  validation or driver-performance claims

M2555 must not install/import/run external high-fidelity simulation, execute
policy rollouts, train, rank, promote, compute success rates, or claim
validation.
