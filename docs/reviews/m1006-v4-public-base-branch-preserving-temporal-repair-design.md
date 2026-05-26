# m1006-v4-public-base-branch-preserving-temporal-repair-design Research Review

## Summary

- Generated at UTC: 20260526T174512Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: branch_preserving_temporal_repair_design_admit_m1007_evaluator
- Decision reason: M1006 designs actor_mean-only branch-preserving temporal repair using M997 temporal positives plus M267/M264 branch ceiling and separation terms before any update

## Hypothesis

A branch-preserving temporal repair design can combine M997 temporal sequence positives with M267/M264 wrong-history proof retention before any further actor update.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1005-v4-public-base-temporal-sequence-update-replay-failure-audit.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv
- parent_config: experiments/manifests/m1005-v4-public-base-temporal-sequence-update-replay-failure-audit.json
- parent_objective: design a branch-preserving temporal repair objective after M1004 proof washout
- derived_from: m1005-v4-public-base-temporal-sequence-update-replay-failure-audit, m1004-v4-public-base-temporal-sequence-update-public-replay-gate
- blocked_by: M1002 temporal objective improves exact metrics but lifts M267/M264 wrong-history rows 6 and 15
- supersedes: None
- invalidates: plain temporal actor_mean update without public proof branch retention, PPO from M1002 temporal candidates

## Success Criteria

- design document exists
- trainable parameters are pre-registered
- positive temporal targets and public proof-retention terms are separated
- exact, preflight, and stop gates are defined
- PPO and promotion remain blocked

## Failure Criteria

- design trains toward wrong-history degraded actions
- design changes actor inputs
- design skips M267/M264 rows 6 and 15
- design routes directly to PPO or promotion

## Evidence Gates

- M1006 must not run PPO
- M1006 must not promote
- M1006 must preserve P0 actor inputs
- M1006 must keep disrupted temporal histories contrast-only
- M1006 must define M267/M264 branch-retention gates before another actor update

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train toward wrong-history degraded actions
- do not add hidden labels or oracle feasibility to actor input
- do not choose lower alpha without a new objective
- do not run PPO
- do not use private holdout

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1006-v4-public-base-branch-preserving-temporal-repair-design
- type: infrastructure
- checkpoint: docs/m1006-v4-public-base-branch-preserving-temporal-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: branch_preserving_temporal_repair_design_admit_m1007_evaluator
- reason: M1006 designs actor_mean-only branch-preserving temporal repair using M997 temporal positives plus M267/M264 branch ceiling and separation terms before any update

## Next Blocker

m1007-v4-public-base-branch-preserving-temporal-repair-evaluator
