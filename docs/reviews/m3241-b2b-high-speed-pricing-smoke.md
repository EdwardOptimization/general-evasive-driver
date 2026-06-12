# m3241-b2b-high-speed-pricing-smoke Research Review

## Summary

- Generated at UTC: 20260612T082501Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b2b_pricing_protocol_smoke_passed
- Decision reason: Completed: M3241 quick protocol smoke passed in 2.0 s with 108 selection episodes, 32 validation arm episodes, and 27 oracle rollouts over two high-speed cells. hs24_tight_mu055 showed a quick-mode oracle-minus-pertuned gap of 0.25 with CI lower 0, while hs30_tight_mu075 was 0; quick mode is not a B2b pricing verdict.

## Hypothesis

A preregistered B2b high-speed pricing protocol smoke can exercise the M3224 high-speed observation/preview profile with raw incumbent, scale-aware fixed*, inert RLS, per-cell tuned reflex, and reveal-constrained oracle arms before any full B2b pricing verdict, training, validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3224-b2-high-speed-domain-normalization-preview-smoke.md, docs/m3240-b1b-moving-obstacle-pricing-full.md
- parent_dataset: experiments/feasibility_audit/high_speed_domain_smoke.json
- parent_config: experiments/feasibility_audit/high_speed_pricing_prereg.json, scripts/feasibility_audit/high_speed_pricing.py
- parent_objective: price whether production-speed window compression opens type-b gaps
- derived_from: M3224 high-speed observation/preview profile, M3240 closed B1b moving-obstacle current formulation negative, roadmap B2b is the next independent OPEN unit
- blocked_by: Full B2b pricing is not interpretable until this protocol smoke passes
- supersedes: direct full B2b pricing without a protocol smoke
- invalidates: claiming high-speed prize from quick mode, opening training or C2 from B2b smoke

## Success Criteria

- experiments/feasibility_audit/high_speed_pricing_quick.json exists with protocol b2b_high_speed_pricing
- quick result reports two high-speed cells and disjoint selection/validation seed streams
- quick result reports raw incumbent plus scale-aware fixed_star/v4_rls/v4_pertuned and oracle attempts
- decision says quick mode is protocol smoke only and not a B2b pricing verdict
- the result document separates measured and inferred sections

## Failure Criteria

- M3241 runs training or writes a policy checkpoint
- M3241 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3241 interprets quick mode as a B2b pricing verdict
- M3241 admits Track C training or C2
- M3241 omits the scale-adapter/raw-incumbent distinction

## Evidence Gates

- M3241 must be quick protocol smoke only, not a B2b full pricing verdict
- M3241 must use disjoint selection and validation seed streams
- M3241 must exercise raw incumbent, scale-aware fixed_star, inert RLS, per-cell tuned reflex, and oracle arms
- M3241 must keep v4_rls explicitly inert/no-spread on this speed-window-only panel
- M3241 must keep C1/C2/C3 training blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, or guarded RL
- do not mutate the incumbent driver
- do not interpret quick mode as a B2b pricing verdict
- do not admit Track C training or C2 from this smoke
- do not claim driver performance, validation ranking, promotion, high-fidelity sufficiency, repair-success, robustness-result, feasibility-proof, paper, or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3241-b2b-high-speed-pricing-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/high_speed_pricing_quick.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b2b_pricing_protocol_smoke_passed
- reason: Completed: M3241 quick protocol smoke passed in 2.0 s with 108 selection episodes, 32 validation arm episodes, and 27 oracle rollouts over two high-speed cells. hs24_tight_mu055 showed a quick-mode oracle-minus-pertuned gap of 0.25 with CI lower 0, while hs30_tight_mu075 was 0; quick mode is not a B2b pricing verdict.

## Next Blocker

Full B2b pricing remains unrun. M3241 quick smoke passed the protocol gates and showed only weak quick-mode prize evidence (hs24_tight_mu055 gap 0.25 with CI lower 0).
