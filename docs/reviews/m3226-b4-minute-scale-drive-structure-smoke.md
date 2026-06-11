# m3226-b4-minute-scale-drive-structure-smoke Research Review

## Summary

- Generated at UTC: 20260611T211058Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: b4_minute_scale_drive_structure_smoke_passed
- Decision reason: Completed: pre-registered B4 minute-scale drive-structure env smoke; 4 full seeds reached 3000 steps / 60.0 s with obs72 shape preserved; warmup gate passed at steps 215-216, emergency obstacle appeared at step 250, raw obstacle pass occurred at steps 991-999, post-pass continuation minimum 2001 steps, deterministic replay failures 0; B4 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Hypothesis

A B4 minute-scale env profile can preserve obs72 shape, carry warmup-gate familiarization into a later emergency-obstacle phase in the same episode, record raw obstacle pass without finish_on_pass truncation, and continue to max_steps before any training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/data-coverage-map-2026-06.md, docs/m3225-b3-geometry-degradation-split-mu-expressibility-smoke.md
- parent_dataset: none: new env-contract smoke only
- parent_config: src/autodrift/env.py, experiments/feasibility_audit/minute_scale_drive_structure_prereg.json
- parent_objective: execute roadmap B4 minute-scale drive-structure engineering without changing incumbent driver, obs72 shape, or training configs
- derived_from: docs/roadmap-phase3-codex-execution.md, docs/data-coverage-map-2026-06.md, experiments/feasibility_audit/minute_scale_drive_structure_prereg.json
- blocked_by: B4 full smoke completed
- supersedes: the B4 OPEN status line if the implementation and smoke are documented
- invalidates: assuming raw obstacle-pass events require finish_on_pass truncation, assuming warmup-gate familiarization cannot carry into a later obstacle phase within one episode

## Success Criteria

- experiments/feasibility_audit/minute_scale_drive_structure_prereg.json exists before full smoke
- experiments/feasibility_audit/minute_scale_drive_structure_smoke.json exists with protocol minute_scale_drive_structure_smoke
- full smoke reports pass for obs72_shape, max_steps_reached, warmup_gate_sequence, emergency_obstacle_sequence, raw_pass_continuation, post_pass_continuation, and deterministic_replay
- the result document states that no training or driver claim is admitted

## Failure Criteria

- obs72 shape changes
- finish_on_pass=true obstacle completion behavior regresses
- raw obstacle pass cannot be observed when finish_on_pass=false
- long smoke terminates before max_steps
- same seed and same scripted controller do not replay deterministically
- the milestone trains, mutates a driver, changes actor-input labels, or admits Track C

## Evidence Gates

- M3226 must keep obs72 shape
- M3226 must keep finish_on_pass=true completion behavior compatible with existing tests
- M3226 must make obstacle_passed_raw independent from finish_on_pass truncation
- M3226 full smoke must reach 3000 steps on all frozen seeds
- M3226 full smoke must show warmup_gate -> emergency_obstacle -> raw pass -> post-pass continuation in the same episode
- M3226 deterministic replay must pass on frozen replay seeds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not train RL or create checkpoints
- do not claim driver performance from the scripted survival controller
- do not change obs72 shape
- do not loosen existing obstacle completion tests

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3226-b4-minute-scale-drive-structure-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/minute_scale_drive_structure_smoke.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: b4_minute_scale_drive_structure_smoke_passed
- reason: Completed: pre-registered B4 minute-scale drive-structure env smoke; 4 full seeds reached 3000 steps / 60.0 s with obs72 shape preserved; warmup gate passed at steps 215-216, emergency obstacle appeared at step 250, raw obstacle pass occurred at steps 991-999, post-pass continuation minimum 2001 steps, deterministic replay failures 0; B4 is env engineering only; no training driver mutation validation ranking promotion paper repair-success robustness-result feasibility-proof or self-ID claim.

## Next Blocker

After B4, Track C remains blocked on CP-1 and D1 Chrono S4 pricing remains open.
