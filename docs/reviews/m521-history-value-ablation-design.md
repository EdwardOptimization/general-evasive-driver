# m521-history-value-ablation-design Research Review

## Summary

- Generated at UTC: 20260524T021638Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m522_history_value_ablation_runner
- Decision reason: M521 redirects from forced one-shot wrong-history mining to diagnostic L0 L1 L2 L3 history-value ablation with L3-vs-L0 as the first implementation target

## Hypothesis

Because valid-offset projection replay shows only source-narrow margin-only wrong-history signal, the next useful evidence is a direct L0/L1/L2/L3 history-value ablation rather than more forced one-shot wrong-history outcome mining.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m520_valid_offset_projection_outcome_gate/summary.json, runs/m520_valid_offset_projection_outcome_gate/projected_variant_summary.csv, runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv
- parent_config: experiments/manifests/m520-valid-offset-projection-outcome-gate.json, experiments/manifests/m517-projection-aware-boundary-outcome-gate-design.json
- parent_objective: L0/L1/L2/L3 history-value ablation design
- derived_from: m520-valid-offset-projection-outcome-gate
- blocked_by: m520-valid-offset-projection-outcome-gate
- supersedes: None
- invalidates: None

## Success Criteria

- define L0 current-observation, L1 one-step feedback, L2 finite-window, and L3 online-GRU levels
- define initial diagnostic surfaces
- define metrics for history value
- state implementation guardrails and limitations
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design treats M520 as positive source-diverse wrong-history proof
- design adds privileged inputs
- design mixes projected mechanism rows with broad scenario claims
- design requires training before diagnostic ablation
- training or checkpoint promotion is performed

## Evidence Gates

- design history-level ablations after margin-only one-shot wrong-history evidence
- separate L3 recurrent belief value from one-shot wrong-history event proof
- keep projected mechanism surfaces separate from natural scenario claims
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim projected mechanism rows prove broad scenario generalization
- do not conflate reset or zero-current controls with wrong-history proof
- do not overclaim L1 or L2 if the first implementation only supports L0 and L3

## Failure Taxonomy

- none

## Scoreboard

- milestone: m521-history-value-ablation-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m522_history_value_ablation_runner
- reason: M521 redirects from forced one-shot wrong-history mining to diagnostic L0 L1 L2 L3 history-value ablation with L3-vs-L0 as the first implementation target

## Next Blocker

M522 should implement a history-value ablation runner.
