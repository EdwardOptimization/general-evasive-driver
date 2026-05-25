# m823-v4-adaptive-primary-calibration-next-route-design Research Review

## Summary

- Generated at UTC: 20260525T095913Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_extreme_hidden_dynamics_data_route_design
- Decision reason: M823 rejects same-corpus fixed-gate tuning and learned gate training from identity-only evidence and pivots to source-diverse extreme hidden-dynamics self-ID data-route design

## Hypothesis

After M821/M822, the next useful step must add new data or a different objective signal rather than tuning fixed residual gates on the same corpus.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m822-v4-adaptive-primary-calibration-grid-audit.md, runs/m821_v4_adaptive_primary_calibration_grid/summary.json, runs/m821_v4_adaptive_primary_calibration_grid/train_candidate_metrics.csv, runs/m821_v4_adaptive_primary_calibration_grid/holdout_candidate_metrics.csv
- parent_config: experiments/manifests/m822-v4-adaptive-primary-calibration-grid-audit.json
- parent_objective: design next route after fixed-gate identity-only audit
- derived_from: m822-v4-adaptive-primary-calibration-grid-audit
- blocked_by: fixed scalar/vector residual gates do not beat identity on M814/M817 corpus
- supersedes: None
- invalidates: None

## Success Criteria

- M823 writes a design document for the next route
- M823 explicitly rejects more fixed-gate tuning on the same corpus
- M823 chooses between data-route expansion, diagnostic objective design, or branch closure
- M823 keeps actor/residual training PPO and promotion blocked

## Failure Criteria

- M823 admits fixed-gate tuning on the same corpus
- M823 starts implementation or training
- M823 allows PPO or promotion
- M823 ignores M821 identity-only result
- M823 weakens actor-input or primary-threshold constraints

## Evidence Gates

- M823 must remain design-only
- M823 must not train or run PPO
- M823 must not promote a checkpoint
- M823 must not continue fixed-gate tuning on the same corpus
- M823 must choose a next route that adds new evidence rather than optimizing identity retention

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not train a calibrator
- do not run PPO
- do not promote a checkpoint
- do not tune fixed scalar/vector gates on the same public corpus
- do not reinterpret identity-only as improvement
- do not widen the primary 0.00005 margin threshold
- do not add oracle deploy-time inputs

## Failure Taxonomy

- metric_artifact
- objective_overfit
- scenario_sampling_failure

## Scoreboard

- milestone: m823-v4-adaptive-primary-calibration-next-route-design
- type: infrastructure
- checkpoint: docs/m823-v4-adaptive-primary-calibration-next-route-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_extreme_hidden_dynamics_data_route_design
- reason: M823 rejects same-corpus fixed-gate tuning and learned gate training from identity-only evidence and pivots to source-diverse extreme hidden-dynamics self-ID data-route design

## Next Blocker

m824-v4-extreme-hidden-dynamics-data-route-design
