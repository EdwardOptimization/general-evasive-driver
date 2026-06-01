# m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation Research Review

## Summary

- Generated at UTC: 20260601T051538Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: current_sim_controlled_comparison_benchmark_spec_preflight_pass_route_to_audit
- Decision reason: M2148 no-rollout preflight pass 8 profiles 5 task families 18 metric rows 10 explicit gaps guardrail 0 no ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

The M2147 current-sim benchmark design can be materialized into a no-rollout spec preflight with explicit profile matrix, task families, metric support, and claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_current_sim_controlled_comparison_benchmark_spec_preflight
- parent_dataset: docs/m2147-paper-route-current-sim-controlled-comparison-benchmark-design.md, configs/paper_route_profiles/m1190_l0_current_masked_smoke.json, configs/paper_route_profiles/m1190_l1_one_step_smoke.json, configs/paper_route_profiles/m1190_l2_window_13_smoke.json, configs/paper_route_profiles/m1190_l2_window_25_smoke.json, configs/paper_route_profiles/m1190_l2_window_50_smoke.json, configs/paper_route_profiles/m1190_l2_window_100_smoke.json, configs/paper_route_profiles/m1190_l3_online_gru_smoke.json, configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
- parent_config: experiments/manifests/m2147-paper-route-current-sim-controlled-comparison-benchmark-design.json
- parent_objective: materialize a no-rollout current-sim controlled comparison benchmark spec preflight
- derived_from: m2147-paper-route-current-sim-controlled-comparison-benchmark-design
- blocked_by: M2147 must freeze controller matrix, task families, metrics, and claim boundary before preflight implementation
- supersedes: manual benchmark matrix tracking, direct measured execution without benchmark contract preflight
- invalidates: None

## Success Criteria

- configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json exists
- runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/summary.json exists
- profile matrix includes all 8 planned profiles
- task-family spec includes T1-T5
- claim boundary is machine-readable
- unsupported metric gaps are explicit
- no reset rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- required artifacts are missing
- profile matrix is incomplete
- T1-T5 task-family coverage is incomplete
- unsupported metrics are silently approximated
- ranking or paper-level claims are made

## Evidence Gates

- M2148 must write a machine-readable benchmark spec preflight artifact
- M2148 must write a profile matrix for the 8 planned controller profiles
- M2148 must represent T1-T5 task families and metric support without rollout
- M2148 must preserve actor input and action contract guardrails
- M2148 must not run reset rollout measured execution or rank controller families

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation
- type: infrastructure
- checkpoint: runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_controlled_comparison_benchmark_spec_preflight_pass_route_to_audit
- reason: M2148 no-rollout preflight pass 8 profiles 5 task families 18 metric rows 10 explicit gaps guardrail 0 no ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2149-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-audit
