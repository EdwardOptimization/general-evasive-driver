# m519-valid-offset-projection-outcome-redesign Research Review

## Summary

- Generated at UTC: 20260524T021200Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m520_valid_offset_projection_outcome_gate
- Decision reason: M519 keeps the same projection-aware semantics and pre-registers a valid-offset rerun with tail offsets 0 2 4 before interpreting wrong-history outcome effects

## Hypothesis

M518 failed because the pre-registered offset set included an invalid late tail offset for near-terminal left snapshots; rerunning the same projection-aware gate with valid offsets can produce an interpretable outcome classification.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m518_projection_aware_boundary_outcome_gate/summary.json, runs/m518_projection_aware_boundary_outcome_gate/projected_invalid_pairs.csv, runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv
- parent_config: experiments/manifests/m517-projection-aware-boundary-outcome-gate-design.json, experiments/manifests/m518-projection-aware-boundary-outcome-gate.json
- parent_objective: valid-offset projection-aware outcome gate redesign
- derived_from: m518-projection-aware-boundary-outcome-gate
- blocked_by: m518-projection-aware-boundary-outcome-gate
- supersedes: None
- invalidates: None

## Success Criteria

- identify the M518 invalid offset pattern
- pre-register the valid offset set for M520
- preserve projection-aware replay semantics
- define how M520 should classify fast correction versus margin-only or positive proof
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- redesign treats M518 invalid replay as controller failure
- redesign changes actor inputs
- redesign changes obstacle projection semantics
- redesign omits invalid-tail reporting
- training or checkpoint promotion is performed

## Evidence Gates

- design a valid-offset rerun of the projection-aware boundary outcome gate
- preserve M517 relocated-obstacle replay semantics
- do not reinterpret M518 invalid replay as controller failure
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not silently change M518 results
- do not reuse original obstacle geometry for projected rows
- do not count reset or zero-current controls as wrong-history proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m519-valid-offset-projection-outcome-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m520_valid_offset_projection_outcome_gate
- reason: M519 keeps the same projection-aware semantics and pre-registers a valid-offset rerun with tail offsets 0 2 4 before interpreting wrong-history outcome effects

## Next Blocker

M520 should rerun the projection-aware boundary outcome gate with tail offsets 0,2,4.
