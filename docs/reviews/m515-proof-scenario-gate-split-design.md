# m515-proof-scenario-gate-split-design Research Review

## Summary

- Generated at UTC: 20260524T014449Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m516_boundary_mechanism_projection_selector
- Decision reason: M515 pre-registers a split where terminal-boundary mechanism proof uses source config target geometry diversity while broad scenario-label diversity is evaluated by a separate scenario distribution gate

## Hypothesis

Because M514 confirms projected scenario labels and terminal-boundary low margins are structurally separated, proof admission should use geometry/source diversity while scenario-label diversity moves to a separate distribution gate.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m514_projected_label_margin_conflict_audit/summary.json, runs/m514_projected_label_margin_conflict_audit/label_margin_summary.csv, runs/m514_projected_label_margin_conflict_audit/margin_bucket_summary.csv
- parent_config: experiments/manifests/m514-projected-label-margin-conflict-audit.json
- parent_objective: proof/scenario gate split design
- derived_from: m514-projected-label-margin-conflict-audit
- blocked_by: m514-projected-label-margin-conflict-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define mechanism proof gate criteria
- define scenario distribution gate criteria
- state what M516 should implement
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design treats the split as a post-hoc success of M512
- design removes diversity requirements instead of moving label diversity to a separate gate
- design uses labels as actor inputs
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- pre-register mechanism proof gate separate from scenario-label distribution gate
- define geometry/source diversity requirements for terminal-boundary proof rows
- define broad scenario distribution evidence as a separate gate
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim mechanism rows prove scenario-label generalization
- do not use scenario labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m515-proof-scenario-gate-split-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m516_boundary_mechanism_projection_selector
- reason: M515 pre-registers a split where terminal-boundary mechanism proof uses source config target geometry diversity while broad scenario-label diversity is evaluated by a separate scenario distribution gate

## Next Blocker

M516 should implement a boundary mechanism projection selector over M514 scored rows.
