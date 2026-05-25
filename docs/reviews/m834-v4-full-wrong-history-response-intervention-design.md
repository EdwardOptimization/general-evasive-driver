# m834-v4-full-wrong-history-response-intervention-design Research Review

## Summary

- Generated at UTC: 20260525T115025Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: full_wrong_history_response_intervention_design_admit_m835
- Decision reason: M834 designs no-training response/action stream wrong-history interventions that separate hidden-only ego-response previous-command and response-plus-hidden effects on M832 near-boundary pairs

## Hypothesis

A full wrong-history intervention that swaps deployable response/action observation fields, not only recurrent hidden state, will better test whether the actor's self-ID signal lives in current response stream versus hidden memory.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m833-v4-near-boundary-wrong-history-pair-mining-audit.md, runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv, runs/m832_v4_near_boundary_wrong_history_pair_mining/wrong_history_replay_rows.csv, runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
- parent_config: experiments/manifests/m833-v4-near-boundary-wrong-history-pair-mining-audit.json
- parent_objective: design full wrong-history response/action observation intervention after hidden-only near-boundary negative
- derived_from: m833-v4-near-boundary-wrong-history-pair-mining-audit
- blocked_by: M832 hidden-only wrong-history injection remains below action and margin thresholds despite near-boundary pairs
- supersedes: None
- invalidates: None

## Success Criteria

- M834 writes a design document for full wrong-history response/action interventions
- M834 defines variants and acceptance gates
- M834 specifies required implementation artifacts
- M834 preserves P0 actor input contract
- M834 keeps PPO and promotion blocked

## Failure Criteria

- M834 proposes hidden fault labels or oracle inputs
- M834 admits PPO or promotion
- M834 fails to separate hidden response and action-history intervention effects
- M834 ignores M832 near-boundary negative

## Evidence Gates

- M834 must remain design-only
- M834 must preserve actor input contract
- M834 must define response/action stream intervention variants separately from hidden-only
- M834 must keep wrong-history evidence separate from zero-command evidence
- M834 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M834
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels or oracle fields to actor input
- do not count zero-command-only degradation as wrong-history proof
- do not relax M832 thresholds after seeing the result

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m834-v4-full-wrong-history-response-intervention-design
- type: infrastructure
- checkpoint: docs/m834-v4-full-wrong-history-response-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: full_wrong_history_response_intervention_design_admit_m835
- reason: M834 designs no-training response/action stream wrong-history interventions that separate hidden-only ego-response previous-command and response-plus-hidden effects on M832 near-boundary pairs

## Next Blocker

full wrong-history response/action intervention is not yet designed
