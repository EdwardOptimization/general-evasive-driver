# m364-old-key-aware-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T114249Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m365_full_public_gate_for_m364_alpha01
- Decision reason: M364 alpha 0.1 from old-key-aware repair interpolation passes old-key source-diverse and first replay proof gates; direct repaired candidate fails old-key by one row and alpha 0.2 is first failing tested old-key alpha

## Hypothesis

Old-key-aware exact repair can generate a candidate that improves or preserves exact M297/M270 and old-key surrogate metrics without immediately requiring alpha 0.00025 clipping under old-key replay.

## Lineage

- parent_checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt, runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- parent_dataset: runs/m363_old_key_preference_corpus/old_key_preference_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m363-old-key-aware-repair-implementation.json
- parent_objective: probe whether old-key-aware exact repair can move beyond retention-only alpha while preserving proof gates
- derived_from: m363-old-key-aware-repair-implementation
- blocked_by: m363-old-key-aware-repair-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- old-key-aware repair candidate passes exact M297/M270 and old-key surrogate gates
- old-key targeted replay has zero accepted regressions or exposes a larger safe alpha than M358
- source-diverse and first replay gates are run if old-key replay passes
- failure is classified if the direction remains retention-only
- research validation passes

## Failure Criteria

- old-key-aware repair cannot move beyond base without exact or old-key surrogate regression
- old-key replay fails at the same micro-alpha scale as M358
- actor input contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression
- old-key surrogate no-regression
- old-key neighborhood targeted replay and replay-gate adapter
- source-diverse protected gates if old-key replay passes
- M183/M170 and M267/M264 first replay gates if proof gates pass
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote directly
- do not run PPO
- do not skip old-key targeted replay
- do not treat surrogate success as proof without replay
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m364-old-key-aware-repair-probe
- type: gate
- checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m365_full_public_gate_for_m364_alpha01
- reason: M364 alpha 0.1 from old-key-aware repair interpolation passes old-key source-diverse and first replay proof gates; direct repaired candidate fails old-key by one row and alpha 0.2 is first failing tested old-key alpha

## Next Blocker

m365-full-public-gate-for-m364-alpha01
