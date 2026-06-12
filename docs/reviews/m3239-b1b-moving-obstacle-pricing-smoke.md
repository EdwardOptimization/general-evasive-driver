# m3239-b1b-moving-obstacle-pricing-smoke Research Review

## Summary

- Generated at UTC: 20260612T080258Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b1b_pricing_protocol_smoke_passed
- Decision reason: Completed: M3239 quick protocol smoke passed in 3.4 s with 108 selection episodes, 32 validation arm episodes, and 12 oracle rollouts over two moving-obstacle cells. All protocol gates passed, but both quick cells were all-success for fixed_star/v4_rls/v4_pertuned/oracle, so quick mode gives no B1b prize evidence and is not a full pricing verdict.

## Hypothesis

A preregistered B1b moving-obstacle pricing protocol smoke can exercise the constant-velocity crosser panel with fixed*, inert RLS, per-cell tuned reflex, and reveal-constrained oracle arms before any full B1b pricing verdict, training, validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3223-b1-moving-obstacle-kinematics-smoke.md
- parent_dataset: experiments/feasibility_audit/moving_obstacle_smoke.json
- parent_config: experiments/feasibility_audit/moving_obstacle_pricing_prereg.json, scripts/feasibility_audit/moving_obstacle_pricing.py
- parent_objective: price whether moving-obstacle timing can create a type-b structural gap
- derived_from: B1/M3223 flagged constant-velocity crosser env axis, C5/A3 four-arm pricing pattern, M3238 blocked local C1 selector/interface route, making independent B1b pricing the lowest OPEN roadmap unit
- blocked_by: Full B1b pricing is not interpretable until this protocol smoke passes
- supersedes: direct full B1b pricing without a protocol smoke
- invalidates: claiming moving-obstacle prize from quick mode, opening training or C2 from B1b smoke

## Success Criteria

- experiments/feasibility_audit/moving_obstacle_pricing_quick.json exists with protocol b1b_moving_obstacle_pricing
- quick result reports two moving-obstacle cells and disjoint selection/validation seed streams
- quick result reports all four reflex arms plus oracle attempts
- decision says quick mode is protocol smoke only and not a B1b pricing verdict
- the result document separates measured and inferred sections

## Failure Criteria

- M3239 runs training or writes a policy checkpoint
- M3239 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3239 interprets quick mode as a B1b pricing verdict
- M3239 admits Track C training or C2
- M3239 omits the inert/no-spread status of the RLS arm

## Evidence Gates

- M3239 must be quick protocol smoke only, not a B1b full pricing verdict
- M3239 must use disjoint selection and validation seed streams
- M3239 must exercise fixed_v4_incumbent, fixed_star, v4_rls, v4_pertuned, and oracle arms
- M3239 must keep v4_rls explicitly inert/no-spread on this moving-obstacle-only panel
- M3239 must keep C1/C2/C3 training blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, or guarded RL
- do not mutate the incumbent driver
- do not interpret quick mode as a B1b pricing verdict
- do not admit Track C training or C2 from this smoke
- do not claim driver performance, validation ranking, promotion, high-fidelity sufficiency, repair-success, robustness-result, feasibility-proof, paper, or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3239-b1b-moving-obstacle-pricing-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/moving_obstacle_pricing_quick.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b1b_pricing_protocol_smoke_passed
- reason: Completed: M3239 quick protocol smoke passed in 3.4 s with 108 selection episodes, 32 validation arm episodes, and 12 oracle rollouts over two moving-obstacle cells. All protocol gates passed, but both quick cells were all-success for fixed_star/v4_rls/v4_pertuned/oracle, so quick mode gives no B1b prize evidence and is not a full pricing verdict.

## Next Blocker

Full B1b pricing remains unrun. M3239 quick smoke passed the protocol gates but produced zero quick-mode prize evidence because both quick cells were all-success for the reflex arms.
