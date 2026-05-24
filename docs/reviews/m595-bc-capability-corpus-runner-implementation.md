# m595-bc-capability-corpus-runner-implementation Research Review

## Summary

- Generated at UTC: 20260524T073906Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_capability_corpus_runner_implementation_admit_export_smoke
- Decision reason: M595 implements corpus exporter and same-corpus pair mining with focused tests plus a 24-row 18-pair real smoke while preserving P0 actor inputs and labels-as-targets only

## Hypothesis

A closed-loop BC5660 capability corpus runner can align P0 observations, base action anchors, recurrent state diagnostics, future-response labels, and matched-current pair-ranking rows without actor-input leakage.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m594-bc-capability-repair-corpus-design.md
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: implement closed-loop capability corpus and matched-current pair runner after M594 design
- derived_from: m594-bc-capability-repair-corpus-design
- blocked_by: m594-bc-capability-repair-corpus-design
- supersedes: None
- invalidates: None

## Success Criteria

- implementation writes capability_corpus.npz pairs.csv summaries and metadata
- tests verify corpus arrays have expected shapes and exclude privileged actor inputs
- tests verify pair rows reference valid corpus row indices and target deltas
- tests verify future-response labels are stored as targets only
- research validation passes

## Failure Criteria

- implementation feeds capability labels into actor observations
- implementation writes invalid pair row indices
- implementation trains or promotes a checkpoint
- implementation lacks focused tests

## Evidence Gates

- implement corpus exporter and focused tests only
- store P0 observations anchors and training-only capability labels
- mine or export matched-current pair rows from the same corpus
- preserve no-oracle actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train repair model
- do not run PPO
- do not promote checkpoint
- do not add capability labels or hidden physical parameters to actor observations
- do not claim driver performance from corpus export

## Failure Taxonomy

- none

## Scoreboard

- milestone: m595-bc-capability-corpus-runner-implementation
- type: infrastructure
- checkpoint: runs/m595_bc_capability_corpus_pair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_corpus_runner_implementation_admit_export_smoke
- reason: M595 implements corpus exporter and same-corpus pair mining with focused tests plus a 24-row 18-pair real smoke while preserving P0 actor inputs and labels-as-targets only

## Next Blocker

m596-bc-capability-corpus-export-smoke
