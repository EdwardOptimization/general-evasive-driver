# m1070-v4-public-base-medium-ppo-proof-washout-audit Research Review

## Summary

- Generated at UTC: 20260527T080502Z
- Type: gate
- Gate tier: process
- Promotion decision: medium_ppo_proof_washout_audit_route_to_repair_projection_design
- Decision reason: M1070 audits M1069 as coupled exact active-set old public replay family-intersection and source-diverse proof washout with broad gates retained and routes to projection design

## Hypothesis

The M1069 medium PPO failure can be localized from existing artifacts without another training run, and the next repair path can be selected before any further PPO.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
- parent_dataset: runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json, runs/m1069_expanded_gate_medium_ppo_seed61069/exact_contract_summary.csv, runs/m1069_expanded_gate_medium_ppo_seed61069/proof_replay_summary.csv, runs/m1069_expanded_gate_medium_ppo_seed61069/family_intersection_summary.json, runs/m1069_expanded_gate_medium_ppo_seed61069/source_diverse_summary.json
- parent_config: configs/ppo_m1069_expanded_gate_medium_seed61069.json, experiments/manifests/m1069-v4-public-base-expanded-gate-medium-ppo-smoke.json
- parent_objective: audit the first expanded-gate 8192-step PPO proof washout before changing the PPO recipe
- derived_from: m1069-v4-public-base-expanded-gate-medium-ppo-smoke
- blocked_by: M1069 completed PPO but failed exact, public replay, family-intersection, and source-diverse proof gates while fresh/OOD and behavior gates passed
- supersedes: None
- invalidates: continuing to 8192-step fresh-seed repeats without localizing the M1069 proof washout, promoting the M1069 checkpoint from fresh/OOD or behavior retention alone

## Success Criteria

- audit artifact exists
- audit reports exact active-set failure details
- audit reports old public replay failed surfaces and failed rows
- audit reports M1061 family-intersection failed sources and failed rows
- audit reports source-diverse failed surfaces and failed rows
- audit distinguishes broad generalization/behavior retention from proof washout
- audit selects the next blocker without running PPO or using private holdout

## Failure Criteria

- audit artifact is missing
- audit omits family-intersection failure
- audit omits exact active-set failure
- audit recommends another PPO repeat without proof-washout localization
- PPO or actor training starts
- private holdout is used

## Evidence Gates

- M1070 must not run PPO
- M1070 must not train actor
- M1070 must not promote
- M1070 must not use private holdout
- M1070 must localize M1069 exact active-set, old public replay, family-intersection, and source-diverse failures
- M1070 must recommend audit/repair/projection next step before any new PPO proposal

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run another PPO proposal
- do not change actor inputs
- do not use private holdout
- do not promote M1069
- do not tune from broad fresh/OOD success while proof gates fail
- do not weaken M1061 family-intersection gate

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1070-v4-public-base-medium-ppo-proof-washout-audit
- type: gate
- checkpoint: docs/m1070-v4-public-base-medium-ppo-proof-washout-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_proof_washout_audit_route_to_repair_projection_design
- reason: M1070 audits M1069 as coupled exact active-set old public replay family-intersection and source-diverse proof washout with broad gates retained and routes to projection design

## Next Blocker

m1071-v4-public-base-medium-ppo-repair-projection-design
