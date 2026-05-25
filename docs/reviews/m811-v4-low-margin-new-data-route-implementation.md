# m811-v4-low-margin-new-data-route-implementation Research Review

## Summary

- Generated at UTC: 20260525T071457Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_low_margin_new_data_route_sparse
- Decision reason: M811 runs 2688 no-training boundary candidates with unchanged actor and residual checksums zero warm-up artifacts zero replay errors but zero primary accepted rows; sparse result blocks calibration PPO and promotion pending audit

## Hypothesis

Active diagnostic warm-up plus joint obstacle and fault timing can produce source-diverse primary low-margin rows without weakening the gate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m810-v4-low-margin-new-data-route-design.md, docs/m809-v4-low-margin-source-diverse-branch-synthesis.md, runs/m807_v4_low_margin_boundary_axis_expansion/summary.json
- parent_config: experiments/manifests/m810-v4-low-margin-new-data-route-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement no-training source-diverse near-boundary data route
- derived_from: m810-v4-low-margin-new-data-route-design
- blocked_by: m809-v4-low-margin-source-diverse-branch-synthesis
- supersedes: None
- invalidates: None

## Success Criteria

- M811 writes source group, warm-up, plan, replay, accepted, intervention, balance, limitations, progress, summary, and documentation artifacts
- M811 reports accepted rows, unique seeds, source groups, source indices, warm-up modes, fault-family pairs, boundary axes, and dominance metrics
- M811 confirms actor and residual-head checksums unchanged
- M811 classifies the result without widening the primary margin gate
- M811 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- implementation trains actor, residual head, or a new calibrator
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits source warm-up fault or axis diversity diagnostics
- implementation treats M804/M807 half-width rows as primary-pass evidence without diversity
- implementation claims true wheel-level faults from current proxy data

## Evidence Gates

- M811 implements and runs only a no-training data route
- M811 preserves the P0 human-view actor contract
- M811 keeps alpha 0.2 and the primary <=0.00005 margin threshold unchanged
- M811 requires source warm-up fault and axis diversity before pass
- M811 confirms actor and M761 residual-head checksums unchanged
- M811 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not train a new residual calibrator
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not widen the primary 0.00005 margin threshold
- do not weaken source fault warm-up or axis dominance thresholds
- do not treat M804 or M807 half-width rows alone as a source-diverse pass
- do not claim true wheel-level faults from current single-track proxy data
- do not tune from private holdout failures

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m811-v4-low-margin-new-data-route-implementation
- type: infrastructure
- checkpoint: runs/m811_v4_low_margin_new_data_route/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_low_margin_new_data_route_sparse
- reason: M811 runs 2688 no-training boundary candidates with unchanged actor and residual checksums zero warm-up artifacts zero replay errors but zero primary accepted rows; sparse result blocks calibration PPO and promotion pending audit

## Next Blocker

m812-v4-low-margin-new-data-route-audit
