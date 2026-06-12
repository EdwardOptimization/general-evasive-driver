# m3244-c1-v3-residual-rl-smoke Research Review

## Summary

- Generated at UTC: 20260612T132334Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: c1_v3_residual_rl_smoke_passed
- Decision reason: Completed: M3244 residual-on-frozen-v4 PPO smoke passed all preregistered quick gates. It ran 1024 steps, completed 10 episodes, exercised S1/S2/S3 C5-prime structural-gap rows, kept residual/final actions finite and bounded, changed model parameters by L2 0.185837, and wrote checkpoint plus metrics. Smoke only; no stage-1 or performance claim.

## Hypothesis

A preregistered C1-v3 residual-RL smoke can run exactly 1024 current-sim C5-prime steps with action clip frozen v4 plus bounded residual and one PPO update before stage-1 validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3222-a3-c5prime-target-consolidation.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md, docs/escalations/2026-06-12-phase3-roadmap-exhausted-pi-route.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/c5prime_target_consolidation.json
- parent_config: experiments/feasibility_audit/c5prime_prereg.json, experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke_prereg.json
- parent_objective: C1-v3 residual RL on the frozen v4 reflex base
- derived_from: PI route decision in docs/roadmap-phase3-codex-execution.md reopened C1 as C1-v3 after M3243, A3 C5-prime current-sim structural gap confirmed S1/S2/S3 T-limit target cells, D1b Chrono-native oracle pricing direction-positive satisfied the CP-2 precondition, M3228-M3238 closed the local imitation and selector-interface route
- blocked_by: Full stage-1 and any run over one hour remain blocked on a separate C1-v3 preregistration and CP-2 budget approval
- supersedes: local direct-MLP BC warm-start from M3228 and M3232, local tail-family interface pretrain from M3236, local family-selector route rejected by M3238
- invalidates: treating a 1024-step smoke as stage-1 performance evidence, admitting C2 or C3 from M3244, any self-ID or history-attribution claim from C1-v3 residual RL

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke_prereg.json exists before quick execution
- quick execution writes experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.json
- result JSON reports passed_quick_gates true
- checkpoint and metrics artifacts are written under runs/feasibility_audit/c5prime_c1_v3_residual_rl_smoke/quick
- docs/m3244-c1-v3-residual-rl-smoke.md records measured vs inferred results

## Failure Criteria

- the smoke edits or mutates ActiveSafetyReflexDriver
- the smoke uses BC labels or oracle-demo supervised targets
- the smoke fails residual bounds finite-loss or optimizer-update gates
- the smoke is used as a stage-1 performance or self-ID claim

## Evidence Gates

- M3244 must use the frozen ActiveSafetyReflexDriver v4 as a base and must not edit the incumbent driver
- M3244 must run exactly 1024 environment steps on frozen C5-prime rows before any stage-1 run
- M3244 must keep residual deltas bounded by the preregistered per-channel delta_max
- M3244 must write result JSON plus checkpoint and metrics artifacts
- M3244 must not make a validation ranking driver-performance high-fidelity sufficiency paper repair-success robustness-result feasibility-proof or self-ID claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not use supervised oracle-demo labels or BC warm-start artifacts
- do not loosen the 1024-step quick smoke gates
- do not start a stage-1 or over-one-hour run from this manifest
- do not claim C2 admission driver-performance promotion high-fidelity sufficiency feasibility proof or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3244-c1-v3-residual-rl-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_v3_residual_rl_smoke.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: c1_v3_residual_rl_smoke_passed
- reason: Completed: M3244 residual-on-frozen-v4 PPO smoke passed all preregistered quick gates. It ran 1024 steps, completed 10 episodes, exercised S1/S2/S3 C5-prime structural-gap rows, kept residual/final actions finite and bounded, changed model parameters by L2 0.185837, and wrote checkpoint plus metrics. Smoke only; no stage-1 or performance claim.

## Next Blocker

C1-v3 stage-1 requires a separate four-arm preregistration and CP-2 budget approval before any run over one hour.
