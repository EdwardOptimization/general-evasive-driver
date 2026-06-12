# m3247-c1-v4-stage-b-guarded-rl Research Review

## Summary

- Generated at UTC: 20260612T163430Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: c1_v4_stage_b_failed_track_c_closed
- Decision reason: Completed: M3247 C1-v4 Stage B first rung failed the frozen rule. 0/3 cells passed and 0/3 cells met the movement threshold; v4_stage_b minus v4_pertuned was -0.0651/-0.0425/-0.0052 on S1/S2/S3, with negative recapture fractions. No 4M extension, C2, C3, scale-up, driver-performance, high-fidelity sufficiency, repair-success, feasibility-proof, paper, or self-ID claim is admitted.

## Hypothesis

A preregistered C1-v4 Stage B guarded-RL first rung can initialize from the M3246 primary distiller, train eight fixed-log-std bounded residual policies for 1M current-sim steps per seed, and judge fixed v4 versus v4_pertuned versus v4_stage_b versus oracle on frozen A3 validation rows before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3246-c1-v4-distill-stage-a.md, docs/m3245-c1-v3-residual-rl-stage1.md, docs/m3222-a3-c5prime-target-consolidation.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/c5prime_target_consolidation.json, runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/primary_distiller.pt
- parent_config: experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_prereg.json, experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_quick.json, experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a.json
- parent_objective: C1-v4 final attempt: guarded RL from the distillation warm start toward the A3 oracle-minus-pertuned gap, Primary readout is v4_stage_b minus v4_pertuned by frozen A3 validation cell
- derived_from: M3246 primary Stage A passed all three frozen cells within 0.05 of v4_pertuned, M3245 direct residual PPO failed to discover the recalibration without distillation warm start, A3 confirmed the current-sim C5-prime structural gap in S1/S2/S3 T-limit cells, D1b Chrono-native oracle pricing was direction-positive and satisfies the CP-2 precondition
- blocked_by: No C3 scale-up is admitted until Stage B returns a positive frozen verdict, If first rung fails without movement then Track C closes per C1-v4 finality clause
- supersedes: C1-v3 direct residual PPO continuation after M3245 stage-1 failure, Stage A distillation-only protocol as a final verdict, local BC/interface/selector routes closed by M3228-M3238
- invalidates: running Stage B without M3246 Stage A pass, using exploratory widened delta_max as the primary Stage B policy, any self-ID or history-attribution claim from this engineering RL readout

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_prereg.json exists before full Stage B execution
- quick mode has run and written experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl_quick.json before full Stage B interpretation
- Stage B execution writes experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.json
- result JSON reports eight training seeds and 432 frozen validation rows
- docs/m3247-c1-v4-stage-b-guarded-rl.md records measured versus inferred results

## Failure Criteria

- the run edits or mutates ActiveSafetyReflexDriver
- the run uses A3 validation rows as training rows
- the warm start is not the M3246 primary distiller
- the Stage B result is interpreted without paired CIs and seed-clustered SE
- the recapture or extension criterion is loosened after seeing the result

## Evidence Gates

- M3247 must use the frozen ActiveSafetyReflexDriver v4 as the base and must not edit the incumbent driver
- M3247 must load the M3246 primary distiller as the warm start and keep the M3245 primary delta_max bounds
- M3247 must use a preregistration frozen before the full Stage B run
- M3247 must train eight model seeds on a new disjoint C1-v4 Stage B seed stream
- M3247 must evaluate fixed v4 v4_pertuned v4_stage_b and oracle on the frozen A3 validation rows
- M3247 must report seed-clustered SE and paired bootstrap CIs without loosening the pass or extension rule
- M3247 must not make validation ranking driver-performance high-fidelity sufficiency paper repair-success robustness-result feasibility-proof or self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not train on A3 validation rows or validation eval seeds
- do not use the M3246 exploratory widened-delta checkpoint as the primary warm start
- do not lower the recapture bar or movement threshold after seeing the result
- do not admit C2 C3 scale-up or paper claim from quick mode
- do not run an extension unless the frozen movement rule admits it

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3247-c1-v4-stage-b-guarded-rl
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: c1_v4_stage_b_failed_track_c_closed
- reason: Completed: M3247 C1-v4 Stage B first rung failed the frozen rule. 0/3 cells passed and 0/3 cells met the movement threshold; v4_stage_b minus v4_pertuned was -0.0651/-0.0425/-0.0052 on S1/S2/S3, with negative recapture fractions. No 4M extension, C2, C3, scale-up, driver-performance, high-fidelity sufficiency, repair-success, feasibility-proof, paper, or self-ID claim is admitted.

## Next Blocker

Track C is closed by the M3247 first-rung failure without movement. No 4M extension, C3 scale-up, or further C1 learning attempt is admitted without new pricing evidence.
