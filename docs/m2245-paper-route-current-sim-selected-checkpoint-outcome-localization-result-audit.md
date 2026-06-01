# M2245 Paper-Route Current-Sim Selected-Checkpoint Outcome Localization Result Audit

- status: completed
- decision: `current_sim_selected_checkpoint_outcome_localization_audit_route_to_offtrack_recovery_corridor_repair_design`
- manifest: `experiments/manifests/m2245-paper-route-current-sim-selected-checkpoint-outcome-localization-result-audit.json`
- parent result: `runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/summary.json`

## Audit Result

M2244 is a complete diagnostic localization artifact:

```text
result_class: current_sim_selected_checkpoint_outcome_localization_pass
selected_checkpoint_count: 15
episode_row_count: 480
expected_episode_row_count: 480
profile_seed_group_count: 15
profile_seed_groups_complete: true
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The guardrails held:

```text
training_started: false
ppo_started: false
replay_started: false
private_holdout_used: false
promoted: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Outcome Evidence

Global outcome over `480` selected-checkpoint episodes:

| outcome | count | rate |
| --- | ---: | ---: |
| success | `277` | `0.57708` |
| offtrack | `110` | `0.22917` |
| collision | `93` | `0.19375` |
| max-step noncompletion | `0` | `0.0` |

The global dominant failure mode is:

```text
offtrack_dominated_failure
```

Every profile aggregate is also labeled `offtrack_dominated_failure`:

| profile | success rate | collision rate | offtrack rate |
| --- | ---: | ---: | ---: |
| L0_current_masked | `0.59375` | `0.17708` | `0.22917` |
| L1_one_step | `0.57292` | `0.19792` | `0.22917` |
| L2_window_25 | `0.59375` | `0.17708` | `0.22917` |
| L2_window_50 | `0.60417` | `0.18750` | `0.20833` |
| L3_online_gru | `0.52083` | `0.22917` | `0.25000` |

Profile-seed rows show local variation:

- `L0_current_masked|222603`, `L1_one_step|222603`, `L2_window_25|222601`,
  `L2_window_50|222601`, and `L3_online_gru|222602` are `success_supported`.
- `L1_one_step|222602` is the only local `collision_dominated_failure`.
- The remaining weak groups are `offtrack_dominated_failure`.

## Classification

Primary classification:

```text
selected_checkpoint_panel_offtrack_recovery_corridor_failure
```

Supported:

- The selected-checkpoint panel is complete enough to diagnose the next repair
  target.
- Offtrack/recovery/corridor failure is the primary blocker.
- Collision/clearance risk remains a secondary guardrail because collision rate
  is `0.19375` and one profile-seed group is collision dominated.
- Checkpoint selection should be retained as infrastructure, but it is not the
  next active repair variable.

Not supported:

- Another checkpoint-selection-only run.
- Another blind budget escalation.
- Profile ranking or winner selection.
- Finite-window-vs-GRU, paper-level, or level3 self-identification claims.

## Route Decision

Route to:

```text
m2246-paper-route-current-sim-offtrack-recovery-corridor-repair-design
```

Reason:

```text
M2244 converts the readiness blocker from unknown aggregate failure into a
specific offtrack/recovery/corridor failure mode. The next experiment should
design a task/reward/corridor repair that reduces offtrack without hiding
collision risk or changing the actor input contract.
```

The repair design should preserve the existing five-profile / three-seed
matched panel and checkpoint-retention infrastructure. It should change the
task/reward/curriculum only after specifying guardrails:

```text
offtrack rate must fall
collision rate must not rise materially
max-step noncompletion must stay near zero
no profile ranking until readiness floors pass
no actor input contract change
```

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another checkpoint-selection-only run
another blind budget escalation
```

## Next

Pre-register:

```text
m2246-paper-route-current-sim-offtrack-recovery-corridor-repair-design
```
