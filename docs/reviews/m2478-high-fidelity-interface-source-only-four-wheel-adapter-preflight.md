# m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight Research Review

## Summary

- Generated at UTC: 20260603T070819Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_only_four_wheel_adapter_preflight_pass_route_to_taxonomy_mapping
- Decision reason: M2478 exercises FourWheelDriftModel through HF0 reset 1 steps 2 obs 72 action 3 wheel forces diagnostic-only no external simulation training ranking winner verdict claims

## Hypothesis

A source-only FourWheelDriftModel adapter can exercise the HF0 ActorView and P0 extractor boundary while preserving action shape 3 and keeping four-wheel diagnostics out of actor input.

## Lineage

- parent_checkpoint: not_applicable_source_only_four_wheel_adapter_preflight
- parent_dataset: docs/m2477-high-fidelity-interface-preparation-branch-synthesis.md, docs/m2476-high-fidelity-interface-external-backend-dependency-api-audit.md, docs/m2475-high-fidelity-interface-external-backend-route-design.md, docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md, docs/m2472-high-fidelity-interface-hf0-design.md
- parent_config: experiments/manifests/m2477-high-fidelity-interface-preparation-branch-synthesis.json
- parent_objective: exercise a source-only four-wheel dynamics fallback through HF0 after branch synthesis
- derived_from: m2477-high-fidelity-interface-preparation-branch-synthesis, m2476-high-fidelity-interface-external-backend-dependency-api-audit
- blocked_by: external Chrono-family route remains conditional because pychrono/projectchrono is not installed locally, branch synthesis selected executable source-only adapter evidence as the next bounded step, source-only four-wheel model has not yet been exercised through HF0 ActorView and P0 extraction
- supersedes: direct Chrono adapter implementation without installed dependency, another high-fidelity interface design/audit milestone without executable adapter evidence
- invalidates: None

## Success Criteria

- source-only four-wheel HF0 adapter code exists
- focused tests pass
- runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json exists
- summary reports observation_shape 72 and action_shape 3
- summary reports actor_input_contract_changed false action_contract_changed false hidden_values_enter_actor_input false oracle_labels_enter_actor_input false
- no external high-fidelity simulation install import execution training ranking winner or verdict claim is made

## Failure Criteria

- M2478 installs imports or runs Chrono or another external simulator
- M2478 changes actor input or action contract
- M2478 injects hidden or oracle actor features
- M2478 ranks controller families or selects a winner
- M2478 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2478 must exercise FourWheelDriftModel through an HF0 DynamicsBackend-style adapter
- M2478 must preserve canonical P0 observation shape 72 and action shape 3
- M2478 must keep four-wheel hidden dynamics force slip load and fault values out of ActorView
- M2478 must generate a bounded summary artifact
- M2478 must not install import or run external high-fidelity simulation
- M2478 must not train rank controllers select winners or make paper self-ID finite-window-vs-GRU current-sim or high-fidelity validation claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not run measured validation
- do not run policy rollout beyond bounded adapter smoke steps
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

- milestone: m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight
- type: infrastructure
- checkpoint: runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_only_four_wheel_adapter_preflight_pass_route_to_taxonomy_mapping
- reason: M2478 exercises FourWheelDriftModel through HF0 reset 1 steps 2 obs 72 action 3 wheel forces diagnostic-only no external simulation training ranking winner verdict claims

## Next Blocker

m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight
