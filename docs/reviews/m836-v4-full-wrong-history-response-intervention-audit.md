# m836-v4-full-wrong-history-response-intervention-audit Research Review

## Summary

- Generated at UTC: 20260525T120922Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_near_boundary_action_effectiveness_probe_design
- Decision reason: M836 audits M835 as clean all-weak metric-artifact result and routes next to local first-action effectiveness probe design before objective or architecture changes

## Hypothesis

M835 is a clean all-weak intervention result and should likely pivot the branch away from more no-training counterfactual mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m835-v4-full-wrong-history-response-intervention-implementation.md, runs/m835_v4_full_wrong_history_response_intervention/summary.json, runs/m835_v4_full_wrong_history_response_intervention/variant_summary.csv, runs/m835_v4_full_wrong_history_response_intervention/response_intervention_replay_rows.csv
- parent_config: experiments/manifests/m835-v4-full-wrong-history-response-intervention-implementation.json
- parent_objective: audit all-weak full wrong-history response/action intervention result
- derived_from: m835-v4-full-wrong-history-response-intervention-implementation
- blocked_by: M835 found zero accepted response-history component mitigation rows and only tiny margin gaps
- supersedes: None
- invalidates: None

## Success Criteria

- M836 writes an audit document for M835
- M836 records per-variant action and margin effects
- M836 separates action drift from outcome evidence
- M836 classifies the failure taxonomy
- M836 names the next blocker without admitting PPO or promotion

## Failure Criteria

- M836 treats action drift alone as proof
- M836 admits PPO or promotion
- M836 proposes threshold relaxation as the main fix
- M836 ignores M835 zero accepted rows

## Evidence Gates

- M836 must audit M835 before any new implementation
- M836 must distinguish action drift from outcome evidence
- M836 must decide whether to continue data/intervention mining or pivot to objective/architecture evidence
- M836 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in the audit
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not reinterpret action drift alone as self-ID proof
- do not relax thresholds after seeing the result

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m836-v4-full-wrong-history-response-intervention-audit
- type: gate
- checkpoint: docs/m836-v4-full-wrong-history-response-intervention-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_near_boundary_action_effectiveness_probe_design
- reason: M836 audits M835 as clean all-weak metric-artifact result and routes next to local first-action effectiveness probe design before objective or architecture changes

## Next Blocker

M568/M761 behavior is outcome-weak under hidden and response/action counterfactuals
