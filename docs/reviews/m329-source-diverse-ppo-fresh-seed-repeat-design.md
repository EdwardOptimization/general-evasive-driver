# m329-source-diverse-ppo-fresh-seed-repeat-design Research Review

## Summary

- Generated at UTC: 20260523T064614Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m330_source_diverse_ppo_fresh_seed_repeat
- Decision reason: M329 registers fresh-seed repeat config from M328 base with exact repair plus source-diverse protected gates plus old-key diagnostic plus first replay gates; no PPO run

## Hypothesis

After M328 promotes one source-diverse protected smoke PPO result, the workflow should repeat the same smoke process with a fresh seed before any longer PPO escalation.

## Lineage

- parent_checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
- parent_dataset: runs/m328_full_public_gate_for_m327_repaired/full_gates, runs/m328_source_diverse_protected_gate/summary.json, runs/m328_m327_repaired_exact_eval_vs_m325/summary.json
- parent_config: experiments/manifests/m328-full-public-gate-for-m327-source-diverse-repaired.json, docs/m328-full-public-gate-for-m327-source-diverse-repaired.md
- parent_objective: design a fresh-seed source-diverse protected PPO repeat from M328 base before lengthening PPO
- derived_from: m328-full-public-gate-for-m327-source-diverse-repaired
- blocked_by: m328-full-public-gate-for-m327-source-diverse-repaired
- supersedes: None
- invalidates: None

## Success Criteria

- design names M328 checkpoint as base
- design registers a fresh-seed smoke PPO config only
- design requires exact repair before replay gates
- design requires source-diverse protected gate before full public promotion
- design keeps 9944 diagnostic reporting
- no PPO is run

## Failure Criteria

- design skips fresh-seed repeat
- design skips exact repair
- design treats first gates as promotion
- design deletes 9944 diagnostic
- design changes actor inputs
- M329 runs PPO

## Evidence Gates

- do not run PPO in M329
- preserve human-view actor input contract
- register fresh optimizer/PPO seed
- register exact repair command
- register source-diverse protected gates
- register old-key diagnostic classification
- define first replay and full public gate escalation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lengthen PPO before fresh-seed repeat
- do not run PPO before the repeat design is committed
- do not remove source-diverse protected gates
- do not delete 9944 diagnostic
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m329-source-diverse-ppo-fresh-seed-repeat-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m330_source_diverse_ppo_fresh_seed_repeat
- reason: M329 registers fresh-seed repeat config from M328 base with exact repair plus source-diverse protected gates plus old-key diagnostic plus first replay gates; no PPO run

## Next Blocker

m330-source-diverse-ppo-fresh-seed-repeat
