# m539-matched-history-seed-fragility-audit Research Review

## Summary

- Generated at UTC: 20260524T033554Z
- Type: gate
- Gate tier: proof
- Promotion decision: seed3531_l2_counterexample_broad_admit_m540_training_variance_design
- Decision reason: M539 shows seed3531 L2-over-L3 counterexample is broad across public surfaces targets and offsets with 31 L2-completed to L3-collision regressions

## Hypothesis

The M538 L3-vs-L2 seed-3531 counterexample can be localized to specific surfaces, offsets, targets, or action/terminal patterns before deciding whether the next step should be longer matched training or finite-window baseline escalation.

## Lineage

- parent_checkpoint: runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt
- parent_dataset: runs/m538_natural_surface_paired_advantage_audit/paired_deltas.csv, runs/m537_full_public_eval_m497_short_reveal/surface_outcomes.csv, runs/m537_full_public_eval_m497_warmup_capability/surface_outcomes.csv, runs/m537_full_public_eval_m487_near_threshold/surface_outcomes.csv, runs/m537_full_public_eval_m487_late_high_energy/surface_outcomes.csv
- parent_config: experiments/manifests/m538-natural-surface-paired-advantage-audit.json
- parent_objective: diagnose L3-vs-L2 seed-3531 public paired counterexample
- derived_from: m538-natural-surface-paired-advantage-audit
- blocked_by: m538-natural-surface-paired-advantage-audit
- supersedes: None
- invalidates: None

## Success Criteria

- seed-3531 negative L3-L2 rows are summarized by surface target tail offset and terminal reason
- first-action differences are reported for the largest negative margin rows
- event versus non-event contribution is reported
- a concrete next decision is selected without training or promotion
- research validation passes

## Failure Criteria

- seed-3531 rows cannot be joined back to outcomes
- diagnostic treats public rows as private holdout
- checkpoint promotion is performed

## Evidence Gates

- isolated seed-3531 L2-over-L3 rows by surface target and tail offset
- compared first-action and terminal-reason differences on negative L3-L2 deltas
- checked whether seed-3531 counterexample concentrates on event rows or broad rows
- did not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune L3 using seed-3531 rows
- do not hide L2 counterexample when reporting M537/M538
- do not promote any baseline from public diagnostic rows

## Failure Taxonomy

- seed_fragility

## Scoreboard

- milestone: m539-matched-history-seed-fragility-audit
- type: gate
- checkpoint: runs/m539_matched_history_seed_fragility_audit/summary.json
- success_rate: -0.013815
- termination_rate: None
- clearance_margin_mean: -0.143703
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: seed3531_l2_counterexample_broad_admit_m540_training_variance_design
- reason: M539 shows seed3531 L2-over-L3 counterexample is broad across public surfaces targets and offsets with 31 L2-completed to L3-collision regressions

## Next Blocker

m540-matched-history-training-variance-design
