# m1112-v4-public-base-materialized-actor-update-full-public-gate Research Review

## Summary

- Generated at UTC: 20260527T203602Z
- Type: gate
- Gate tier: proof
- Promotion decision: materialized_actor_update_full_public_gate_reject_proof_washout
- Decision reason: M1112 exact M1107 and contract pass but expanded full public gate rejects m1110_110901: proof old replay 3/6 family-intersection 0/3 source-diverse 0/3 while fresh/OOD and behavior pass

## Hypothesis

The M1110 primary candidate can retain exact, proof, source-diverse, fresh/OOD, and behavior gates without PPO or private holdout.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt
- parent_dataset: docs/m1111-v4-public-base-materialized-actor-update-full-public-gate-design.md, runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz, runs/m1110_materialized_actor_update_exact_eval/summary.json
- parent_config: experiments/manifests/m1111-v4-public-base-materialized-actor-update-full-public-gate-design.json
- parent_objective: run exact M1107 recheck and expanded full public gate for the M1110 primary candidate
- derived_from: m1111-v4-public-base-materialized-actor-update-full-public-gate-design
- blocked_by: M1111 design required before replay/full public gate
- supersedes: None
- invalidates: promotion before full public gate, PPO continuation before full public gate, candidate switching after failed gate without audit

## Success Criteria

- exact M1107 recheck completes
- expanded full public gate completes
- summary artifacts exist
- actor inputs are unchanged
- allowed changed-parameter surface passes
- exact gate passes
- old public replay gates pass
- M1061 family-intersection gate passes
- source-diverse gate passes
- fresh/OOD gates pass
- behavior gates pass
- no training, PPO, promotion, or private holdout occurs

## Failure Criteria

- exact M1107 recheck fails
- expanded full public gate crashes
- summary artifact is missing
- actor inputs change
- allowed changed-parameter surface fails
- any exact/proof/family/source/generalization/behavior gate fails
- training, PPO, promotion, or private holdout occurs

## Evidence Gates

- M1112 must not train actor weights
- M1112 must not run PPO
- M1112 must not promote
- M1112 must not use private holdout
- M1112 must preserve actor inputs
- M1112 must rerun exact M1107 objective for selected candidate
- M1112 must run expanded full public gate for selected candidate
- M1112 must not switch candidate after failure

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip exact M1107 check
- do not skip old public replay or family-intersection gates
- do not switch candidate after seeing gate outcome

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1112-v4-public-base-materialized-actor-update-full-public-gate
- type: gate
- checkpoint: runs/m1112_materialized_actor_update_full_public_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_actor_update_full_public_gate_reject_proof_washout
- reason: M1112 exact M1107 and contract pass but expanded full public gate rejects m1110_110901: proof old replay 3/6 family-intersection 0/3 source-diverse 0/3 while fresh/OOD and behavior pass

## Next Blocker

m1113-v4-public-base-materialized-actor-update-proof-washout-audit
