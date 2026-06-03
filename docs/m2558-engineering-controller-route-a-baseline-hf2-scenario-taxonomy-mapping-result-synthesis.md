# M2558 Engineering Controller Route A Baseline HF2 Scenario Taxonomy Mapping Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_low_cost_pilot_design`
- manifest: `experiments/manifests/m2558-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-result-synthesis.json`
- parent audit: `docs/m2557-engineering-controller-route-a-baseline-hf2-scenario-taxonomy-mapping-materialization-result-audit.md`
- parent materialization summary: `runs/m2556_engineering_controller_route_a_hf2_scenario_taxonomy_mapping/summary.json`
- follow-up manifest: `experiments/manifests/m2559-engineering-controller-route-a-baseline-hf3-low-cost-pilot-design.json`
- next: `m2559-engineering-controller-route-a-baseline-hf3-low-cost-pilot-design`

## Evidence Summary

M2556/M2557 provide accepted source-level HF2 scenario taxonomy mapping
evidence:

```text
route-role rows: 5/5 pass
surface/fixture binding rows: 10/10 pass
metadata-boundary checks: 7/7 pass
pilot-admission guards: 5/5 pass
materialization gates: 7/7 pass
source support counts: supported=5, limited_fixture=5
binding counts: baseline_reference=5, diagnostic_reference=2, materialization_candidate=3
actor contract: P0 observation 72 / action 3
limited/reference upgrade: false
metadata label actor leakage: false
HF3 pilot admission claim: false
external high-fidelity simulation: not installed/imported/run
policy rollout/training/ranking/verdict: not run
```

This is enough to choose a bounded HF3 low-cost pilot design step. It is not
enough to admit a pilot, run a pilot, claim validation readiness, or rank
controller families.

## Supported Claims

Supported:

- Route A has a materialized HF2 taxonomy map across the five Route C role
  families
- the ten M2480/M2482 surface/fixture bindings are represented under the
  Route A/HF1 boundary
- support and fixture admission statuses are preserved without silent upgrade
- metadata labels, feasibility classes, and pilot-candidate status remain
  outside actor input
- P0 `72/3` actor/action contract remains unchanged
- the branch can proceed to a design-only HF3 low-cost pilot plan with explicit
  reset-feasibility and rollout-feasibility gates

## Falsified Claims

Not supported, and explicitly rejected:

- high-fidelity validation readiness or result
- HF3 pilot admission from taxonomy mapping alone
- external simulator behavior transfer
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

The accepted HF2 artifacts are maps and guards, not measured behavior.

## Failure Taxonomy Summary

No accepted M2556/M2557 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved and are not affected by taxonomy mapping.
- `objective_overfit`: taxonomy rows can be overclaimed as validation if the
  next step skips explicit feasibility gates.
- `scenario_sampling_failure`: not triggered yet, but HF3 design must prevent
  baseline/reference rows from being treated as executable pilots without
  reset and rollout feasibility checks.

## Public Gate Overfit Risk

Risk is medium. HF2 artifacts are source-level contract and taxonomy rows, so
they do not directly optimize public behavior rows. The risk is that role
labels or support statuses become a substitute for measured feasibility.

The next step must therefore design HF3 artifacts that:

- keep taxonomy labels metadata-only
- keep `baseline_reference`, `diagnostic_reference_only`, and
  `materialization_candidate` statuses explicit
- require reset feasibility before rollout feasibility
- require rollout feasibility before any controller-family verdict
- keep validation, ranking, driver-performance, paper, FW-vs-GRU, current-sim,
  and self-ID claims out of scope

## Next Branch Decision

Continue to:

```text
m2559-engineering-controller-route-a-baseline-hf3-low-cost-pilot-design
```

M2559 should design a bounded HF3 low-cost pilot materialization/preflight. It
should define:

- a candidate table for a stable avoidable/AEB-feasible pilot and a stable
  AES/AEB-infeasible pilot without granting pilot admission
- reset-feasibility preflight rows
- rollout-feasibility preflight rows
- external-backend boundary and no-install/no-run checks
- claim-boundary rows separating feasibility design from validation and driver
  performance
- an M2560 materialization gate matrix

M2559 must not install/import/run external high-fidelity simulation, execute
policy actions, step environments, train, rank, promote, compute success
rates, or claim validation.
