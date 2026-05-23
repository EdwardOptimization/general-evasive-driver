# m350-old-key-neighborhood-ppo-escalation-design Research Review

## Summary

- Generated at UTC: 20260523T102411Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m351_old_key_neighborhood_ppo_escalation_run
- Decision reason: M350 registers a short PPO proposal from M349 base with exact repair source-diverse protected old-key neighborhood and first replay gate order; no PPO run

## Hypothesis

After M349 promotion, the next PPO continuation should be designed around exact repair plus source-diverse and old-key-neighborhood proof retention before any training is run.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m349_full_public_gate_for_m335_a010/summary.json, runs/m348_m335_a010_probe/summary.json, runs/m347_old_key_alpha_sweep/summary.json
- parent_config: experiments/manifests/m349-full-public-gate-for-m335-a010.json, docs/m349-full-public-gate-for-m335-a010.md
- parent_objective: design the next PPO escalation from the M349 public-gate base under exact/source-diverse/old-key-neighborhood acceptance
- derived_from: m349-full-public-gate-for-m335-a010
- blocked_by: m349-full-public-gate-for-m335-a010
- supersedes: None
- invalidates: None

## Success Criteria

- a PPO escalation design document is written
- the design names the M349 base checkpoint
- the design registers exact repair and proof-gate ordering
- the design includes old-key neighborhood replay acceptance
- research validation passes

## Failure Criteria

- the design runs PPO before registration
- the design omits old-key neighborhood acceptance
- the design changes actor inputs
- the design treats singleton 9944 as the sole old-key veto again

## Evidence Gates

- design only; no PPO run
- preserve exact M297 and exact M270 as first-class gates
- preserve source-diverse protected gates
- preserve old-key neighborhood replay gate instead of singleton 9944 standalone veto
- preserve first replay and full public gate order
- preserve behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO before the acceptance stack is registered
- do not change actor inputs
- do not remove source-diverse protected gates
- do not remove the old-key neighborhood gate
- do not promote from design alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m350-old-key-neighborhood-ppo-escalation-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m351_old_key_neighborhood_ppo_escalation_run
- reason: M350 registers a short PPO proposal from M349 base with exact repair source-diverse protected old-key neighborhood and first replay gate order; no PPO run

## Next Blocker

m351-old-key-neighborhood-ppo-escalation-run
