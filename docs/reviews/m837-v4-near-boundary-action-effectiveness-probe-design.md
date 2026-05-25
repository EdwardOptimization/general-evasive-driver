# m837-v4-near-boundary-action-effectiveness-probe-design Research Review

## Summary

- Generated at UTC: 20260525T121401Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: near_boundary_action_effectiveness_probe_design_admit_m838
- Decision reason: M837 designs bounded direct first-action override probing on M832 near-boundary pairs; direct override success will count only as local controllability evidence not learned self-ID proof and M838 implementation is admitted without PPO or promotion

## Hypothesis

A local direct-action override probe can determine whether M832 near-boundary states are first-action controllable enough to support an outcome-coupled response-history objective.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m836-v4-full-wrong-history-response-intervention-audit.md, runs/m835_v4_full_wrong_history_response_intervention/variant_summary.csv, runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv, runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
- parent_config: experiments/manifests/m836-v4-full-wrong-history-response-intervention-audit.json
- parent_objective: design local first-action effectiveness probe before objective or architecture changes
- derived_from: m836-v4-full-wrong-history-response-intervention-audit
- blocked_by: M835 response/action interventions create action drift but not outcome evidence
- supersedes: None
- invalidates: None

## Success Criteria

- M837 writes a design document for local action-effectiveness probing
- M837 defines override directions bounds and acceptance gates
- M837 specifies required implementation artifacts
- M837 states that direct override evidence is not policy self-ID proof
- M837 keeps PPO and promotion blocked

## Failure Criteria

- M837 admits PPO or promotion
- M837 trains actor or residual parameters
- M837 treats action override success as learned policy proof
- M837 ignores M835 all-weak result

## Evidence Gates

- M837 must remain design-only
- M837 must define local action override directions and bounds
- M837 must separate controllability evidence from policy self-ID evidence
- M837 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M837
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not reinterpret direct action override success as policy self-ID
- do not relax M835 thresholds after seeing the result

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m837-v4-near-boundary-action-effectiveness-probe-design
- type: infrastructure
- checkpoint: docs/m837-v4-near-boundary-action-effectiveness-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: near_boundary_action_effectiveness_probe_design_admit_m838
- reason: M837 designs bounded direct first-action override probing on M832 near-boundary pairs; direct override success will count only as local controllability evidence not learned self-ID proof and M838 implementation is admitted without PPO or promotion

## Next Blocker

near-boundary state action-effectiveness is unknown
