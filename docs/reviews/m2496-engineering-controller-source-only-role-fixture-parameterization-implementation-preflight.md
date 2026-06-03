# m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight Research Review

## Summary

- Generated at UTC: 20260603T091813Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_only_role_fixture_parameterization_preflight_pass_route_to_result_audit
- Decision reason: M2496 passes reset-only source-only role fixture parameterization 3 specs 3 resets obs 72 action 3 unique state fault road obstacle reset digests pairwise L2 min 0.303787 no policy action training ranking success-rate verdict claims

## Hypothesis

A reset-only source-only role fixture parameterization preflight can verify dynamically differentiated role fixtures while preserving actor/action contracts and avoiding performance overclaims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m2495-engineering-controller-source-only-role-fixture-parameterization-design.md, docs/m2494-engineering-controller-source-only-role-metric-panel-result-audit.md, runs/m2493_engineering_controller_source_only_role_metric_panel/role_metric_panel.csv
- parent_config: experiments/manifests/m2495-engineering-controller-source-only-role-fixture-parameterization-design.json
- parent_objective: implement reset-only source-only role fixture parameterization preflight
- derived_from: m2495-engineering-controller-source-only-role-fixture-parameterization-design, m2494-engineering-controller-source-only-role-metric-panel-result-audit
- blocked_by: source-only role fixtures need dynamic differentiation before role metric panel rerun, implementation must preserve P0 actor input and action contracts, preflight must verify differentiation without policy actions or verdict claims
- supersedes: another role metric panel over metadata-only fixtures, direct source-only performance claim from identical role metrics
- invalidates: None

## Success Criteria

- runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json exists
- runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/fixture_parameterization_rows.csv exists
- runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/reset_differentiation_rows.csv exists
- exactly three role fixture specs exist
- all reset observations have shape 72
- action shape remains 3
- pairwise reset observation L2 min is greater than 1e-3
- state obstacle and fault-scale digests show role differentiation
- all actor-input leak flags are false
- policy_action and policy_rollout_run are false
- no external high-fidelity simulation install import execution training ranking winner success-rate or verdict claim is made

## Failure Criteria

- M2496 installs imports or runs Chrono or another external simulator
- M2496 changes actor input or action contract
- M2496 injects hidden or oracle actor features
- M2496 executes policy actions or rollout
- M2496 leaves role reset observations identical
- M2496 treats fixture parameterization as driver performance
- M2496 ranks controller families or selects a winner
- M2496 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2496 must implement the M2495 source-only role fixture parameterization design
- M2496 must preserve the default FourWheelHF0Backend behavior when no fixture spec is supplied
- M2496 must create exactly three role fixture specs for stable_aes drift_required_recovery and unavoidable_mitigation
- M2496 must run reset-only preflight over the three specs and must not execute policy actions
- M2496 must verify P0 observation shape 72 and action shape 3 remain unchanged
- M2496 must verify role labels fixture labels hidden diagnostics oracle labels TTC required clearance reward terms and success labels stay out of actor input
- M2496 must verify reset observations state digests fault-scale digests and obstacle digests are differentiated by role
- M2496 must write summary.json fixture_parameterization_rows.csv reset_differentiation_rows.csv and a milestone doc without success-rate ranking winner validation or driver-performance claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not run measured validation
- do not execute policy actions
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
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from source-only fixture parameterization

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight
- type: infrastructure
- checkpoint: runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_only_role_fixture_parameterization_preflight_pass_route_to_result_audit
- reason: M2496 passes reset-only source-only role fixture parameterization 3 specs 3 resets obs 72 action 3 unique state fault road obstacle reset digests pairwise L2 min 0.303787 no policy action training ranking success-rate verdict claims

## Next Blocker

m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight
