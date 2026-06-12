# m3246-c1-v4-distill-stage-a Research Review

## Summary

- Generated at UTC: 20260612T161158Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: c1_v4_stage_a_passed
- Decision reason: Completed: M3246 C1-v4 Stage A passed the frozen primary gate. Primary candidate minus v4_pertuned was +0.0139/-0.0208/+0.0000 on S1/S2/S3, so all three cells were within -0.05. Primary representation check found M3245 delta_max overbound on 17.18 percent of teacher frames; exploratory widened delta_max also passed but is not the gate. Stage B guarded RL is admitted only after separate preregistration; no driver-performance high-fidelity sufficiency repair-success feasibility-proof paper or self-ID claim is admitted.

## Hypothesis

A preregistered C1-v4 Stage A distill-then-RL gate can train a supervised bounded residual to imitate v4_pertuned minus frozen v4 on disjoint C5-prime rollouts and test closed-loop success within 0.05 paired of v4_pertuned in all three frozen T-limit cells before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3245-c1-v3-residual-rl-stage1.md, docs/m3222-a3-c5prime-target-consolidation.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/c5prime_target_consolidation.json
- parent_config: experiments/feasibility_audit/c5prime_prereg.json, experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_prereg.json, experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_quick.json
- parent_objective: C1-v4 final attempt: distill per-instance v4_pertuned recalibration before any guarded RL, Primary Stage A gate is distilled residual closed-loop success minus v4_pertuned success by frozen A3 validation cell
- derived_from: M3245 showed direct PPO over the bounded residual did not discover the simple recalibration at 65k steps, A3 confirmed the current-sim C5-prime structural gap in S1/S2/S3 T-limit cells, D1b Chrono-native oracle pricing was direction-positive and satisfies the CP-2 precondition, PI disposition opened C1-v4 as the final pre-registered learning attempt at the C5-prime prize
- blocked_by: Stage B guarded RL is not admitted unless primary Stage A passes all three cells, Track C closes if C1-v4 produces a behavior verdict that fails the frozen route
- supersedes: C1-v3 direct residual PPO continuation after M3245 stage-1 failure, local direct-MLP BC warm-start from M3228 and M3232, local tail-family interface pretrain from M3236, local family-selector route rejected by M3238
- invalidates: treating exploratory widened delta_max as a Stage B admission gate, running C1-v4 RL before the supervised Stage A closed-loop gate, any self-ID or history-attribution claim from this engineering distillation readout

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_prereg.json exists before full Stage A execution
- quick mode has run and written experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_quick.json before full Stage A interpretation
- Stage A execution writes experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a.json
- result JSON reports primary representation check and primary candidate minus v4_pertuned by all three frozen cells
- docs/m3246-c1-v4-distill-stage-a.md records measured versus inferred results

## Failure Criteria

- the run edits or mutates ActiveSafetyReflexDriver
- the run uses PPO or guarded RL during Stage A
- training rows overlap A3 validation eval seeds
- the exploratory widened delta_max arm is used as the primary pass gate
- the Stage A result is interpreted without paired CIs or after loosening the within-0.05 all-cell rule

## Evidence Gates

- M3246 must use the frozen ActiveSafetyReflexDriver v4 as the base and must not edit the incumbent driver
- M3246 must use a preregistration frozen before the full Stage A run
- M3246 must train on a new disjoint C1-v4 seed stream and must not train on A3 validation eval seeds
- M3246 primary arm must keep the M3245 delta_max bounds for comparability
- M3246 exploratory widened delta_max may be reported only as representation evidence and cannot admit Stage B
- M3246 must report primary candidate minus v4_pertuned by cell with paired bootstrap CIs without loosening the frozen pass rule
- M3246 must not make validation ranking driver-performance high-fidelity sufficiency paper repair-success robustness-result feasibility-proof or self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not run PPO or guarded RL in Stage A
- do not train on A3 validation rows or validation eval seeds
- do not use exploratory widened delta_max as the primary gate
- do not lower the within-0.05 all-cell bar after seeing the result
- do not admit C2 C3 or Stage B unless the primary Stage A gate passes

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3246-c1-v4-distill-stage-a
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: c1_v4_stage_a_passed
- reason: Completed: M3246 C1-v4 Stage A passed the frozen primary gate. Primary candidate minus v4_pertuned was +0.0139/-0.0208/+0.0000 on S1/S2/S3, so all three cells were within -0.05. Primary representation check found M3245 delta_max overbound on 17.18 percent of teacher frames; exploratory widened delta_max also passed but is not the gate. Stage B guarded RL is admitted only after separate preregistration; no driver-performance high-fidelity sufficiency repair-success feasibility-proof paper or self-ID claim is admitted.

## Next Blocker

C1-v4 Stage B guarded RL is admitted by the primary Stage A pass, but must be preregistered as a separate M3247 unit before any RL run.
