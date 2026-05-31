# M2019 Source-Diverse Diagnostic Expansion Mining Result Audit

- status: completed
- decision: `source_diverse_diagnostic_expansion_audit_route_to_multi_slice_bounded_diagnostic_comparison`
- audited summary: `runs/m2018_source_diverse_diagnostic_expansion_mining/summary.json`
- next branch: `paper_route_multi_slice_bounded_diagnostic_comparison`
- reset/rollout/measured execution in M2019: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2018 is complete as a no-rerun mining artifact:

```text
result_class: source_diverse_diagnostic_expansion_mining_pass
diagnostic_row_count: 88
episode_row_count: 960
candidate_count: 7
admitted_candidate_count: 6
beyond_m2016_admitted_candidate_count: 5
guardrail_violation_count: 0
```

M2018 did not interact with the environment or actor:

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

## Diversity Audit

M2018 found more than a singleton:

```text
admitted_candidate_count: 6
beyond_m2016_admitted_candidate_count: 5
role_count: 4
tier_count: 3
surface_count: 2
label_count: 4
max_candidate_source_count: 5
```

But it is not fully source-kind diverse:

```text
repair_source_kind_count: 1
```

Allowed interpretation:

```text
The current public artifacts contain multi-slice L2-zero/non-L2-success
diagnostic support across roles, tiers, surfaces, labels, and candidate
sources, beyond the M2016 singleton.
```

Forbidden interpretation:

```text
The evidence is source-kind diverse.
The evidence ranks controller families.
The evidence proves finite-window-vs-GRU.
The evidence proves level3 self-identification.
```

## Route Decision

Decision:

```text
route_to_multi_slice_bounded_diagnostic_comparison
```

Rationale:

- M2018 found enough admitted candidates for a multi-slice diagnostic table.
- The table can check whether the M2016 pattern persists across roles, tiers,
  surfaces, and labels without new rollout.
- The source-kind singleton boundary is explicit, so the next comparison must
  remain diagnostic and cannot become broad ranking or paper-level evidence.
- Starting a repair/redesign before consuming the admitted candidates would
  leave existing evidence unused.

Rejected routes:

```text
direct_controller_family_ranking:
  rejected because M2018 is no-rerun public mining and source-kind singleton.

finite_window_vs_gru_conclusion:
  rejected because the comparison is not source-kind diverse, not private
  holdout, and not a fair training/eval matrix.

task_quality_repair_immediately:
  rejected until the six admitted candidates are summarized in one multi-slice
  diagnostic table.

level3_self_id_testing:
  rejected because this branch does not test wrong-history or history
  necessity.
```

## M2020 Requirements

M2020 should implement and run a no-rerun multi-slice bounded diagnostic
comparison. It should read M2018 admitted candidates and M2009 episode rows,
then write:

```text
candidate/profile-group table
aggregate profile-group table
candidate-level support table
claim boundary
guardrail summary
```

M2020 must not:

```text
execute policy actions
run measured execution
train or replay
rank controller families
claim finite-window-vs-GRU
claim paper-level evidence
claim level3 self-ID
```
