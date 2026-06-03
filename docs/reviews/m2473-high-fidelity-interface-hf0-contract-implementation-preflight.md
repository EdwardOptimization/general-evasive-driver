# m2473-high-fidelity-interface-hf0-contract-implementation-preflight Research Review

## Summary

- Generated at UTC: 20260603T062211Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: hf0_contract_preflight_pass_route_to_current_sim_adapter_smoke
- Decision reason: M2473 implements HF0 contract module and current-sim P0 preflight obs 72 action 3 contract flags false no hidden oracle actor leak no external simulation training ranking winner verdict claims

## Hypothesis

A local HF0 contract implementation and current-sim parity preflight can make high-fidelity interface boundaries machine-checkable without external simulation or actor/action contract changes.

## Lineage

- parent_checkpoint: not_applicable_hf0_contract_implementation_preflight
- parent_dataset: docs/m2472-high-fidelity-interface-hf0-design.md, docs/m2471-current-sim-readiness-route-synthesis.md, docs/post-m2470-route-plan.md, docs/observation-contract.md
- parent_config: experiments/manifests/m2472-high-fidelity-interface-hf0-design.json
- parent_objective: implement the HF0 backend contract and local current-sim parity preflight without external high-fidelity simulation
- derived_from: m2472-high-fidelity-interface-hf0-design, m2471-current-sim-readiness-route-synthesis
- blocked_by: HF0 design must become checked code before any high-fidelity adapter or validation run, P0 observation/action contract preservation must be machine-checkable, diagnostics and hidden values must be separated from actor-visible extraction
- supersedes: direct high-fidelity backend implementation without a checked contract, direct high-fidelity rollout before current-sim parity preflight, manual inspection of actor observation/action contract preservation
- invalidates: None

## Success Criteria

- src/autodrift/high_fidelity_interface.py exists
- src/autodrift/high_fidelity_interface_preflight.py exists
- tests/test_high_fidelity_interface.py exists and focused tests pass
- runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json exists
- summary reports observation_shape 72 and action_shape 3
- summary reports actor_input_contract_changed false action_contract_changed false hidden_values_enter_actor_input false oracle_labels_enter_actor_input false
- no external high-fidelity simulation training ranking winner or verdict claim is made

## Failure Criteria

- M2473 requires Chrono or another external high-fidelity simulator to run local tests
- M2473 changes actor input or action contract
- M2473 injects hidden or oracle actor features
- M2473 ranks controller families or selects a winner
- M2473 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2473 must implement a local HF0 contract module and focused tests
- M2473 must generate a summary artifact proving canonical P0 observation shape 72 and action shape 3 under current-sim parity preflight
- M2473 must prove hidden diagnostics and oracle labels are not read by the P0 observation extractor
- M2473 must preserve actor_input_contract_changed false and action_contract_changed false
- M2473 must not import or require external high-fidelity simulation
- M2473 must not train rank controllers select winners or make paper self-ID finite-window-vs-GRU current-sim or high-fidelity validation claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run external high-fidelity simulation
- do not run measured validation
- do not execute policy rollout beyond local shape preflight
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

- milestone: m2473-high-fidelity-interface-hf0-contract-implementation-preflight
- type: infrastructure
- checkpoint: runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hf0_contract_preflight_pass_route_to_current_sim_adapter_smoke
- reason: M2473 implements HF0 contract module and current-sim P0 preflight obs 72 action 3 contract flags false no hidden oracle actor leak no external simulation training ranking winner verdict claims

## Next Blocker

m2473-high-fidelity-interface-hf0-contract-implementation-preflight
