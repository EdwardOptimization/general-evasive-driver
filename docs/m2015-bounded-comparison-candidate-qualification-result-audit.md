# M2015 Bounded Comparison Candidate Qualification Result Audit

- status: completed
- decision: `bounded_comparison_candidate_qualification_audit_route_to_bounded_diagnostic_comparison`
- audited summary: `runs/m2014_bounded_comparison_candidate_qualification/summary.json`
- next branch: `paper_route_bounded_diagnostic_comparison`
- reset/rollout/measured execution in M2015: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2014 is complete as a no-rerun candidate-qualification artifact:

```text
result_class: bounded_comparison_candidate_qualification_pass
source_candidate_count: 2
qualification_row_count: 2
admitted_candidate_count: 1
rejected_candidate_count: 1
guardrail_violation_count: 0
```

M2014 did not interact with the environment or actor:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Admitted Candidate Audit

The admitted candidate is:

```text
success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible
```

Qualification facts:

```text
episode_count: 60
success_count: 17
collision_count: 2
offtrack_outcome_count: 41
success_rate: 28.33%
collision_rate: 3.33%
offtrack_outcome_rate: 68.33%
success_profile_groups: L0; L1; L3
l2_success_present: false
l2_total_success_count: 0
admitted_scope: bounded_diagnostic_comparison_not_finite_window_vs_gru
```

The candidate is useful enough for a bounded diagnostic comparison because it
has nonzero support, low collision rate, and multiple non-L2 profile groups with
success. It is not enough for a paper-level controller-family ranking because
it is a single public slice with high offtrack rate and no L2 successes.

## Rejected Candidate Audit

The rejected candidate is:

```text
success_stabilizer|drift_required_recovery|tier_e_mitigation_only|steady_surface|drift_required
```

Reasons:

```text
source_label_not_comparison_ready_candidate
episode_count_below_threshold
success_count_below_threshold
collision_rate_above_threshold
```

This is a mitigation/collision diagnostic, not a bounded comparison target.

## Route Decision

Decision:

```text
route_to_bounded_diagnostic_comparison
```

Rationale:

- M2014 turned the localizer label into an explicit admissible scope.
- The admitted stable-AES slice is strong enough to produce a small diagnostic
  profile table from existing rows.
- Direct ranking and finite-window-vs-GRU conclusions remain blocked because
  L2 has zero successes and the slice is single-source/single-role.
- Running another task-quality repair before extracting the diagnostic table
  would ignore the new admitted evidence.

Rejected routes:

```text
direct_controller_family_ranking:
  rejected because the admitted scope is bounded diagnostic only.

finite_window_vs_gru_conclusion:
  rejected because l2_success_present=false and the evidence is one public
  slice.

paper_level_comparison:
  rejected because support is sparse and offtrack dominated.

new outcome-support repair:
  rejected for now because the admitted diagnostic slice should be consumed
  before another repair branch.
```

## M2016 Requirements

M2016 should implement and run a no-rerun bounded diagnostic comparison over
the admitted candidate key. It should read existing M2009/M2012/M2014 artifacts
and write:

```text
profile-level outcome table on the admitted slice
profile-group summary
claim-boundary artifact
guardrail summary
```

M2016 must not:

```text
run environment rollout
execute policy actions
train or replay
rank controller families broadly
claim finite-window-vs-GRU
claim paper-level evidence
claim level3 self-ID
```
