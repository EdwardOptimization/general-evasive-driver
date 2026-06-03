# Current Status

This file is the compact official state for the project. Milestone documents
and `docs/research-log.md` remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Current Research Blocker

Latest completed milestone:

```text
m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight
```

Latest attempted milestone:

```text
m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight
result: completed
```

Current next task:

```text
m2483-high-fidelity-interface-source-only-fixture-smoke-design
```

Current route:

```text
M2482 materialized a checked HF0 fixture catalog from the M2481 fixture design.
The catalog keeps current-sim limited rows diagnostic/reference only and admits
three source-only four-wheel limited rows for a bounded fixture smoke design.
```

The materialization preserves P0 observation shape `72`, action shape `3`, and the rule
that scenario labels, feasibility classes, hidden dynamics, per-wheel forces,
fault scales, TTC, required clearance, reward terms, and success labels remain
metadata-only.

M2482 did not install, import, or run an external high-fidelity simulator. It
did not run measured validation, policy evaluation, training, replay, PPO,
controller ranking, winner selection, or any paper/FW-vs-GRU/self-ID/current-
sim/high-fidelity validation verdict.

The active next task is M2483: design a bounded source-only fixture smoke
protocol for the three admitted M2482 rows. M2483 must preserve observation
shape `72`, action shape `3`, and metadata-only role labels. It must not
install, import, or run external high-fidelity simulation, train, rank
controllers, select winners, or make validation/paper verdict claims.

## Latest Evidence

M2471 remains the active route pivot after the post-M2470 synthesis:

```text
decision:
  freeze current-sim as a diagnostic/mining layer
  stop direct static current-sim materialization as the immediate route
  start high-fidelity interface preparation now
```

Current-sim scenario-readiness evidence remains useful but not driver
capability evidence:

```text
M2468 reset-only attempts: 120
M2468 reset successes: 109
stable_aes_support: 14/24
stable-AES failures: 10/11 total reset failures
partial stable-AES cells:
  broad threshold-free: 5/8
  threshold-band: 3/8
  low-mu near: 6/8
```

HF0 interface evidence now consists of:

```text
M2472:
  design: DynamicsBackend boundary and P0 extractor contract

M2473:
  result_class: hf0_contract_preflight_pass
  reset observation shape: 72
  step observation shape: 72
  action shape: 3
  actor/action contract changed: false
  hidden/oracle diagnostics enter actor input: false

M2474:
  result_class: current_sim_adapter_smoke_pass
  backend: current_sim_autodrift_hf0
  seed count: 3
  bounded reset count: 3
  bounded step count: 6
  observation/action shape: 72 / 3
  max extractor parity error: 5.960464477539063e-08
  actor/action contract changed: false
  hidden/oracle diagnostics enter actor input: false

M2475:
  decision: external_backend_route_to_dependency_api_audit
  primary direction: open auditable high-fidelity backend route
  fallback direction: source-only four-wheel adapter preflight
  external simulation installed/imported/executed: false

M2476:
  decision: conditional_external_backend_route_to_branch_synthesis
  local pychrono/projectchrono package: absent
  Chrono route: plausible but conditional
  next route: branch synthesis before source-only adapter preflight
  external simulation installed/imported/executed: false

M2477:
  synthesis decision: continue
  decision: continue_to_source_only_four_wheel_adapter_preflight
  process-overhead risk: high
  supported driver/paper evidence: none
  next executable route: source-only FourWheelDriftModel HF0 adapter preflight
  external simulation installed/imported/executed: false

M2478:
  result_class: source_only_four_wheel_adapter_preflight_pass
  backend: source_only_four_wheel_hf0
  model: FourWheelDriftModel
  reset/step count: 1 / 2
  observation/action shape: 72 / 3
  wheel forces and fault scales: diagnostics only
  external simulation installed/imported/executed: false

M2479:
  decision: scenario_taxonomy_mapping_route_to_materialization_preflight
  roles: stable_avoidable stable_aes drift_required_recovery hidden_dynamics_robustness unavoidable_mitigation
  role labels and feasibility classes: metadata only
  next route: materialized surface role matrix
  external simulation installed/imported/executed: false

M2480:
  result_class: hf0_scenario_taxonomy_mapping_materialization_pass
  matrix rows: 10
  surfaces: current_sim_autodrift_hf0 source_only_four_wheel_hf0
  support statuses: supported 5 limited_fixture 5 blocked 0
  observation/action shape: 72 / 3
  role labels and feasibility classes enter actor input: false
  next route: bounded fixture design for limited rows
  external simulation installed/imported/executed: false

M2481:
  decision: scenario_taxonomy_fixture_design_route_to_materialization_preflight
  limited rows covered: 5
  current-sim limited rows: diagnostic/reference only
  source-only four-wheel limited rows: admitted for fixture catalog materialization
  observation/action shape: 72 / 3
  role labels feasibility classes hidden diagnostics and oracle verdicts: metadata only
  next route: checked fixture catalog materialization
  external simulation installed/imported/executed: false

M2482:
  result_class: hf0_scenario_taxonomy_fixture_materialization_pass
  catalog rows: 10
  fixture admission statuses: baseline_reference 5 diagnostic_reference_only 2 admitted_for_materialization 3
  limited rows silently upgraded: false
  current-sim limited references: 2
  source-only admitted fixtures: 3
  observation/action shape: 72 / 3
  role labels feasibility classes hidden diagnostics and oracle verdicts: metadata only
  next route: source-only fixture smoke design
  external simulation installed/imported/executed: false
```

## Current Interpretation Boundary

Allowed claim:

```text
The HF0 interface boundary has checked local contract primitives, a current-sim
adapter smoke, a bounded external-backend route design, a dependency/API audit,
branch synthesis, source-only four-wheel adapter preflight, and scenario
taxonomy mapping design/materialization. These preserve the canonical P0
actor/action contract and keep diagnostics outside actor input. M2481 also
designs fixture admissions for limited rows, and M2482 materializes a checked
fixture catalog, but these do not prove driver capability.
```

Blocked claims:

```text
high-fidelity validation readiness
driver performance improvement
current-sim benchmark readiness
controller-family ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign success
training repair success
```

## Immediate Next Step

M2483 should design bounded source-only fixture smoke from:

```text
docs/post-m2470-route-plan.md
docs/m2472-high-fidelity-interface-hf0-design.md
docs/m2477-high-fidelity-interface-preparation-branch-synthesis.md
docs/m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight.md
runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json
docs/m2479-high-fidelity-interface-scenario-taxonomy-mapping-design.md
runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json
runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv
docs/m2481-high-fidelity-interface-scenario-taxonomy-fixture-design.md
runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json
runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv
```

The smoke design must cover the three source-only `admitted_for_materialization`
rows while preserving observation shape `72`, action shape `3`, explicit
metadata-only labels, and no validation/ranking/winner claims. It must not
install, import, or run external high-fidelity simulation, execute policy
rollout, train, replay, use PPO, rank controllers, select a winner, or claim
high-fidelity validation, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, or level-3 self-identification.
