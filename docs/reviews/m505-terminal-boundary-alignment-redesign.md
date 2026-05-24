# m505-terminal-boundary-alignment-redesign Research Review

## Summary

- Generated at UTC: 20260524T003939Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m506_terminal_boundary_aware_selector
- Decision reason: M505 shows low-margin rows are source-diverse but have smaller action perturbations so the next selector should filter terminal margin first with softer action thresholds

## Hypothesis

M504 failed because current mining selects capability/action ambiguity before terminal-boundary sensitivity; the next proof path should first mine or construct low-clearance normal-history boundary states, then test wrong-history action sensitivity there.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m504_boundary_action_sensitive_targeted_pair_triage/summary.json, runs/m504_boundary_action_sensitive_targeted_pair_triage/action_sensitive_candidates.csv, runs/m503_natural_boundary_pressure_matched_current_summary/combined_matched_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m504-boundary-action-sensitive-targeted-pair-triage.json
- parent_objective: terminal-boundary alignment redesign
- derived_from: m504-boundary-action-sensitive-targeted-pair-triage
- blocked_by: m504-boundary-action-sensitive-targeted-pair-triage
- supersedes: None
- invalidates: None

## Success Criteria

- summarize M504 terminal-boundary sparsity
- select a concrete next proof path
- define admission thresholds for low normal margin and source diversity
- state why the path is less artificial than hidden-hold forcing
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- redesign repeats M504 action-only triage unchanged
- redesign admits outcome gates on high-margin rows
- redesign relies on persistent wrong hidden as deployable proof
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- audit why M504 action-sensitive rows remain high-margin
- design a next proof path that starts from terminal-boundary-sensitive normal-history states
- pre-register whether to mine boundary anchors, project obstacle geometry, or redesign task distribution
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not run an outcome gate on high-margin M504 rows
- do not repeat action-only triage unchanged
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m505-terminal-boundary-alignment-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m506_terminal_boundary_aware_selector
- reason: M505 shows low-margin rows are source-diverse but have smaller action perturbations so the next selector should filter terminal margin first with softer action thresholds

## Next Blocker

M506 should implement and run a terminal-boundary-aware selector over the M504 candidate table.
