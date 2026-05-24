# m518-projection-aware-boundary-outcome-gate Research Review

## Summary

- Generated at UTC: 20260524T021200Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_invalid_projection_replay
- Decision reason: M518 implements projection-aware replay and preserves relocated geometry but rejects the formal gate because tail offset 8 is missing left-tail snapshots for all 239 input rows

## Hypothesis

Projection-aware replay of M516 terminal-boundary rows can determine whether one-shot wrong-history affects near-boundary outcomes before current feedback corrects belief mismatch.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv, runs/m516_boundary_mechanism_projection_selector/summary.json
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m517-projection-aware-boundary-outcome-gate-design.json
- parent_objective: projection-aware boundary outcome gate
- derived_from: m517-projection-aware-boundary-outcome-gate-design
- blocked_by: m517-projection-aware-boundary-outcome-gate-design
- supersedes: None
- invalidates: None

## Success Criteria

- projection-aware outcome gate implementation runs on M516 targeted rows
- relocated obstacle geometry is preserved during replay
- wrong-history and reset/zero controls are summarized separately
- source/target/config/geometry diversity is reported
- result classification is explicit
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- too many rows fail snapshot reconstruction or relocation
- gate uses original obstacle geometry instead of projected geometry
- summary cannot separate wrong-history from reset/zero controls
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- replay M516 targeted rows while preserving projected obstacle geometry
- report wrong-history proof rows and reset/zero controls
- classify positive proof, margin-only signal, control-only sensitivity, fast correction, or invalid replay
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not replay original obstacle geometry for projected rows
- do not use hidden-hold variants as deployable proof
- do not count reset or zero-current controls as wrong-history proof

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m518-projection-aware-boundary-outcome-gate
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_invalid_projection_replay
- reason: M518 implements projection-aware replay and preserves relocated geometry but rejects the formal gate because tail offset 8 is missing left-tail snapshots for all 239 input rows

## Next Blocker

M519 should redesign the projection outcome gate with valid tail offsets after M518 finds offset 8 invalid for all input rows.
