# m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight Research Review

## Summary

- Generated at UTC: 20260603T075549Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: hf0_source_only_fixture_smoke_pass_route_to_result_audit
- Decision reason: M2484 source-only fixture smoke pass fixtures 3 resets 3 steps 6 obs 72 action 3 wheel force diagnostics 4 each fixture labels metadata-only no simulation training ranking winner verdict claims

## Hypothesis

The admitted source-only fixture rows can be smoke-tested through FourWheelHF0Backend while preserving actor/action contracts and keeping fixture labels diagnostics-only.

## Lineage

- parent_checkpoint: not_applicable_source_only_fixture_smoke_preflight
- parent_dataset: docs/m2483-high-fidelity-interface-source-only-fixture-smoke-design.md, runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json, runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv, docs/m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight.md, docs/m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight.md
- parent_config: experiments/manifests/m2483-high-fidelity-interface-source-only-fixture-smoke-design.json
- parent_objective: implement bounded source-only fixture smoke preflight without actor input leakage
- derived_from: m2483-high-fidelity-interface-source-only-fixture-smoke-design, m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight, m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight
- blocked_by: source-only fixture smoke protocol is designed but not executable, admitted source-only fixture rows need an adapter smoke before pilot design, fixture metadata and diagnostic four-wheel state must remain outside actor input
- supersedes: manual source-only fixture smoke inspection, direct pilot design without bounded source-only fixture smoke
- invalidates: None

## Success Criteria

- src/autodrift/hf0_source_only_fixture_smoke.py exists
- tests/test_hf0_source_only_fixture_smoke.py exists and focused tests pass
- runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/summary.json exists
- runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/fixture_smoke_rows.csv exists
- summary reports all admitted source-only fixture rows smoked
- summary reports observation_shape 72 and action_shape 3 preserved for all reset and step observations/actions
- summary reports scenario_labels_enter_actor_input false feasibility_classes_enter_actor_input false and fixture_labels_enter_actor_input false
- no external high-fidelity simulation install import execution training ranking winner or verdict claim is made

## Failure Criteria

- M2484 installs imports or runs Chrono or another external simulator
- M2484 changes actor input or action contract
- M2484 injects hidden or oracle actor features
- M2484 treats canned actions as policy performance
- M2484 ranks controller families or selects a winner
- M2484 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2484 must execute a bounded source-only fixture smoke over admitted M2482 source-only rows
- M2484 must preserve P0 observation shape 72 and action shape 3 for every reset and step
- M2484 must keep scenario labels feasibility classes fixture labels hidden dynamics wheel forces and oracle verdicts out of actor input
- M2484 must generate summary JSON and fixture_smoke_rows CSV
- M2484 must not install import or run external high-fidelity simulation
- M2484 must not train rank controllers select winners or make paper self-ID finite-window-vs-GRU current-sim or high-fidelity validation claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not run measured validation
- do not run policy rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not rank controller families
- do not select a winner
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight
- type: infrastructure
- checkpoint: runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hf0_source_only_fixture_smoke_pass_route_to_result_audit
- reason: M2484 source-only fixture smoke pass fixtures 3 resets 3 steps 6 obs 72 action 3 wheel force diagnostics 4 each fixture labels metadata-only no simulation training ranking winner verdict claims

## Next Blocker

m2484-high-fidelity-interface-source-only-fixture-smoke-implementation-preflight
