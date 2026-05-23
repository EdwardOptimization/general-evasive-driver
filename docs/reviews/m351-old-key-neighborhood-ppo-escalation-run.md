# m351-old-key-neighborhood-ppo-escalation-run Research Review

## Summary

- Generated at UTC: 20260523T103224Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m352_full_public_gate_for_m351_a0075
- Decision reason: M351 raw PPO plus exact repair produces strong endpoint objective gains but endpoint fails proof gates; bounded alpha 0.0075 passes exact source-diverse old-key neighborhood and first replay gates

## Hypothesis

A short PPO proposal from the M349 public base may yield an exact-repair candidate that preserves source-diverse proof and old-key neighborhood proof before first replay gates.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m349_full_public_gate_for_m335_a010/summary.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m351_old_key_neighborhood_escalation.json, experiments/manifests/m350-old-key-neighborhood-ppo-escalation-design.json, docs/m350-old-key-neighborhood-ppo-escalation-design.md
- parent_objective: run short PPO proposal from M349 base with exact repair and old-key neighborhood acceptance
- derived_from: m350-old-key-neighborhood-ppo-escalation-design
- blocked_by: m350-old-key-neighborhood-ppo-escalation-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO completes as proposal-only
- exact repair candidate does not regress exact M297/M270 versus M349
- selected candidate passes source-diverse protected gates
- selected candidate passes old-key neighborhood replay gate
- selected candidate passes M183/M170 and M267/M264 first replay gates
- research validation passes

## Failure Criteria

- raw PPO cannot run
- exact repair regresses M297 or M270
- source-diverse protected gate fails
- old-key neighborhood gate fails without a passing interpolation
- first replay gate fails
- actor input contract changes

## Evidence Gates

- raw PPO is proposal-only
- exact M297 and exact M270 no-regression versus M349
- source-diverse protected gate pass
- old-key neighborhood replay gate pass
- M183/M170 and M267/M264 first replay gates pass before any full public gate
- do not promote directly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote raw PPO
- do not skip exact repair
- do not skip old-key neighborhood targeted replay
- do not use singleton 9944 as the only old-key gate
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m351-old-key-neighborhood-ppo-escalation-run
- type: driver_candidate
- checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m352_full_public_gate_for_m351_a0075
- reason: M351 raw PPO plus exact repair produces strong endpoint objective gains but endpoint fails proof gates; bounded alpha 0.0075 passes exact source-diverse old-key neighborhood and first replay gates

## Next Blocker

m352-full-public-gate-for-m351-a0075
