# m715-extreme-fault-coverage-refresh-design Research Review

## Summary

- Generated at UTC: 20260524T193344Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: extreme_fault_coverage_refresh_design_admit_m716
- Decision reason: M715 registers a broader v2 fault coverage taxonomy and config with current-model proxy boundaries validates it with a one-seed smoke and admits only a no-training M716 data wave

## Hypothesis

The project may not have mined enough extreme hidden-condition coverage; a broader current-model/proxy fault taxonomy can reveal matched-history intervention rows that M704/M707 did not expose.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m714-actor-head-history-signal-coupling-audit.md, runs/m704_extreme_dynamics_scenario_corpus/summary.json, runs/m707_cross_fault_wrong_history_scenario/summary.json, runs/m710_cross_fault_hidden_action_gap_audit/summary.json, runs/m713_actor_head_history_signal_coupling/summary.json
- parent_config: configs/extreme_hidden_condition_scenarios.json, configs/cross_fault_hidden_condition_scenarios.json
- parent_objective: design a broader no-training extreme-fault coverage refresh before objective design or actor mutation
- derived_from: m714-actor-head-history-signal-coupling-audit
- blocked_by: m714-actor-head-history-signal-coupling-audit
- supersedes: configs/cross_fault_hidden_condition_scenarios.json for future full-coverage discovery runs
- invalidates: None

## Success Criteria

- M715 documents the coverage gap hypothesis and model-fidelity boundary
- M715 adds a validated v2 fault coverage config
- M715 defines the M716 full data wave command and acceptance criteria
- actor input contract remains unchanged
- no training PPO actor update or promotion occurs

## Failure Criteria

- design claims true single-wheel or left-right dynamics from the single-track model
- design omits normal reset wrong or delayed-history interventions
- design lacks source-diversity requirements
- design admits actor update PPO or promotion before data generation
- config cannot be loaded by the existing extreme dynamics corpus runner

## Evidence Gates

- fault taxonomy separates current-model faults current-model proxies and future four-wheel-only faults
- config covers road surface tire/axle authority brake drive steering vehicle-mass actuator-delay and combined faults
- single-wheel blowout split-mu stuck-caliper and true asymmetric half-shaft faults are not claimed as faithful single-track physics
- M716 full data wave is pre-registered with normal reset wrong and delayed-history comparisons
- actor inputs remain P0 human-view no-wheel with no hidden fault labels
- objective design PPO actor update and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim current-model proxies are true single-wheel or left-right physics
- do not add fault family severity activation step or hidden vehicle parameters to actor inputs
- do not train an actor from this config milestone
- do not run PPO
- do not promote a checkpoint
- do not tune thresholds after inspecting private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m715-extreme-fault-coverage-refresh-design
- type: infrastructure
- checkpoint: docs/m715-extreme-fault-coverage-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_coverage_refresh_design_admit_m716
- reason: M715 registers a broader v2 fault coverage taxonomy and config with current-model proxy boundaries validates it with a one-seed smoke and admits only a no-training M716 data wave

## Next Blocker

m716-extreme-fault-coverage-refresh-implementation
