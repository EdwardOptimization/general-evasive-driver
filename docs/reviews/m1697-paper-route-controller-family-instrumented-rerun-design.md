# m1697-paper-route-controller-family-instrumented-rerun-design Research Review

## Summary

- Generated at UTC: 20260530T003447Z
- Type: gate
- Gate tier: process
- Promotion decision: instrumented_rerun_design_admit_public_execution
- Decision reason: M1697 designs same-workload instrumented public rerun to M1698 output with outcome termination and profile-outcome artifacts before audit

## Hypothesis

A guarded instrumented rerun plan can preserve M1693 comparability while adding outcome semantics needed for later audit.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1696-paper-route-controller-family-outcome-semantics-instrumentation-implementation.md, runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
- parent_config: experiments/manifests/m1696-paper-route-controller-family-outcome-semantics-instrumentation-implementation.json
- parent_objective: design an instrumented rerun of the M1693 public workload
- derived_from: m1696-paper-route-controller-family-outcome-semantics-instrumentation-implementation
- blocked_by: need design before rerunning the 864-cell workload with outcome semantics instrumentation
- supersedes: direct instrumented rerun without design, controller-family ranking from uninstrumented M1693 rows
- invalidates: None

## Success Criteria

- docs/m1697-paper-route-controller-family-instrumented-rerun-design.md exists
- design specifies same 864 workload and deterministic seeds
- design specifies outcome aggregate artifacts
- design specifies no-ranking claim boundary
- full rerun training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design changes workload profiles checkpoints seeds or actor inputs
- design omits outcome-semantics artifacts
- design allows ranking before audit
- full rerun training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1697 must design but not execute the instrumented 864-cell public rerun
- M1697 must preserve the exact M1693 workload, profiles, checkpoints, seeds, and actor input contract
- M1697 must require outcome, termination-reason, and profile-outcome aggregates
- M1697 must keep no-training no-replay no-PPO no-promotion no-private-holdout guardrails
- M1697 must not claim controller-family ranking, paper-level evidence, or level3 self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not execute the full rerun in M1697
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not claim controller-family ranking
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1697-paper-route-controller-family-instrumented-rerun-design
- type: gate
- checkpoint: docs/m1697-paper-route-controller-family-instrumented-rerun-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: instrumented_rerun_design_admit_public_execution
- reason: M1697 designs same-workload instrumented public rerun to M1698 output with outcome termination and profile-outcome artifacts before audit

## Next Blocker

m1698-paper-route-controller-family-instrumented-rerun-execution
