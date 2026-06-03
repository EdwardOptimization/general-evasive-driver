# m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260603T072609Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: hf0_scenario_taxonomy_mapping_materialization_pass_route_to_fixture_design
- Decision reason: M2480 materializes 10-row HF0 surface-role matrix across 2 surfaces and 5 roles preserving obs 72 action 3 with labels metadata-only no simulation training ranking winner verdict claims

## Hypothesis

A materialized HF0 surface role matrix can represent current-sim and source-only four-wheel scenario taxonomy while preserving actor/action contracts and keeping labels metadata-only.

## Lineage

- parent_checkpoint: not_applicable_scenario_taxonomy_mapping_materialization_preflight
- parent_dataset: docs/m2479-high-fidelity-interface-scenario-taxonomy-mapping-design.md, docs/m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight.md, runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json, docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md, docs/observation-contract.md
- parent_config: experiments/manifests/m2479-high-fidelity-interface-scenario-taxonomy-mapping-design.json
- parent_objective: materialize HF0 scenario taxonomy mapping across adapter surfaces without actor input leakage
- derived_from: m2479-high-fidelity-interface-scenario-taxonomy-mapping-design, m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight
- blocked_by: scenario taxonomy mapping is designed but not materialized into a checked artifact, surface role support status must be machine-readable before pilot or fixture work, scenario labels and feasibility classes must remain metadata-only
- supersedes: manual scenario-role mapping inspection, direct validation pilot before checked taxonomy artifact
- invalidates: None

## Success Criteria

- src/autodrift/hf0_scenario_taxonomy_mapping.py exists
- tests/test_hf0_scenario_taxonomy_mapping.py exists and focused tests pass
- runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json exists
- runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/surface_role_matrix.csv exists
- summary reports current-sim and source-only four-wheel surfaces represented
- summary reports observation_shape 72 and action_shape 3 preserved for all rows
- summary reports scenario_labels_enter_actor_input false and feasibility_classes_enter_actor_input false
- no external high-fidelity simulation install import execution training ranking winner or verdict claim is made

## Failure Criteria

- M2480 installs imports or runs Chrono or another external simulator
- M2480 changes actor input or action contract
- M2480 injects hidden or oracle actor features
- M2480 ranks controller families or selects a winner
- M2480 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2480 must generate a machine-readable HF0 surface role matrix
- M2480 must include current-sim and source-only four-wheel HF0 surfaces
- M2480 must preserve P0 observation shape 72 and action shape 3 in every row
- M2480 must prove scenario role labels and feasibility classes are metadata-only
- M2480 must not install import or run external high-fidelity simulation
- M2480 must not train rank controllers select winners or make paper self-ID finite-window-vs-GRU current-sim or high-fidelity validation claims

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

- milestone: m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight
- type: infrastructure
- checkpoint: runs/m2480_high_fidelity_interface_scenario_taxonomy_mapping_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hf0_scenario_taxonomy_mapping_materialization_pass_route_to_fixture_design
- reason: M2480 materializes 10-row HF0 surface-role matrix across 2 surfaces and 5 roles preserving obs 72 action 3 with labels metadata-only no simulation training ranking winner verdict claims

## Next Blocker

m2480-high-fidelity-interface-scenario-taxonomy-mapping-materialization-preflight
