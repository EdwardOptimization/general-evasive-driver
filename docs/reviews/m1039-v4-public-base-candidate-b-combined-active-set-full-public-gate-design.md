# m1039-v4-public-base-candidate-b-combined-active-set-full-public-gate-design Research Review

## Summary

- Generated at UTC: 20260527T005945Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_combined_active_set_full_public_gate_design_admit_m1040_gate
- Decision reason: M1039 designs full public proof generalization behavior gate for the M1038 selected checkpoint and keeps promotion blocked until M1040 result

## Hypothesis

The M1038 selected checkpoint should be evaluated by a full public proof/generalization/behavior gate before any promotion decision.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- parent_dataset: docs/m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe.md, runs/m1038_candidate_b_combined_active_set_repair_projection_probe/summary.json
- parent_config: experiments/manifests/m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe.json
- parent_objective: design full public proof/generalization/behavior gate for the M1038 first-replay candidate
- derived_from: m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe
- blocked_by: M1038 produced a first-replay candidate but not a full public-gate result
- supersedes: None
- invalidates: promoting the M1038 selected checkpoint before full public gates, claiming broad driver improvement from first-replay-only evidence

## Success Criteria

- design artifact exists
- selected checkpoint is named
- baseline Candidate B checkpoint is named
- proof replay surfaces are named
- fresh public and moderate-OOD checks are named
- behavior seeds are named
- promotion remains blocked until implementation result

## Failure Criteria

- design omits selected checkpoint
- design omits old replay surfaces
- design uses private holdout
- design changes actor inputs
- design promotes the candidate

## Evidence Gates

- M1039 must run no PPO
- M1039 must not promote
- M1039 must not use private holdout
- M1039 must preserve P0 actor inputs
- M1039 must design six-surface replay gates
- M1039 must include fresh public and moderate-OOD checks
- M1039 must include behavior seeds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not change actor inputs
- do not skip old replay surfaces
- do not skip fresh public or OOD checks
- do not use private holdout
- do not claim paper-level evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1039-v4-public-base-candidate-b-combined-active-set-full-public-gate-design
- type: gate
- checkpoint: docs/m1039-v4-public-base-candidate-b-combined-active-set-full-public-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_combined_active_set_full_public_gate_design_admit_m1040_gate
- reason: M1039 designs full public proof generalization behavior gate for the M1038 selected checkpoint and keeps promotion blocked until M1040 result

## Next Blocker

m1040-v4-public-base-candidate-b-combined-active-set-full-public-gate
