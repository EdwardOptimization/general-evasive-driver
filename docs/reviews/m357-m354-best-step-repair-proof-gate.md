# m357-m354-best-step-repair-proof-gate Research Review

## Summary

- Generated at UTC: 20260523T110332Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_m354_best_step_proof_washout
- Decision reason: M357 rejects direct proof-gate acceptance because the M356 best-step candidate passes exact objectives but fails source-diverse 3/5 old-key 25/40 accepted and M267/M264 15/17 success-drop retention

## Hypothesis

The M356 best-step repaired M354 candidate may preserve exact, source-diverse, old-key neighborhood, and first replay proof gates that the original final-step M354 candidate could not reach.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- parent_dataset: runs/m356_m354_repair_best_step_probe/summary.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m356-exact-repair-best-step-selection-implementation.json, docs/m356-exact-repair-best-step-selection-implementation.md
- parent_objective: run proof gates skipped by M354 on the corrected best-step repaired candidate
- derived_from: m356-exact-repair-best-step-selection-implementation
- blocked_by: m356-exact-repair-best-step-selection-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- exact M297/M270 remain non-regressing versus M352
- source-diverse protected gates pass
- old-key neighborhood replay gate passes
- M183/M170 and M267/M264 first replay gates pass
- research validation passes

## Failure Criteria

- exact objectives regress
- source-diverse protected gate fails
- old-key neighborhood gate fails
- first replay gate fails
- actor input contract changes

## Evidence Gates

- no PPO run
- candidate retains exact M297/M270 no-regression versus M352
- source-diverse protected gate pass
- old-key neighborhood replay gate pass
- M183/M170 and M267/M264 first replay gates pass
- do not promote directly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from proof gate alone
- do not run full public behavior gates before proof gates pass
- do not change actor inputs
- do not relax exact or old-key thresholds

## Failure Taxonomy

- proof_washout
- protected_key_window_failure

## Scoreboard

- milestone: m357-m354-best-step-repair-proof-gate
- type: gate
- checkpoint: runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m354_best_step_proof_washout
- reason: M357 rejects direct proof-gate acceptance because the M356 best-step candidate passes exact objectives but fails source-diverse 3/5 old-key 25/40 accepted and M267/M264 15/17 success-drop retention

## Next Blocker

m358-m354-best-step-bounded-interpolation-probe
