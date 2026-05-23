# m332-m330-old-key-gap-bounded-interpolation-probe Research Review

## Summary

- Generated at UTC: 20260523T070136Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m333_full_public_gate_for_m332_a045
- Decision reason: M332 selects alpha 0.45 as largest old-key-gap-floor-passing interpolation with exact/source-diverse and first replay gates passing; no promotion

## Hypothesis

Interpolating from M328 base toward the M330 repaired candidate may recover useful exact/source-diverse improvement while keeping the old-key margin gap above the 0.09 diagnostic floor.

## Lineage

- parent_checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt, runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
- parent_dataset: runs/m331_m330_old_key_gap_floor_audit/summary.json, runs/m330_source_diverse_protected_gate/summary.json, runs/m330_critical_key_seed9944/guard_results.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m331-m330-old-key-gap-floor-failure-audit.json, docs/m331-m330-old-key-gap-floor-failure-audit.md
- parent_objective: probe whether the useful M330 exact/source-diverse direction can be accepted inside an old-key gap-bounded trust region
- derived_from: m331-m330-old-key-gap-floor-failure-audit
- blocked_by: m331-m330-old-key-gap-floor-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- interpolation checkpoints are generated
- one or more nonzero alphas pass exact M297/M270 no-regression
- one or more nonzero alphas pass source-diverse protected gates
- one or more nonzero alphas retain old-key margin_gap >= 0.09
- selected alpha passes M183/M170 and M267/M264 first replay gates
- actor input contract remains unchanged

## Failure Criteria

- no nonzero alpha passes exact objectives
- no nonzero alpha passes source-diverse protected gates
- no nonzero alpha retains old-key margin gap floor
- first replay gate fails for the selected alpha
- actor observation inputs change

## Evidence Gates

- do not run PPO
- interpolate M328 base to M330 repaired
- exact M297 and exact M270 no-regression versus M328
- source-diverse protected replay bundle passes
- old 9944 margin gap remains at least 0.09
- M183/M170 first replay gate versus M328
- M267/M264 first replay gate versus M328
- no promotion in M332

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower the old-key floor
- do not promote from M332
- do not run PPO
- do not skip source-diverse protected gates
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m332-m330-old-key-gap-bounded-interpolation-probe
- type: driver_candidate
- checkpoint: runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m333_full_public_gate_for_m332_a045
- reason: M332 selects alpha 0.45 as largest old-key-gap-floor-passing interpolation with exact/source-diverse and first replay gates passing; no promotion

## Next Blocker

m333-full-public-gate-for-m332-a045
