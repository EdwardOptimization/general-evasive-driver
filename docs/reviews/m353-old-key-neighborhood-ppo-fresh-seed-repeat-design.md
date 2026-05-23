# m353-old-key-neighborhood-ppo-fresh-seed-repeat-design Research Review

## Summary

- Generated at UTC: 20260523T104215Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m354_old_key_neighborhood_ppo_fresh_seed_repeat
- Decision reason: M353 registers a fresh-seed short PPO repeat from M352 base with exact repair source-diverse protected old-key neighborhood and first replay gate order; no PPO run

## Hypothesis

After M352 promotion, the next step should be a fresh-seed repeat of the short PPO proposal under the same exact/source-diverse/old-key-neighborhood acceptance stack before any longer PPO escalation.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m352_full_public_gate_for_m351_a0075/summary.json, runs/m351_old_key_neighborhood_ppo_escalation/summary.json
- parent_config: experiments/manifests/m352-full-public-gate-for-m351-a0075.json, docs/m352-full-public-gate-for-m351-a0075.md
- parent_objective: design a fresh-seed repeat from the M352 public-gate base before longer PPO
- derived_from: m352-full-public-gate-for-m351-a0075
- blocked_by: m352-full-public-gate-for-m351-a0075
- supersedes: None
- invalidates: None

## Success Criteria

- fresh-seed repeat design document is written
- repeat config names the M352 base checkpoint
- gate order remains exact repair, source-diverse, old-key neighborhood, first replay, full public gate
- research validation passes

## Failure Criteria

- the design runs PPO before registration
- the design omits old-key neighborhood acceptance
- the design changes actor inputs
- the design admits longer PPO before repeat

## Evidence Gates

- design only; no PPO run
- fresh PPO seed required before longer PPO
- preserve exact M297/M270 repair
- preserve source-diverse protected gates
- preserve old-key neighborhood replay gate
- preserve first replay before full public gate order

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lengthen PPO before fresh-seed repeat
- do not run PPO before manifest/config registration
- do not change actor inputs
- do not remove old-key neighborhood gate
- do not promote from design alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m353-old-key-neighborhood-ppo-fresh-seed-repeat-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m354_old_key_neighborhood_ppo_fresh_seed_repeat
- reason: M353 registers a fresh-seed short PPO repeat from M352 base with exact repair source-diverse protected old-key neighborhood and first replay gate order; no PPO run

## Next Blocker

m354-old-key-neighborhood-ppo-fresh-seed-repeat
