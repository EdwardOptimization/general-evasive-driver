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
m2495-engineering-controller-source-only-role-fixture-parameterization-design
```

Latest attempted milestone:

```text
m2495-engineering-controller-source-only-role-fixture-parameterization-design
result: completed
```

Current next task:

```text
m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight
```

Current route:

```text
M2495 designs the source-only role fixture parameterization contract after
M2494 classified identical role metrics as a fixture differentiation blocker.
The next task should implement reset-only differentiated role fixtures and
verify reset observations/state/obstacle/fault digests differ before rerunning
any role metric panel.
```

The materialization preserves P0 observation shape `72`, action shape `3`, and the rule
that scenario labels, feasibility classes, hidden dynamics, per-wheel forces,
fault scales, TTC, required clearance, reward terms, and success labels remain
metadata-only.

M2495 did not install, import, or run an external high-fidelity simulator. It
did not run policy action, measured validation, training, replay, PPO,
controller ranking, winner selection, success-rate computation, or any paper/
FW-vs-GRU/self-ID/current-sim/high-fidelity validation verdict.

The active next task is M2496: implement the reset-only source-only role
fixture parameterization preflight. It must not execute policy actions, train,
rank, select a winner, compute success-rate verdicts, or claim performance or
validation.

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

M2483:
  decision: source_only_fixture_smoke_design_route_to_implementation_preflight
  admitted source-only rows: stable_aes drift_required_recovery unavoidable_mitigation
  smoke protocol: one reset and two canned actions per admitted row
  observation/action shape: 72 / 3
  actions are adapter smoke only, not policy performance
  role labels feasibility classes fixture labels hidden diagnostics and oracle verdicts: metadata only
  next route: source-only fixture smoke implementation preflight
  external simulation installed/imported/executed: false

M2484:
  result_class: hf0_source_only_fixture_smoke_pass
  admitted source-only fixtures: 3
  resets/steps: 3 / 6
  observation/action shape: 72 / 3
  diagnostic wheel force counts: 4 4 4 4 4 4
  canned actions only: true
  policy action: false
  fixture labels scenario labels feasibility classes hidden values oracle labels enter actor input: false
  next route: source-only fixture smoke result audit
  external simulation installed/imported/executed: false

M2485:
  decision: accept_source_only_fixture_smoke_route_to_branch_synthesis
  accepted evidence: M2484 smoke pass fixtures 3 resets 3 steps 6 obs 72 action 3
  rejected claims: driver performance policy rollout training ranking winner validation paper FW-vs-GRU self-ID
  route: branch synthesis before another interface milestone
  external simulation installed/imported/executed: false

M2486:
  synthesis decision: promote_to_next_branch
  decision: promote_to_source_only_closed_loop_fixture_pilot_branch
  accepted evidence: HF0 interface branch is ready-enough infrastructure for bounded pilot design
  rejected claims: driver performance policy rollout training ranking winner validation paper FW-vs-GRU self-ID
  route: close high_fidelity_interface_preparation and open source_only_closed_loop_fixture_pilot
  external simulation installed/imported/executed: false

M2487:
  decision: source_only_closed_loop_fixture_pilot_design_route_to_implementation_preflight
  actor admission candidate: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  pilot scope: 3 admitted source-only fixtures
  planned horizon: 20 deterministic policy-action steps per fixture
  route: implementation preflight with summary and pilot_rollout_rows artifacts
  external simulation installed/imported/executed: false

M2488:
  result_class: source_only_closed_loop_fixture_pilot_pass
  checkpoint_admitted: true
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  fixtures/resets/steps: 3 / 3 / 60
  all actions finite and within bounds: true
  all actor-input leak flags: false
  policy_action and policy_rollout_run: true
  route: result audit before longer pilot or claim escalation
  external simulation installed/imported/executed: false

M2489:
  decision: accept_source_only_policy_action_path_smoke_route_to_extended_execution
  audited rows: 60
  role counts: stable_aes 20 drift_required_recovery 20 unavoidable_mitigation 20
  row gates: observation 72 action 3 finite bounded running wheel_count_4
  accepted scope: source-only policy-action path smoke
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: 100-step-per-fixture extended execution
  external simulation installed/imported/executed: false

M2490:
  result_class: source_only_closed_loop_fixture_pilot_pass
  checkpoint_admitted: true
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  fixtures/resets/steps: 3 / 3 / 300
  role counts: stable_aes 100 drift_required_recovery 100 unavoidable_mitigation 100
  all actions finite and within bounds: true
  all actor-input leak flags: false
  policy_action and policy_rollout_run: true
  route: extended result audit before route escalation
  external simulation installed/imported/executed: false

M2491:
  decision: accept_extended_source_only_policy_action_execution_route_to_branch_synthesis
  audited rows: 300
  row gates: observation 72 action 3 finite bounded running wheel_count_4
  accepted scope: extended source-only policy-action execution
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: branch synthesis before another extension or route escalation
  external simulation installed/imported/executed: false

M2492:
  synthesis decision: promote_to_next_branch
  decision: promote_to_engineering_controller_source_only_metric_panel
  accepted evidence: source-only closed-loop path live with 60-row path smoke and 300-row extended execution
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: engineering source-only role metric panel before any claim escalation
  external simulation installed/imported/executed: false

M2493:
  result_class: engineering_controller_source_only_role_metric_panel_pass
  telemetry rows: 300
  role metric panel rows: 3
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  role counts: stable_aes 100 drift_required_recovery 100 unavoidable_mitigation 100
  row gates: observation 72 action 3 finite bounded running wheel_count_4
  nonverdict gates: success_rate_computed false verdict_claim_made false ranking_run false winner_selected false
  key finding: all three role panels are numerically identical so source-only role fixtures remain metadata-only for dynamics
  route: result audit before fixture differentiation repair or claim escalation
  external simulation installed/imported/executed: false

M2494:
  decision: accept_panel_path_identical_roles_route_to_fixture_parameterization_design
  accepted evidence: M2493 telemetry infrastructure and nonverdict panel path pass
  blocker: role metric values are identical across all three roles
  classification: source_only_role_fixture_differentiation_blocker
  rejected claims: role-specific performance equal role capability validation ranking paper FW-vs-GRU self-ID
  route: source-only role fixture parameterization design
  external simulation installed/imported/executed: false

M2495:
  decision: source_only_role_fixture_parameterization_design_route_to_implementation_preflight
  design contract: SourceOnlyRoleFixtureDynamicsSpec
  allowed variation: initial state road obstacle fault scales diagnostics
  actor contract: preserve P0 observation 72 and action 3
  implementation gate: reset-only role differentiation with pairwise reset observation L2 min greater than 1e-3
  policy action: false
  route: M2496 reset-only implementation preflight
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
fixture catalog. M2483 designs and M2484 executes a bounded source-only fixture
smoke protocol. M2485 audits that smoke and explicitly rejects performance
overclaims. M2486 closes the HF0 interface branch and promotes to a bounded
source-only closed-loop pilot design. M2487 defines the same-contract actor
admission and source-only pilot implementation preflight. M2488 runs that
bounded policy-action path smoke. M2489 audits and accepts it with the same
claim boundary. M2490 extends it to 100 steps per fixture, and M2491 audits and
accepts those rows. M2492 promotes the branch to an engineering telemetry panel.
M2493 implements that panel and exposes that source-only role fixture dynamics
are not yet differentiated. M2494 audits that finding and routes to fixture
parameterization design. M2495 defines that parameterization contract and keeps
the next step reset-only. These do not prove driver capability.
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

M2496 should implement source-only role fixture parameterization from:

```text
docs/m2495-engineering-controller-source-only-role-fixture-parameterization-design.md
experiments/manifests/m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight.json
src/autodrift/four_wheel_hf0_adapter.py
```

The implementation should add exactly three differentiated source-only role
fixture specs and run reset-only preflight artifacts. It must preserve the
actor/input contract and must not install, import, or run external high-fidelity
simulation, execute policy actions, train, replay, use PPO, rank controllers,
select a winner, promote a checkpoint, compute success-rate verdicts, or claim
high-fidelity validation, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, or level-3 self-identification.
