# m599-bc-capability-head-smoke-audit Research Review

## Summary

- Generated at UTC: 20260524T075358Z
- Type: gate
- Gate tier: process
- Promotion decision: bc_capability_head_smoke_audit_admit_belief_intervention_design
- Decision reason: M599 audits M598 as learnable hidden capability signal but not driver improvement and admits capability-belief intervention design before actor fine-tuning

## Hypothesis

Because M598 shows capability targets are learnable from frozen BC5660 hidden states, the next step should test whether the learned capability belief changes under wrong/delayed hidden interventions before actor fine-tuning.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m598_bc_capability_repair_head_only_smoke/summary.json, runs/m596_bc_capability_corpus_train_smoke/summary.json, runs/m596_bc_capability_corpus_validation_smoke/summary.json
- parent_config: docs/m597-bc-capability-repair-objective-smoke-design.md
- parent_objective: audit head-only capability smoke before actor or hidden fine-tuning
- derived_from: m598-bc-capability-repair-objective-smoke-implementation
- blocked_by: m598-bc-capability-repair-objective-smoke-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit clearly separates data/objective signal from driver improvement
- audit chooses the next branch and pre-registers blocker
- audit keeps PPO promotion and route claims blocked
- research validation passes

## Failure Criteria

- audit treats head-only loss improvement as driver improvement
- audit starts actor training
- audit skips behavior retention gates
- audit promotes a checkpoint

## Evidence Gates

- audit what M598 proves and does not prove
- decide whether capability-belief intervention design is needed before actor fine-tuning
- pre-register next validation gates before actor updates
- keep promotion and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in audit milestone
- do not run PPO
- do not promote checkpoint
- do not claim driver improvement from head-only objective loss
- do not skip action-retention and M591-style hidden-action gates before actor updates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m599-bc-capability-head-smoke-audit
- type: gate
- checkpoint: docs/m599-bc-capability-head-smoke-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_head_smoke_audit_admit_belief_intervention_design
- reason: M599 audits M598 as learnable hidden capability signal but not driver improvement and admits capability-belief intervention design before actor fine-tuning

## Next Blocker

m600-bc-capability-belief-intervention-probe-design
