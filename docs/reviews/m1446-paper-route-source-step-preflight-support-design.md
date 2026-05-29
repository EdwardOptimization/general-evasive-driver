# m1446-paper-route-source-step-preflight-support-design Research Review

## Summary

- Generated at UTC: 20260529T040636Z
- Type: gate
- Gate tier: process
- Promotion decision: source_step_preflight_support_design_admit_implementation
- Decision reason: M1446 designs explicit candidate-step column support so source-step candidates are not evaluated at reveal_step

## Hypothesis

M1445 source-step candidates require explicit candidate-step column support before preflight or replay can produce meaningful evidence.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1445_forward_geometry_source_miner_smoke/summary.json, docs/m1445-paper-route-forward-geometry-source-miner-smoke.md
- parent_config: experiments/manifests/m1445-paper-route-forward-geometry-source-miner-smoke.json
- parent_objective: design source-step-aware preflight and replay support after M1445 selected source-step candidate rows
- derived_from: m1445-paper-route-forward-geometry-source-miner-smoke
- blocked_by: existing bounded relocation preflight and replay tools reconstruct at reveal_step while M1445 candidates are source_step anchored
- supersedes: running old reveal-step preflight directly on M1445 selected candidates
- invalidates: None

## Success Criteria

- docs/m1446-paper-route-source-step-preflight-support-design.md exists
- design preserves reveal_step lineage while adding candidate_step support
- design blocks old reveal-step preflight on M1445 source-step candidates
- design lists focused implementation tests
- no source preflight replay training PPO promotion private holdout corpus export or actor-input change occurs

## Failure Criteria

- design document is missing
- design overwrites reveal_step
- design routes directly to old reveal-step preflight
- design starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1446 must design source-step-aware preflight and replay support before any M1445 preflight or replay run
- M1446 must preserve reveal_step lineage while allowing source_step as candidate_step
- M1446 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source preflight
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not overwrite reveal_step with source_step in artifacts
- do not claim M1445 source rows are replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1446-paper-route-source-step-preflight-support-design
- type: gate
- checkpoint: docs/m1446-paper-route-source-step-preflight-support-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_step_preflight_support_design_admit_implementation
- reason: M1446 designs explicit candidate-step column support so source-step candidates are not evaluated at reveal_step

## Next Blocker

m1447-paper-route-source-step-preflight-support-implementation
