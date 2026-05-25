# m843-v4-source-diverse-sequence-effective-corpus-design Research Review

## Summary

- Generated at UTC: 20260525T125056Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_diverse_sequence_effective_corpus_design_admit_m844
- Decision reason: M843 designs no-training source-diverse sequence-effective corpus refresh with accepted-row diversity gates and source-aware train eval holdout splits before any objective training PPO or promotion

## Hypothesis

A source-diverse sequence-effective corpus design can convert M841's sparse-positive controllability evidence into a broader training/evaluation surface before outcome-coupled objectives.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m842-v4-low-margin-new-data-route-third-branch-synthesis.md, runs/m841_v4_near_boundary_sequence_effectiveness_probe/summary.json, runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv, runs/m841_v4_near_boundary_sequence_effectiveness_probe/diversity_summary.json
- parent_config: experiments/manifests/m842-v4-low-margin-new-data-route-third-branch-synthesis.json
- parent_objective: design source-diverse sequence-effective corpus refresh after M841 sparse-positive controllability
- derived_from: m842-v4-low-margin-new-data-route-third-branch-synthesis
- blocked_by: M841 sequence-effective rows are positive but source-concentrated
- supersedes: None
- invalidates: None

## Success Criteria

- M843 writes a design document for source-diverse sequence-effective corpus refresh
- M843 defines source diversity and accepted-row gates
- M843 specifies required implementation artifacts
- M843 keeps direct sequence override evidence separate from learned self-ID proof
- M843 keeps PPO and promotion blocked

## Failure Criteria

- M843 admits PPO or promotion
- M843 trains actor or residual parameters
- M843 treats direct sequence override success as learned policy proof
- M843 ignores M841 source concentration

## Evidence Gates

- M843 must remain design-only
- M843 must define source-diverse sequence-effective mining targets
- M843 must keep direct sequence override evidence separate from learned policy self-ID evidence
- M843 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M843
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat M841 direct sequence overrides as learned self-ID proof
- do not relax M841 diversity thresholds after seeing the result

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m843-v4-source-diverse-sequence-effective-corpus-design
- type: infrastructure
- checkpoint: docs/m843-v4-source-diverse-sequence-effective-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_sequence_effective_corpus_design_admit_m844
- reason: M843 designs no-training source-diverse sequence-effective corpus refresh with accepted-row diversity gates and source-aware train eval holdout splits before any objective training PPO or promotion

## Next Blocker

M841 sequence-effective evidence is positive but source-concentrated
