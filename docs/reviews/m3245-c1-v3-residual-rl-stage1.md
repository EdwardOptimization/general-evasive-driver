# m3245-c1-v3-residual-rl-stage1 Research Review

## Summary

- Generated at UTC: 20260612T135400Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: c1_v3_stage1_failed
- Decision reason: Completed: M3245 C1-v3 stage-1 failed the frozen gate with 0/3 cells passing. v4_residual minus v4_pertuned was -0.6276/-0.4262/-0.3299 on S1/S2/S3 and all CI95 intervals were negative. No C2, C3, scale-up, driver-performance, high-fidelity sufficiency, repair-success, feasibility-proof, or self-ID claim is admitted.

## Hypothesis

A preregistered C1-v3 residual-RL stage-1 run can train eight bounded residual policies on disjoint C5-prime rows over the frozen v4 reflex and judge fixed v4 versus v4_pertuned versus v4 residual versus oracle on frozen A3 validation rows before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3244-c1-v3-residual-rl-smoke.md, docs/m3222-a3-c5prime-target-consolidation.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/c5prime_target_consolidation.json
- parent_config: experiments/feasibility_audit/c5prime_prereg.json, experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke_prereg.json, experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1_prereg.json
- parent_objective: C1-v3 residual RL on the frozen v4 reflex base, Primary readout is v4_residual minus v4_pertuned by frozen A3 validation cell
- derived_from: M3244 passed the residual-on-frozen-v4 1024-step PPO smoke, A3 confirmed the current-sim C5-prime structural gap in S1/S2/S3 T-limit cells, D1b Chrono-native oracle pricing was direction-positive and satisfied the CP-2 precondition, PI reopened C1 as C1-v3 after local imitation and selector-interface routes failed
- blocked_by: C3 scale-up is not admitted from the negative M3245 stage-1 result, Further C1-v3 work requires synthesis or PI route selection
- supersedes: local direct-MLP BC warm-start from M3228 and M3232, local tail-family interface pretrain from M3236, local family-selector route rejected by M3238
- invalidates: treating M3244 smoke as a performance result, using supervised oracle-demo labels in C1-v3, any self-ID or history-attribution claim from this engineering RL readout

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1_prereg.json exists before stage-1 execution
- quick mode has run and written experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1_quick.json before full stage-1 interpretation
- stage-1 execution writes experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.json
- result JSON reports eight training seeds and 432 frozen validation rows
- docs/m3245-c1-v3-residual-rl-stage1.md records measured versus inferred results

## Failure Criteria

- the run edits or mutates ActiveSafetyReflexDriver
- the run uses BC labels or oracle-demo supervised targets
- training rows overlap A3 validation eval seeds
- the stage-1 result is interpreted without paired CIs and seed-clustered SE
- the recapture criterion is loosened after seeing the result

## Evidence Gates

- M3245 must use the frozen ActiveSafetyReflexDriver v4 as the base and must not edit the incumbent driver
- M3245 must use a preregistration frozen before the stage-1 run
- M3245 must train eight residual policies with model seeds disjoint from M3244 and validation seeds
- M3245 must evaluate fixed v4 v4_pertuned v4_residual and oracle on the frozen A3 validation rows
- M3245 must report seed-clustered SE and paired bootstrap CIs without loosening the pass rule
- M3245 must not make validation ranking driver-performance high-fidelity sufficiency paper repair-success robustness-result feasibility-proof or self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not use supervised oracle-demo labels or BC warm-start checkpoints
- do not train on A3 validation rows or validation eval seeds
- do not lower the recapture bar or reinterpret quick mode as a stage-1 result
- do not admit C2 or C3 without the stage-1 verdict and PI checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3245-c1-v3-residual-rl-stage1
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: c1_v3_stage1_failed
- reason: Completed: M3245 C1-v3 stage-1 failed the frozen gate with 0/3 cells passing. v4_residual minus v4_pertuned was -0.6276/-0.4262/-0.3299 on S1/S2/S3 and all CI95 intervals were negative. No C2, C3, scale-up, driver-performance, high-fidelity sufficiency, repair-success, feasibility-proof, or self-ID claim is admitted.

## Next Blocker

C3 scale-up and any run over one hour are not admitted from the negative stage-1 result; synthesis or PI route selection is required before further C1-v3 attempts.
