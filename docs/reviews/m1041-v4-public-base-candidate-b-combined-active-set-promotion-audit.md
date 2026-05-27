# m1041-v4-public-base-candidate-b-combined-active-set-promotion-audit Research Review

## Summary

- Generated at UTC: 20260527T014209Z
- Type: gate
- Gate tier: promotion
- Promotion decision: candidate_b_combined_active_set_promote_public_gate_base
- Decision reason: M1041 promotes the M1038 selected checkpoint as current public-gate base after M1040 full public gate pass; scope remains public-gate only

## Hypothesis

The M1038 selected checkpoint should replace Candidate B as the current public-gate base if M1040 evidence is complete and promotion remains scoped to public-gate status.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- parent_dataset: runs/m1040_candidate_b_combined_active_set_full_public_gate/summary.json, docs/m1040-v4-public-base-candidate-b-combined-active-set-full-public-gate.md
- parent_config: experiments/manifests/m1040-v4-public-base-candidate-b-combined-active-set-full-public-gate.json
- parent_objective: audit whether the M1038 combined active-set candidate should replace Candidate B as the current public-gate base
- derived_from: m1040-v4-public-base-candidate-b-combined-active-set-full-public-gate
- blocked_by: M1040 classifies the M1038 selected checkpoint as a full public-gate candidate but does not promote
- supersedes: None
- invalidates: using the M1038 selected checkpoint as the public base before explicit promotion audit

## Success Criteria

- promotion audit artifact exists
- M1038 and M1040 evidence are summarized
- promotion decision is explicit
- current-status and scoreboard lineage are updated if promoted
- PPO, private holdout, and paper-level claims remain blocked

## Failure Criteria

- promotion decision is missing
- promotion occurs without current-status update
- private holdout is used
- PPO starts
- paper-level generalization is claimed

## Evidence Gates

- M1041 must audit M1038 and M1040 evidence
- M1041 must decide promote or reject for public-gate base status
- M1041 must not train or run PPO
- M1041 must not use private holdout
- M1041 must preserve actor input contract
- M1041 must scope any promotion to public-gate base status only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not change actor inputs
- do not use private holdout
- do not promote without updating current status and scoreboard lineage
- do not claim paper-level generalization
- do not claim long-run PPO stability

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1041-v4-public-base-candidate-b-combined-active-set-promotion-audit
- type: driver_candidate
- checkpoint: runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_combined_active_set_promote_public_gate_base
- reason: M1041 promotes the M1038 selected checkpoint as current public-gate base after M1040 full public gate pass; scope remains public-gate only

## Next Blocker

m1042-v4-public-base-combined-active-set-post-promotion-synthesis
