# M2021 Multi-Slice Bounded Diagnostic Comparison Result Audit

- status: completed
- decision: `multi_slice_bounded_diagnostic_audit_route_to_controlled_comparison_panel_design`
- audited summary: `runs/m2020_multi_slice_bounded_diagnostic_comparison/summary.json`
- audited aggregate table: `runs/m2020_multi_slice_bounded_diagnostic_comparison/aggregate_profile_group_comparison.csv`
- audited candidate support: `runs/m2020_multi_slice_bounded_diagnostic_comparison/candidate_support.csv`
- governing plans:
  - `docs/self-id-go-no-go-paper-route-plan.md`
  - `docs/paper-route-finite-window-vs-gru-plan.md`
- next branch: `paper_route_controlled_l0_l1_l2_l3_comparison_design`
- reset/rollout/measured execution in M2021: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2020 is complete as a no-rerun multi-slice bounded diagnostic artifact:

```text
result_class: multi_slice_bounded_diagnostic_comparison_pass
candidate_count: 6
matched_episode_count: 216
candidate_profile_group_row_count: 24
aggregate_profile_group_row_count: 4
guardrail_violation_count: 0
```

M2020 did not interact with the actor or environment:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
actor_input_contract_changed: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Diagnostic Signal

M2020 aggregates six admitted public slices:

```text
L0: 9/18 success, collision 3/18, offtrack 6/18
L1: 8/18 success, collision 2/18, offtrack 8/18
L2: 0/144 success, collision 27/144, offtrack 117/144
L3: 22/36 success, collision 5/36, offtrack 9/36
```

Candidate-level support:

```text
drift_required_recovery / tier_c_boundary_near_miss / post_friction_step / drift_required:
  L2 0/24, non-L2 7/12

drift_required_recovery / tier_e_mitigation_only / steady_surface / drift_required:
  L2 0/16, non-L2 5/8

stable_aeb / tier_c_boundary_near_miss / post_friction_step / aeb_feasible:
  L2 0/24, non-L2 5/12

stable_aeb / tier_e_mitigation_only / post_friction_step / aeb_feasible:
  L2 0/24, non-L2 3/12

stable_aes_only / tier_b_feasible_emergency / post_friction_step / aes_feasible:
  L2 0/40, non-L2 17/20

unavoidable_mitigation / tier_b_feasible_emergency / post_friction_step / unavoidable:
  L2 0/16, non-L2 2/8
```

This is a useful diagnostic trigger: the current artifacts contain multiple
active-safety roles where the profile groups separate strongly enough to justify
a controlled comparison design.

## Boundary Audit

The evidence remains bounded:

```text
repair_source_kind_count: 1
private_holdout_used: false
profile_specific_tuning: false
wrong-history test: not run
history necessity test: not run
fair training-budget matrix: not run
```

Allowed interpretation:

```text
M2020 is a multi-slice public diagnostic table. It suggests that a fair
L0/L1/L2/L3 comparison would be informative and should be designed.
```

Forbidden interpretation:

```text
M2020 ranks controller families.
M2020 proves L3-GRU is better than finite-window controllers.
M2020 proves level3 self-identification.
M2020 is paper-level benchmark evidence.
```

The paper-route plans require finite-window-vs-GRU and self-ID to remain
bounded hypotheses. A source-singleton public diagnostic pattern cannot support
the final claim ladder by itself.

## Route Decision

Decision:

```text
route_to_controlled_comparison_panel_design
```

Rationale:

- The M2020 signal is no longer a singleton diagnostic; it spans six admitted
  slices across multiple roles, tiers, surfaces, and labels.
- The source-kind singleton boundary prevents direct ranking or paper-level
  claims.
- More public-slice mining would risk local search unless it introduces a new
  evidence type.
- The highest-leverage next step is to design the fair L0/L1/L2/L3 controller
  comparison panel required by the paper-route plans, including source-rich task
  requirements and holdout discipline before any execution.

Rejected routes:

```text
direct_controller_family_ranking:
  rejected because M2020 is public, source-kind singleton, and not a fair
  training/evaluation matrix.

finite_window_vs_gru_conclusion:
  rejected because L2/L3 profile counts differ, no controlled training budgets
  are established, and no holdout or source-rich comparison is run.

level3_self_identification_testing_directly:
  rejected because the current audit branch has not yet defined a source-rich
  controlled panel or wrong-history/history-necessity task family.

another_no_rerun_public_slice_extension:
  rejected unless a synthesis first proves it adds a new evidence type rather
  than extending the same public diagnostic loop.

stop_branch:
  rejected because M2020 provides enough diagnostic signal to justify a
  controlled comparison design.
```

## M2022 Requirements

M2022 should design a paper-route controlled comparison panel. It must not run
training or rollout yet. It should specify:

```text
controller families:
  L0-current
  L1-one-step
  L2-finite-window at practical windows
  L3-GRU
  L3-reset/truncated controls

task families:
  reactive evasive driving
  same-current different-older-history
  active diagnostic warmup
  variable diagnostic delay
  source-rich extreme dynamics

fairness:
  same action contract
  same actor input boundary
  same train/eval splits
  same budgets and seeds
  parameter count and inference latency reporting
  public/private holdout rules

claim gates:
  engineering feedback driver
  history-conditioned output feedback
  recurrent belief advantage
  strong self-identification
```

M2022 must preserve the current rule:

```text
No controller ranking, finite-window-vs-GRU conclusion, paper-level claim, or
level3 self-ID claim is allowed until the controlled panel is executed and
audited.
```
