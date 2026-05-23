# m326-source-diverse-protected-ppo-proposal-design Research Review

## Summary

- Generated at UTC: 20260523T063108Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m327_source_diverse_protected_ppo_proposal_smoke
- Decision reason: M326 registers M327 smoke PPO from M325 base with exact repair plus three source-diverse protected gates plus old-key diagnostic plus first replay gates; no PPO run

## Hypothesis

After M325 promotes the M316 repaired endpoint under source-diverse protected policy, the next PPO proposal should be designed around M325 as base, exact M297/M270 repair, source-diverse protected acceptance, old-key diagnostic classification, and staged replay/behavior gates.

## Lineage

- parent_checkpoint: runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- parent_dataset: runs/m325_full_public_gate_for_m316_repaired/full_gates, runs/m325_source_diverse_policy_gate/summary.json, runs/m325_m316_repaired_exact_eval_vs_m317/summary.json
- parent_config: experiments/manifests/m325-source-diverse-policy-full-gate-for-m316-repaired.json, docs/m325-source-diverse-policy-full-gate-for-m316-repaired.md, docs/m324-single-key-window-override-policy-design.md
- parent_objective: design the next PPO proposal from M325 base with mandatory exact repair and source-diverse protected acceptance
- derived_from: m325-source-diverse-policy-full-gate-for-m316-repaired
- blocked_by: m325-source-diverse-policy-full-gate-for-m316-repaired
- supersedes: None
- invalidates: None

## Success Criteria

- design names M325 checkpoint as base
- design registers a smoke-scale PPO proposal only
- design requires exact repair before replay gates
- design requires source-diverse protected gate before full public promotion
- design keeps 9944 diagnostic reporting
- no PPO is run

## Failure Criteria

- design skips exact repair
- design treats source-diverse pass as promotion
- design deletes 9944 diagnostic
- design changes actor inputs
- M326 runs PPO

## Evidence Gates

- do not run PPO in M326
- preserve human-view actor input contract
- register PPO smoke config from M325 base
- register exact repair command
- register source-diverse protected acceptance gate
- register old 9944 diagnostic classification
- define first replay and full public gate escalation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO before the design is committed
- do not remove source-diverse protected gates
- do not delete 9944 diagnostic
- do not change actor inputs
- do not lengthen PPO before a smoke repeat passes

## Failure Taxonomy

- none

## Scoreboard

- milestone: m326-source-diverse-protected-ppo-proposal-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m327_source_diverse_protected_ppo_proposal_smoke
- reason: M326 registers M327 smoke PPO from M325 base with exact repair plus three source-diverse protected gates plus old-key diagnostic plus first replay gates; no PPO run

## Next Blocker

m327-source-diverse-protected-ppo-proposal-smoke
