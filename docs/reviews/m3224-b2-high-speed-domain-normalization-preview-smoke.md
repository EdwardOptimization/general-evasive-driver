# m3224-b2-high-speed-domain-normalization-preview-smoke Research Review

## Summary

- Generated at UTC: 20260611T204110Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b2_high_speed_env_contract_smoke_passed
- Decision reason: Completed: pre-registered B2 high-speed env-contract smoke; 48 episodes and 1776 frames; legacy vx/20 exposed max abs 1.800 and fixed preview 1.111 s; scaled profile selected-channel max abs 0.900, preview 2.500 s, high-speed labels 592/592, deterministic replay failures 0; B2 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Hypothesis

A non-default high-speed obs72 normalization and speed-aware road preview profile can represent 36 m/s scenarios, expose the legacy fixed-preview blocker, keep obs72 shape, and preserve deterministic high-speed feasibility labels before any training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/m3221-a2-obs-normalization-audit.md, docs/m3223-b1-moving-obstacle-kinematics-smoke.md
- parent_dataset: none: new env-contract smoke only
- parent_config: src/autodrift/env.py, src/autodrift/config.py, experiments/feasibility_audit/high_speed_domain_prereg.json
- parent_objective: execute roadmap B2 high-speed domain engineering without changing incumbent driver, obs72 shape, or legacy default scaling
- derived_from: docs/roadmap-phase3-codex-execution.md, docs/m3221-a2-obs-normalization-audit.md, experiments/feasibility_audit/high_speed_domain_prereg.json
- blocked_by: B2 full smoke completed
- supersedes: the B2 OPEN status line if the implementation and smoke are documented
- invalidates: assuming the legacy vx/20, ay/15, road_y/20, rel_vy/12, and fixed 40 m road preview are acceptable for 36 m/s scenarios

## Success Criteria

- experiments/feasibility_audit/high_speed_domain_prereg.json exists before full smoke
- experiments/feasibility_audit/high_speed_domain_smoke.json exists with protocol high_speed_domain_normalization_preview_smoke
- full smoke reports pass for obs72_shape, high_speed_reached, legacy_saturation_exposed, scaled_normalization, fixed_preview_short_exposed, speed_aware_preview, high_speed_label, and deterministic_replay
- the result document states that no training or driver claim is admitted

## Failure Criteria

- default observation scaling or obs72 shape changes
- the 36 m/s high-speed profile is available without explicit observation_scale plus max_speed_limit configuration
- selected scaled channels exceed max_abs <= 1.0
- speed-aware preview time drops below 2.45 s
- same seed and same actions do not replay deterministically
- the milestone trains, mutates a driver, changes actor-input labels, or admits Track C

## Evidence Gates

- M3224 must keep default ObservationScaleConfig values equivalent to the legacy obs72 contract
- M3224 must keep obs72 shape for history_length=1, action_history_mode=full, road_lookahead_count=8, obstacle_slots=4
- M3224 must expose the 36 m/s profile only through explicit observation_scale plus max_speed_limit configuration
- M3224 full smoke must show selected scaled channels within max_abs <= 1.0
- M3224 full smoke must show speed-aware preview time >= 2.45 s and deterministic replay
- M3224 must not mutate ActiveSafetyReflexDriver, public driver defaults, training configs, or checkpoints

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change the default obs72 scaling or shape
- do not train RL or create checkpoints
- do not use labels or hidden feasibility quantities as actor inputs
- do not claim driver performance or current-sim robustness from the smoke
- do not admit Track C training from this B2 env-contract result

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3224-b2-high-speed-domain-normalization-preview-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/high_speed_domain_smoke.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b2_high_speed_env_contract_smoke_passed
- reason: Completed: pre-registered B2 high-speed env-contract smoke; 48 episodes and 1776 frames; legacy vx/20 exposed max abs 1.800 and fixed preview 1.111 s; scaled profile selected-channel max abs 0.900, preview 2.500 s, high-speed labels 592/592, deterministic replay failures 0; B2 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Next Blocker

B3 geometry-channel degradation and split-mu remains open after B2; Track C remains blocked on CP-1.
