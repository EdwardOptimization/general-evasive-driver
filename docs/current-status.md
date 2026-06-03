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
m2513-engineering-controller-behavior-outcome-protocol-design
```

Latest attempted milestone:

```text
m2513-engineering-controller-behavior-outcome-protocol-design
result: completed
```

Current next task:

```text
m2514-engineering-controller-behavior-outcome-protocol-materialization-preflight
```

Current route:

```text
M2513 designs the Route A engineering-controller behavior/outcome protocol.
The protocol separates source-only diagnostics, current-sim diagnostic/mining,
and future high-fidelity validation layers; defines admissible metric families,
forbidden metric shortcuts, row schema, and audit gates; and preserves the
bounded claim boundary. The active next task is no-rollout materialization of
the protocol as schema and registry artifacts before any measured behavior,
ranking, success-rate, validation, or performance claim.
```

The Route A artifact set preserves P0 observation shape `72`, action shape `3`,
and the rule that scenario labels, feasibility classes, hidden dynamics,
per-wheel forces, fault scales, TTC, required clearance, reward terms, and
success labels remain metadata-only.

M2513 did not install, import, or run an external high-fidelity simulator. It
did not step a simulator, execute policy rollouts, run measured validation,
training, replay, PPO, controller ranking, winner selection, success-rate
computation, or any driver-performance, paper/FW-vs-GRU/self-ID/current-sim/
high-fidelity validation verdict.

The active next task is M2514: materialize the behavior/outcome protocol as
machine-readable no-rollout artifacts. It must not step an environment, execute
policy rollouts, train, rank, select a winner, compute success-rate verdicts,
or claim performance or validation.

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

M2496:
  result_class: source_only_role_fixture_parameterization_preflight_pass
  specs/resets: 3 / 3
  reset observation shapes: 72 72 72
  action shape: 3
  unique initial state/fault/road/obstacle/reset observation digests: 3 / 3 / 3 / 3 / 3
  pairwise reset observation L2 min: 0.3037872612476349
  policy action and rollout: false / false
  actor-input leak flags: false
  route: result audit before differentiated role metric panel rerun
  external simulation installed/imported/executed: false

M2497:
  decision: accept_reset_only_fixture_parameterization_route_to_differentiated_role_metric_panel
  accepted evidence: M2496 reset-only differentiated source-only fixtures
  accepted scope: fixture differentiation infrastructure only
  rejected claims: behavior performance success-rate validation ranking paper FW-vs-GRU self-ID
  route: parameterized source-only nonverdict role metric panel rerun
  external simulation installed/imported/executed: false

M2498:
  result_class: engineering_controller_parameterized_source_only_role_metric_panel_pass
  parameterized fixtures: true
  telemetry rows / role panel rows: 300 / 3
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  role reset digests unique: 3
  row gates: observation 72 action 3 finite bounded running wheel_count_4
  role metric status: nonidentical diagnostic-only rows
  max abs y by role: stable_aes 8.874552706111096 drift_required_recovery 9.186174406522152 unavoidable_mitigation 4.35557577943488
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: result audit before comparison repair synthesis or claim escalation
  external simulation installed/imported/executed: false

M2499:
  decision: accept_parameterized_role_metric_panel_route_to_baseline_comparison_design
  accepted evidence: M2498 parameterized source-only diagnostic telemetry
  accepted scope: differentiated source-only engineering diagnostics only
  rejected claims: behavior performance success-rate validation ranking paper FW-vs-GRU self-ID
  route: source-only baseline comparison protocol design
  new policy action: false
  external simulation installed/imported/executed: false

M2500:
  decision: source_only_baseline_comparison_design_route_to_implementation_preflight
  comparison subjects: m1154_policy_actor coast_open_loop straight_full_brake_open_loop
  roles: stable_aes drift_required_recovery unavoidable_mitigation
  expected implementation rows: 900 telemetry rows / 9 role-subject panel rows
  action mapping: coast [0,-1,-1] straight full brake [0,-1,1]
  required gates: reset digests match within role and differ across roles, obs/action 72/3, finite bounded actions, diagnostic-only rows
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: implementation preflight before result audit
  policy action in M2500: false
  external simulation installed/imported/executed: false

M2501:
  result_class: engineering_controller_source_only_baseline_comparison_preflight_pass
  comparison subjects: m1154_policy_actor coast_open_loop straight_full_brake_open_loop
  roles: stable_aes drift_required_recovery unavoidable_mitigation
  telemetry rows / role-subject panel rows: 900 / 9
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  reset digest gates: match within role across subjects and differ across roles
  row gates: observation 72 action 3 finite bounded running wheel_count_4 diagnostic-only
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: result audit before repair synthesis or claim escalation
  external simulation installed/imported/executed: false

M2502:
  decision: accept_source_only_baseline_comparison_route_to_branch_synthesis
  accepted evidence: M2501 diagnostic comparison artifacts
  accepted scope: source-only engineering diagnostics only
  rejected claims: behavior performance success-rate validation ranking paper FW-vs-GRU self-ID
  route: branch synthesis before another metric artifact or claim escalation
  new policy action: false
  external simulation installed/imported/executed: false

M2503:
  synthesis decision: promote_to_next_branch
  decision: promote_to_engineering_controller_public_benchmark_pack
  evidence window: M2493-M2502
  supported scope: source-only engineering diagnostic telemetry package
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  public-gate overfit risk: medium
  route: public benchmark pack design
  new policy action: false
  external simulation installed/imported/executed: false

M2504:
  decision: public_benchmark_pack_design_route_to_materialization_preflight
  pack scope: source-only engineering diagnostics
  required files: README artifact_manifest claim_boundary actor_contract checkpoint_lineage scenario_role_diagnostics baseline_comparison_diagnostics known_limitations reproduce summary
  required contract: P0 observation 72 action 3 no hidden/oracle actor input
  rejected claims: performance validation ranking paper FW-vs-GRU self-ID
  route: materialization preflight before result audit
  policy action in M2504: false
  external simulation installed/imported/executed: false

M2505:
  result_class: engineering_controller_public_benchmark_pack_materialization_preflight_pass
  pack directory: public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505
  required files present: true
  artifact manifest rows: 14
  source artifacts exist: true
  missing source artifacts: []
  actor contract: P0 observation 72 action 3 actor_encoder human_view_online_gru horizon 1
  claim boundary rejects: performance success-rate ranking winner validation paper FW-vs-GRU self-ID
  summary claim flags false: policy_action training replay PPO ranking winner success-rate verdict performance paper validation
  route: result audit before public export or route escalation
  policy action in M2505: false
  external simulation installed/imported/executed: false

M2506:
  decision: accept_public_benchmark_pack_route_to_branch_synthesis
  audited pack: public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505
  accepted gates: required files present source artifacts exist missing source artifacts [] actor contract 72/3 claim boundary false flags
  accepted scope: source-only public engineering diagnostic artifact
  rejected claims: performance success-rate ranking winner validation paper FW-vs-GRU self-ID
  route: branch synthesis before public export or route escalation
  new policy action in M2506: false
  external simulation installed/imported/executed: false

M2507:
  synthesis decision: promote_to_next_branch
  decision: promote_to_engineering_controller_runtime_inference_cost_report
  evidence window: M2504-M2506
  supported scope: bounded public source-only diagnostic pack is complete enough for later export review
  rejected claims: performance success-rate ranking winner validation paper FW-vs-GRU self-ID
  public-gate overfit risk: medium-low
  route: runtime/inference-cost report preflight
  new policy action in M2507: false
  external simulation installed/imported/executed: false

M2508:
  result_class: engineering_controller_runtime_inference_cost_report_pass
  timed path: recurrent_features_tensor_plus_actor_mean_tanh
  synthetic observation source: seeded_normal_shape_only
  device: cpu
  batch sizes: 1 8 32
  measured rows: 300
  checkpoint contract: obs/action/encoder/horizon 72 / 3 / human_view_online_gru / 1
  model parameter count: 164679
  p50 forward time: batch1 42.13us batch8 76.355us batch32 124.291us
  accepted scope: actor-only runtime/inference cost
  rejected claims: performance success-rate ranking winner validation paper FW-vs-GRU self-ID
  environment rollout in M2508: false
  external simulation installed/imported/executed: false

M2509:
  decision: accept_runtime_inference_cost_report_route_to_known_failure_taxonomy
  audited summary: runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json
  audited runtime rows: 300 data rows
  accepted scope: actor-only runtime/inference cost
  rejected claims: performance controller quality environment throughput simulator throughput ranking validation paper FW-vs-GRU self-ID
  route: known failure taxonomy materialization preflight
  environment rollout in M2509: false
  external simulation installed/imported/executed: false

M2510:
  result_class: engineering_controller_known_failure_taxonomy_materialization_pass
  taxonomy rows: 10
  failure categories: 9
  severity counts: high 4 medium 5 low 1
  source artifacts exist: true
  actor contract: 72/3
  accepted scope: structured known limitations and route implications
  rejected claims: performance success-rate ranking winner validation paper FW-vs-GRU self-ID
  environment rollout in M2510: false
  external simulation installed/imported/executed: false

M2511:
  decision: accept_known_failure_taxonomy_route_to_route_a_artifact_synthesis
  audited taxonomy rows: 10
  audited categories: 9
  accepted scope: structured known limitations and route implications
  rejected claims: performance behavior verdict success-rate ranking winner validation paper FW-vs-GRU self-ID
  route: Route A artifact-set branch synthesis
  environment rollout in M2511: false
  external simulation installed/imported/executed: false

M2512:
  synthesis decision: promote_to_next_branch
  decision: promote_to_engineering_controller_behavior_outcome_protocol
  evidence window: M2493-M2511
  supported scope: coherent Route A engineering artifacts under a bounded claim boundary
  public pack evidence: required files present artifact manifest rows 14 source references actor contract 72/3 claim flags false
  runtime evidence: actor-only timing rows 300 batch sizes 1/8/32 params 164679 synthetic shape-only observation scope
  taxonomy evidence: 10 rows 9 categories source references forbidden interpretations false claim flags
  rejected claims: performance behavior verdict success-rate ranking winner validation paper FW-vs-GRU self-ID
  public-gate overfit risk: medium
  route: behavior/outcome protocol design before measured behavior or validation claims
  environment rollout in M2512: false
  external simulation installed/imported/executed: false

M2513:
  decision: behavior_outcome_protocol_design_admit_no_rollout_materialization_preflight
  design scope: evaluator-side engineering behavior/outcome protocol only
  actor contract: P0 observation 72 action 3 human_view_online_gru horizon 1
  protocol layers: source_only_diagnostic current_sim_diagnostic_mining future_high_fidelity_validation
  scenario roles: stable_avoidable stable_aes drift_required_recovery hidden_dynamics_robustness unavoidable_mitigation
  admissible metric families: contract episode status avoidance/boundary response/recovery actuator/smoothness mitigation metadata/completeness
  row schema: protocol layer surface role subject checkpoint actor contract episode status outcome metrics completeness flags claim scope forbidden interpretation source artifact
  audit gates: actor contract row schema metric registry forbidden registry layer separation claim boundary denominator completeness
  rejected claims: performance behavior verdict success-rate ranking winner validation paper FW-vs-GRU self-ID
  route: no-rollout behavior/outcome protocol materialization preflight
  environment rollout in M2513: false
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
the next step reset-only. M2496 implements that reset-only differentiation.
M2497 audits and accepts the reset-only differentiation. These do not prove
driver capability. M2498 reruns the nonverdict role metric panel on the
differentiated fixtures, producing role telemetry that is now interpretable as
source-only engineering diagnostics but still not performance evidence. M2499
audits and accepts that boundary, then routes to baseline comparison protocol
design rather than direct ranking or verdict claims. M2500 defines that
protocol and keeps the next implementation preflight diagnostic-only. M2501
implements the diagnostic comparison artifact but still does not rank
controllers or prove driver performance. M2502 audits and accepts the artifact
only as engineering diagnostics, then routes to branch synthesis. M2503 closes
the source-only metric branch and promotes to public benchmark-pack design
instead of adding another local metric artifact. M2504 defines the benchmark
pack contract and preserves it as an engineering diagnostic artifact, not a
driver-performance benchmark. M2505 materializes that pack and checks required
files, source artifact references, actor contract, claim boundary, and false
claim flags without adding new performance evidence. M2506 audits and accepts
the pack as a public source-only diagnostic artifact, then routes to branch
synthesis instead of another packaging task. M2507 closes the public pack branch
and promotes to a runtime/inference-cost report route, because Route A still
needs deployability cost evidence and another packaging task would be local
process work. M2508 adds that deployability artifact by measuring actor-only
forward-pass cost without environment rollout or performance interpretation.
M2509 audits and accepts that runtime artifact, then routes to known failure
taxonomy because Route A still needs structured limitations before export or
claim escalation. M2510 materializes that taxonomy from existing M2498/M2501/
M2505/M2508 artifacts without new rollout or performance interpretation.
M2511 audits and accepts the taxonomy, then routes to Route A artifact-set
synthesis so the project does not continue static artifact work without a route
decision. M2512 closes the Route A artifact-set branch and promotes to
engineering-controller behavior/outcome protocol design because behavior
regression and outcome semantics remain the limiting unresolved gap. M2513
defines that evaluator-side protocol and routes to no-rollout materialization
before any measured behavior or validation execution.
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

M2514 should materialize the M2513 engineering-controller behavior/outcome
protocol as no-rollout schema and registry artifacts:

```text
docs/m2513-engineering-controller-behavior-outcome-protocol-design.md
docs/m2512-engineering-controller-route-a-artifact-set-branch-synthesis.md
docs/m2511-engineering-controller-known-failure-taxonomy-result-audit.md
runs/m2510_engineering_controller_known_failure_taxonomy/failure_taxonomy.csv
docs/observation-contract.md
docs/post-m2470-route-plan.md
```

The materialization should write:

```text
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/protocol_schema.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/audit_gate_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/layer_registry.csv
```

It must preserve actor contract `72/3`, layer separation, forbidden actor input
and forbidden outcome shortcut registries, false claim flags, and no-rollout
scope. It must not install, import, or run external high-fidelity simulation,
step a simulator, execute policy action, train, replay, use PPO, rank
controllers, select a winner, promote a checkpoint, compute success-rate
verdicts, or claim driver performance, high-fidelity validation, current-sim
verdict, paper-level evidence, finite-window-vs-GRU evidence, or level-3
self-identification.
