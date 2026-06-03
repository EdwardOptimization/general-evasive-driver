# m2474-high-fidelity-interface-current-sim-adapter-smoke Research Review

## Summary

- Generated at UTC: 20260603T063212Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_adapter_smoke_pass_route_to_external_backend_design
- Decision reason: M2474 exercises current-sim through HF0 backend 3 resets 6 bounded steps obs 72 action 3 parity max 5.96e-08 diagnostics separated no external simulation training ranking winner verdict claims

## Hypothesis

A bounded current-sim adapter smoke can exercise the HF0 DynamicsBackend boundary while preserving P0 observation shape 72, action shape 3, and diagnostics separation without external high-fidelity simulation.

## Lineage

- parent_checkpoint: not_applicable_current_sim_adapter_smoke
- parent_dataset: runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json, docs/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.md, docs/m2472-high-fidelity-interface-hf0-design.md, docs/observation-contract.md
- parent_config: experiments/manifests/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.json
- parent_objective: exercise the HF0 boundary through a bounded current-sim adapter smoke without external high-fidelity simulation
- derived_from: m2473-high-fidelity-interface-hf0-contract-implementation-preflight, m2472-high-fidelity-interface-hf0-design
- blocked_by: HF0 contract implementation exists but has not yet been exercised through a backend adapter, current-sim parity should be smoke-tested through the DynamicsBackend boundary before external backend work, diagnostics separation must remain checked when AutoDriftEnv is wrapped as a backend
- supersedes: direct external high-fidelity adapter implementation before current-sim adapter smoke, manual parity inspection without a backend wrapper
- invalidates: None

## Success Criteria

- current-sim adapter smoke code exists
- focused tests pass
- runs/m2474_high_fidelity_interface_current_sim_adapter_smoke/summary.json exists
- summary reports observation_shape 72 and action_shape 3 across the bounded seed set
- summary reports actor_input_contract_changed false action_contract_changed false hidden_values_enter_actor_input false oracle_labels_enter_actor_input false
- no external high-fidelity simulation training ranking winner or verdict claim is made

## Failure Criteria

- M2474 requires Chrono or another external high-fidelity simulator to run local tests
- M2474 changes actor input or action contract
- M2474 injects hidden or oracle actor features
- M2474 ranks controller families or selects a winner
- M2474 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2474 must exercise a current-sim adapter through the HF0 DynamicsBackend boundary
- M2474 must use a small bounded seed set and report reset and step counts
- M2474 must preserve canonical P0 observation shape 72 and action shape 3
- M2474 must preserve actor_input_contract_changed false and action_contract_changed false
- M2474 must prove hidden diagnostics and oracle labels are not read by actor observation extraction
- M2474 must not import or require external high-fidelity simulation
- M2474 must not train rank controllers select winners or make paper self-ID finite-window-vs-GRU current-sim or high-fidelity validation claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m2474-high-fidelity-interface-current-sim-adapter-smoke
- type: infrastructure
- checkpoint: runs/m2474_high_fidelity_interface_current_sim_adapter_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_adapter_smoke_pass_route_to_external_backend_design
- reason: M2474 exercises current-sim through HF0 backend 3 resets 6 bounded steps obs 72 action 3 parity max 5.96e-08 diagnostics separated no external simulation training ranking winner verdict claims

## Next Blocker

m2474-high-fidelity-interface-current-sim-adapter-smoke
