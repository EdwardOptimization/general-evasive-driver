# m3240-b1b-moving-obstacle-pricing-full Research Review

## Summary

- Generated at UTC: 20260612T080904Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b1b_moving_obstacle_pricing_negative
- Decision reason: Completed: full B1b moving-obstacle pricing was negative by the frozen rule: 0/4 cells qualified, oracle-minus-pertuned gap was 0.0000 in every cell, oracle solvability was 1.0, and fixed_star/v4_rls/v4_pertuned all succeeded 32/32. All rows were aeb_feasible; current moving-crosser formulation does not create a type-b prize.

## Hypothesis

A preregistered B1b moving-obstacle full pricing panel can decide whether the flagged constant-velocity crosser axis creates type-b regions where a reveal-constrained oracle beats the best disjoint-selection reflex-family arm before any training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3223-b1-moving-obstacle-kinematics-smoke.md, docs/m3239-b1b-moving-obstacle-pricing-smoke.md
- parent_dataset: experiments/feasibility_audit/moving_obstacle_pricing_quick.json
- parent_config: experiments/feasibility_audit/moving_obstacle_pricing_prereg.json, scripts/feasibility_audit/moving_obstacle_pricing.py
- parent_objective: full B1b moving-obstacle pricing after M3239 protocol smoke
- derived_from: M3223 flagged constant-velocity crosser env axis, M3239 B1b pricing protocol smoke passed, M3239 quick cells were all-success for reflex arms, so full pricing must be interpreted without assuming a positive prize
- blocked_by: Moving-obstacle Track C extension remains blocked until full B1b pricing is positive
- supersedes: using M3239 quick mode as a pricing verdict
- invalidates: opening moving-obstacle Track C training without full pricing, claiming B1b prize from protocol smoke

## Success Criteria

- experiments/feasibility_audit/moving_obstacle_pricing.json exists with protocol b1b_moving_obstacle_pricing and quick_mode false
- result reports all four preregistered full cells
- result reports oracle-solved denominator structural gaps and qualifying cells
- result decision applies the frozen >=2 qualifying cells rule
- the result document separates measured and inferred sections

## Failure Criteria

- M3240 runs quick mode instead of full mode
- M3240 runs training or writes a policy checkpoint
- M3240 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3240 admits Track C training or C2 directly
- M3240 changes the full decision rule after seeing results

## Evidence Gates

- M3240 must use the frozen B1b preregistration decision rule
- M3240 must run the full four-cell panel, not quick mode
- M3240 must report oracle-solved denominator and oracle-infeasible rows separately
- M3240 must preserve the inert/no-spread status of the RLS arm
- M3240 must not admit training unless the full pricing rule is positive and a later PI/admission gate opens it

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, or guarded RL
- do not mutate the incumbent driver
- do not change the preregistered full decision rule after seeing M3239 quick results
- do not admit Track C training or C2 from a negative or inconclusive B1b full result
- do not claim driver performance, validation ranking, promotion, high-fidelity sufficiency, repair-success, robustness-result, feasibility-proof, paper, or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3240-b1b-moving-obstacle-pricing-full
- type: infrastructure
- checkpoint: experiments/feasibility_audit/moving_obstacle_pricing.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b1b_moving_obstacle_pricing_negative
- reason: Completed: full B1b moving-obstacle pricing was negative by the frozen rule: 0/4 cells qualified, oracle-minus-pertuned gap was 0.0000 in every cell, oracle solvability was 1.0, and fixed_star/v4_rls/v4_pertuned all succeeded 32/32. All rows were aeb_feasible; current moving-crosser formulation does not create a type-b prize.

## Next Blocker

B1b current moving-obstacle formulation is done-negative. Move to the next independent OPEN roadmap unit, B2b high-speed domain pricing, unless a new preregistered moving-obstacle hardening unit is explicitly opened later.
