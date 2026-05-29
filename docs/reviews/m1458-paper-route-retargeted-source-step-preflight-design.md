# m1458-paper-route-retargeted-source-step-preflight-design Research Review

## Summary

- Generated at UTC: 20260529T044555Z
- Type: gate
- Gate tier: process
- Promotion decision: retargeted_source_step_preflight_design_admit_smoke
- Decision reason: M1458 designs a source-step preflight-only validation over M1457 retarget candidates before any bounded replay training promotion or corpus export

## Hypothesis

M1457 retarget candidates justify one preflight-only validation run before any bounded replay or corpus export.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1457_source_step_boundary_retarget_smoke/retarget_candidate_rows.csv, runs/m1457_source_step_boundary_retarget_smoke/summary.json, docs/m1457-paper-route-source-step-boundary-retarget-smoke.md
- parent_config: experiments/manifests/m1457-paper-route-source-step-boundary-retarget-smoke.json
- parent_objective: design retargeted source-step preflight smoke after M1457 proposal gate passes
- derived_from: m1457-paper-route-source-step-boundary-retarget-smoke
- blocked_by: retarget candidates have not yet been reconstructed by source-step preflight
- supersedes: direct bounded replay from unvalidated retarget candidates
- invalidates: None

## Success Criteria

- docs/m1458-paper-route-retargeted-source-step-preflight-design.md exists
- design command uses --candidate-step-column source_step
- design blocks bounded replay training PPO promotion private holdout corpus export and actor-input changes
- design routes to preflight result audit or bounded replay design depending on M1459 outcome

## Failure Criteria

- design document is missing
- design uses reveal_step for source-step candidates
- design claims retarget proposals are replay evidence
- design starts source preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1458 must design preflight-only validation before bounded replay
- M1458 must require candidate_step_column source_step
- M1458 must block bounded replay training PPO promotion private holdout corpus export and actor-input changes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source preflight in this design milestone
- do not run bounded replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not count retarget proposals as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1458-paper-route-retargeted-source-step-preflight-design
- type: gate
- checkpoint: docs/m1458-paper-route-retargeted-source-step-preflight-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: retargeted_source_step_preflight_design_admit_smoke
- reason: M1458 designs a source-step preflight-only validation over M1457 retarget candidates before any bounded replay training promotion or corpus export

## Next Blocker

m1459-paper-route-retargeted-source-step-preflight-smoke
