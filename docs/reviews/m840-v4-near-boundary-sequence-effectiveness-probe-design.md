# m840-v4-near-boundary-sequence-effectiveness-probe-design Research Review

## Summary

- Generated at UTC: 20260525T123224Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: near_boundary_sequence_effectiveness_probe_design_admit_m841
- Decision reason: M840 designs no-training short-horizon sequence override probe using hold steps 2 4 6 and bounded per-step deltas; direct sequence evidence remains controllability-only and M841 implementation is admitted

## Hypothesis

A short-horizon direct action-sequence override design can test whether M832 near-boundary terminal margins are sensitive to sustained action intent even though first-step overrides are weak.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m839-v4-near-boundary-action-effectiveness-probe-audit.md, runs/m838_v4_near_boundary_action_effectiveness_probe/summary.json, runs/m838_v4_near_boundary_action_effectiveness_probe/direction_summary.csv, runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
- parent_config: experiments/manifests/m839-v4-near-boundary-action-effectiveness-probe-audit.json
- parent_objective: design no-training short-horizon sequence-effectiveness probe after first-step overrides are outcome-weak
- derived_from: m839-v4-near-boundary-action-effectiveness-probe-audit
- blocked_by: M838 first-step direct overrides produce no accepted rows and max margin delta 0.00265
- supersedes: None
- invalidates: None

## Success Criteria

- M840 writes a design document for sequence-effectiveness probing
- M840 defines hold-step semantics directions bounds and acceptance gates
- M840 specifies required implementation artifacts
- M840 states that direct sequence override evidence is not policy self-ID proof
- M840 keeps PPO and promotion blocked

## Failure Criteria

- M840 admits PPO or promotion
- M840 trains actor or residual parameters
- M840 treats sequence override success as learned policy proof
- M840 ignores M838 first-step-insensitive result

## Evidence Gates

- M840 must remain design-only
- M840 must define short-horizon action sequence override semantics
- M840 must keep direct sequence override evidence separate from learned policy self-ID evidence
- M840 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M840
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not reinterpret direct sequence override success as policy self-ID
- do not relax M838 thresholds after seeing the result

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m840-v4-near-boundary-sequence-effectiveness-probe-design
- type: infrastructure
- checkpoint: docs/m840-v4-near-boundary-sequence-effectiveness-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: near_boundary_sequence_effectiveness_probe_design_admit_m841
- reason: M840 designs no-training short-horizon sequence override probe using hold steps 2 4 6 and bounded per-step deltas; direct sequence evidence remains controllability-only and M841 implementation is admitted

## Next Blocker

M838 shows first-step local action effectiveness is too weak, but short-horizon sequence effectiveness is unknown
