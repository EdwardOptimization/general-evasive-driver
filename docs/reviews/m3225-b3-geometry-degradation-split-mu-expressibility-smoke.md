# m3225-b3-geometry-degradation-split-mu-expressibility-smoke Research Review

## Summary

- Generated at UTC: 20260611T205720Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b3_geometry_degradation_smoke_passed
- Decision reason: Completed: pre-registered B3 geometry-channel degradation smoke and split-mu expressibility audit; 16 episodes and 400 paired frames; ego/command delta 0, present/size delta 0, empty-slot delta 0; road max delta 0.159, active obstacle continuous max delta 0.132, deterministic replay failures 0; split-mu declared not expressible in the current DriftObstacleEnv single-track outcome path; B3 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Hypothesis

A config-gated geometry-channel observation degradation mode can perturb road-boundary and obstacle continuous geometry channels while preserving ego response, commands, obstacle present bits, obstacle sizes, empty slots, obs72 shape, and deterministic replay; left/right split-mu will be implemented only if physically expressible in the current single-track simulator, otherwise declared not expressible before any training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/data-coverage-map-2026-06.md, docs/m3224-b2-high-speed-domain-normalization-preview-smoke.md
- parent_dataset: none: new env-contract smoke and expressibility audit only
- parent_config: src/autodrift/observation_degradation_wrapper.py, src/autodrift/env.py, experiments/feasibility_audit/geometry_degradation_prereg.json
- parent_objective: execute roadmap B3 geometry-channel degradation engineering and split-mu expressibility audit without changing incumbent driver, obs72 shape, or training configs
- derived_from: docs/roadmap-phase3-codex-execution.md, docs/data-coverage-map-2026-06.md, experiments/feasibility_audit/geometry_degradation_prereg.json
- blocked_by: B3 full smoke completed
- supersedes: the B3 OPEN status line if the implementation and smoke are documented
- invalidates: assuming obs72 road/obstacle geometry channels cannot be degraded by the task wrapper, assuming current single-track dynamics necessarily express left/right split-mu

## Success Criteria

- experiments/feasibility_audit/geometry_degradation_prereg.json exists before full smoke
- experiments/feasibility_audit/geometry_degradation_smoke.json exists with protocol geometry_degradation_and_split_mu_expressibility_smoke
- full smoke reports pass for obs72_shape, ego_command_untouched, road_boundary_degraded, obstacle_geometry_degraded, present_and_size_untouched, empty_slots_untouched, termination_consistency, deterministic_replay, and split_mu_declared_not_expressible when applicable
- the result document states that no training or driver claim is admitted

## Failure Criteria

- default ego-degradation behavior changes
- geometry noise perturbs ego/command channels, obstacle present bits, size fields, or empty slots
- same seed and same actions do not replay deterministically
- split-mu is added without current-sim left/right wheel-contact semantics
- the milestone trains, mutates a driver, changes actor-input labels, or admits Track C

## Evidence Gates

- M3225 must keep default geometry_scope=none behavior compatible with existing ego-degradation tests
- M3225 must keep obs72 shape
- M3225 geometry noise must perturb road-boundary and active obstacle continuous geometry channels
- M3225 geometry noise must not perturb ego response, previous commands, obstacle present bits, obstacle size fields, empty obstacle slots, privileged channels, rewards, or termination
- M3225 deterministic replay must pass on frozen replay seeds
- M3225 must declare split-mu not expressible if current-sim lacks left/right wheel contact semantics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not perturb obstacle present bits or create ghost obstacle slots
- do not change obs72 shape
- do not train RL or create checkpoints
- do not add a fake split-mu label without a physical current-sim mechanism
- do not claim driver performance, robustness, or self-ID from the smoke

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3225-b3-geometry-degradation-split-mu-expressibility-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/geometry_degradation_smoke.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b3_geometry_degradation_smoke_passed
- reason: Completed: pre-registered B3 geometry-channel degradation smoke and split-mu expressibility audit; 16 episodes and 400 paired frames; ego/command delta 0, present/size delta 0, empty-slot delta 0; road max delta 0.159, active obstacle continuous max delta 0.132, deterministic replay failures 0; split-mu declared not expressible in the current DriftObstacleEnv single-track outcome path; B3 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Next Blocker

B4 minute-scale drive structure remains open after B3; Track C remains blocked on CP-1.
