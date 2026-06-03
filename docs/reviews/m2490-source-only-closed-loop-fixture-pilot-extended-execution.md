# m2490-source-only-closed-loop-fixture-pilot-extended-execution Research Review

## Summary

- Generated at UTC: 20260603T083446Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_only_closed_loop_fixture_pilot_extended_pass_route_to_audit
- Decision reason: M2490 passes extended source-only same-contract policy-action execution checkpoint admitted obs 72 action 3 fixtures 3 resets 3 steps 300 leak flags false no simulation training ranking winner or verdict claims

## Hypothesis

The same admitted actor can continue bounded deterministic policy actions through the three source-only HF0 fixtures for 100 steps per fixture without actor-input leakage or backend path failure.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m2489-source-only-closed-loop-fixture-pilot-result-audit.md, runs/m2488_source_only_closed_loop_fixture_pilot_preflight/summary.json, runs/m2488_source_only_closed_loop_fixture_pilot_preflight/pilot_rollout_rows.csv, docs/m2488-source-only-closed-loop-fixture-pilot-implementation-preflight.md
- parent_config: experiments/manifests/m2489-source-only-closed-loop-fixture-pilot-result-audit.json
- parent_objective: run a longer bounded source-only closed-loop fixture pilot after M2489 accepts M2488 path smoke
- derived_from: m2489-source-only-closed-loop-fixture-pilot-result-audit, m2488-source-only-closed-loop-fixture-pilot-implementation-preflight
- blocked_by: M2488 only covered 20 policy-action steps per fixture, longer source-only execution is needed before any broader route selection, the follow-up must preserve actor admission and leak gates without claiming performance
- supersedes: another audit-only source-only pilot milestone after M2489, direct success-rate or performance claim from M2488
- invalidates: None

## Success Criteria

- runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/summary.json exists
- runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/pilot_rollout_rows.csv exists
- checkpoint loads and is admitted as obs_dim 72 action_dim 3 allowed recurrent actor
- three admitted source-only fixtures reset and run 100 policy-action steps each
- all reset and step observations have shape 72
- all actions have shape 3 finite values and stay within deployed bounds
- all actor-input leak flags are false
- no external high-fidelity simulation install import execution training replay PPO ranking winner or verdict claim is made

## Failure Criteria

- M2490 installs imports or runs Chrono or another external simulator
- M2490 changes actor input or action contract
- M2490 injects hidden or oracle actor features
- M2490 trains replays runs PPO promotes ranks or selects a winner
- M2490 computes success rate or claims driver performance
- M2490 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2490 must reuse the admitted checkpoint path and same-contract 72 observation 3 action admission gate
- M2490 must run exactly the three M2484 admitted source-only fixtures unless the manifest is updated before execution
- M2490 must execute deterministic deployable policy actions for 100 steps per fixture through FourWheelHF0Backend
- M2490 must preserve P0 observation shape 72 and action shape 3 at every reset and step
- M2490 must keep fixture labels scenario labels feasibility classes hidden values wheel diagnostics oracle labels TTC required clearance reward terms and success or progress labels out of actor input
- M2490 must write summary.json and pilot_rollout_rows.csv and must not train replay run PPO rank select a winner promote a checkpoint or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not run measured validation
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
- do not compute success rate or controller-family verdict metrics in this execution

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2490-source-only-closed-loop-fixture-pilot-extended-execution
- type: infrastructure
- checkpoint: runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_only_closed_loop_fixture_pilot_extended_pass_route_to_audit
- reason: M2490 passes extended source-only same-contract policy-action execution checkpoint admitted obs 72 action 3 fixtures 3 resets 3 steps 300 leak flags false no simulation training ranking winner or verdict claims

## Next Blocker

m2490-source-only-closed-loop-fixture-pilot-extended-execution
