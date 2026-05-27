# m1071-v4-public-base-medium-ppo-repair-projection-design Research Review

## Summary

- Generated at UTC: 20260527T081055Z
- Type: gate
- Gate tier: process
- Promotion decision: medium_ppo_repair_projection_design_route_to_failed_row_corpus_export
- Decision reason: M1071 designs projection-first repair and requires source-labeled failed-row corpus export before any optimizer or new PPO proposal

## Hypothesis

A post-PPO repair/projection design can convert the M1069 raw proposal into a testable candidate by making exact and family-intersection proof retention first-class acceptance constraints.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
- parent_dataset: docs/m1070-v4-public-base-medium-ppo-proof-washout-audit.md, runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json
- parent_config: configs/ppo_m1069_expanded_gate_medium_seed61069.json, experiments/manifests/m1070-v4-public-base-medium-ppo-proof-washout-audit.json
- parent_objective: design an exact post-PPO repair/projection path for the M1069 medium-ramp proof washout
- derived_from: m1070-v4-public-base-medium-ppo-proof-washout-audit
- blocked_by: M1070 classified M1069 as coupled exact/public/family/source proof washout while broad gates passed
- supersedes: None
- invalidates: running another medium PPO before designing exact proof projection, repairing only old row15/row16 while ignoring M1061 family-intersection failures

## Success Criteria

- design artifact exists
- design names base and raw proposal checkpoints
- design includes exact active-set constraints
- design includes old public replay failed rows
- design includes M1061 family-intersection failed rows
- design includes source-diverse failed rows
- design defines acceptance order and rollback conditions
- no PPO actor training promotion or private holdout occurs

## Failure Criteria

- design artifact is missing
- design omits M1061 family-intersection failed rows
- design omits exact active-set constraints
- design accepts a repaired checkpoint before proof gates
- PPO or actor training starts
- private holdout is used

## Evidence Gates

- M1071 must not run PPO
- M1071 must not train actor
- M1071 must not promote
- M1071 must not use private holdout
- M1071 must design a projection/repair path that includes exact active-set, old public replay, M1061 family-intersection, and source-diverse failed rows
- M1071 must define acceptance order before any projection probe

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train actor
- do not promote M1069
- do not use private holdout
- do not weaken proof gates
- do not design a repair that ignores family-intersection failed rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1071-v4-public-base-medium-ppo-repair-projection-design
- type: gate
- checkpoint: docs/m1071-v4-public-base-medium-ppo-repair-projection-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_repair_projection_design_route_to_failed_row_corpus_export
- reason: M1071 designs projection-first repair and requires source-labeled failed-row corpus export before any optimizer or new PPO proposal

## Next Blocker

m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export
