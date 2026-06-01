# M2189 Paper-Route Current-Sim Task-Quality Offtrack Support Repair Design

- status: completed
- decision: `current_sim_task_quality_offtrack_support_repair_design_admit_candidate_generation`
- manifest: `experiments/manifests/m2189-paper-route-current-sim-task-quality-offtrack-support-repair-design.json`
- parent audit: `docs/m2188-paper-route-current-sim-repeat-seed-diversity-and-combined-outcome-audit-result-audit.md`
- training in M2189: `false`
- measured execution in M2189: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M2187/M2188 prove the current repeat panel is execution-complete, but it is not
comparison-ready:

```text
combined episodes: 960
combined success: 163
combined collision: 56
combined offtrack: 741
combined success rate: 0.16979166666666667
combined offtrack rate: 0.771875
per-repeat success min: 50
```

Readiness gates that failed:

```text
min_combined_success_count: 240
max_combined_offtrack_rate: 0.60
min_success_count_per_repeat: 80
```

Task-family localization:

```text
T1_reactive_emergency_avoidance: success 59 / 192, offtrack 112 / 192
T2_delayed_actuator_response: success 54 / 192, offtrack 135 / 192
T3_diagnostic_warmup_obstacle_reveal: success 30 / 192, offtrack 152 / 192
T4_same_current_different_older_history: success 8 / 192, offtrack 184 / 192
T5_terminal_boundary_near_constraint: success 12 / 192, offtrack 158 / 192
```

The primary blocker is therefore task quality and offtrack saturation, not
runner correctness, metadata plumbing, actor input contract, training, or a
controller-family comparison result.

## Repair Principle

The repair branch must create a more support-rich current-sim panel without
making scenarios trivial and without tuning to a profile family.

Allowed repair levers:

```text
road-boundary relief:
  increase track width in bounded increments;
  increase track radius in bounded increments;
  preserve ego-frame road geometry as actor input.

obstacle timing relief:
  move obstacle distance ranges later in bounded increments;
  reveal obstacle slightly earlier while preserving task-family semantics;
  keep obstacle labels as metadata only.

obstacle geometry relief:
  reduce half-width ranges in small bounded increments;
  preserve safety margin semantics;
  do not relabel collision/offtrack as success.

terminal-boundary severity ladder:
  add milder terminal-boundary variants next to saturated T5 rows;
  preserve hard variants as diagnostics;
  do not erase handling-limit cases.

older-history support ladder:
  reduce road-boundary saturation in T4 while keeping older-history delay
  outside practical short windows.

positive-support preservation:
  seed repair candidates around tasks that already show multiple successful
  profiles so the repaired panel includes solvable anchors.
```

Forbidden repair levers:

```text
profile-specific scenario tuning;
actor input changes;
controller-family-specific filters;
ranking from current descriptive aggregates;
turning off road-boundary failure;
calling offtrack or collision a success;
lowering readiness thresholds to force comparison;
private holdout use in this public repair branch;
paper-level or level3 self-ID claims.
```

## First Candidate Wave

M2190 should implement a deterministic no-rollout repair candidate generator.

Target output:

```text
288 repair candidate templates
```

Composition:

```text
offtrack_saturation_relief:
  96 candidates around zero/near-zero support rows from T3/T4/T5 and
  offtrack-heavy T1/T2 rows.

terminal_boundary_support_ladder:
  64 candidates focused on T5 high-speed close-obstacle rows, especially the
  zero-support T5-02 through T5-06 block and the partially supported T5-07 row.

older_history_ambiguity_support_ladder:
  64 candidates focused on T4 same-current/different-older-history rows, with
  road and timing relief that preserves older-history diagnostic semantics.

diagnostic_warmup_support_ladder:
  32 candidates focused on T3 warmup/reveal rows with high offtrack and low
  success support.

positive_support_preservation:
  32 candidates around supported rows such as T1-05, T2-04, T1-06, and T5-07,
  used as solvable anchors rather than ranking evidence.
```

Suggested deterministic split metadata:

```text
public_debug: 176
public_gate: 112
paper_holdout_candidate: 0
```

No private holdout is used because this is still public task-quality repair.

## Candidate Fields

Each candidate should include:

```text
repair_branch_id
repair_candidate_id
repair_axis
repair_split
parent_task_source_id
parent_task_family
parent_source_family_template
parent_capability_pair
parent_claim_level_target
parent_support_class
parent_episode_count
parent_success_count
parent_collision_count
parent_offtrack_count
delta_track_width
delta_track_radius
delta_obstacle_distance_min
delta_obstacle_distance_max
delta_obstacle_half_width_min
delta_obstacle_half_width_max
delta_reveal_step
delta_speed_min
delta_speed_max
preserve_history_semantics
ranking_admissible_by_default
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

All claim flags must be `false`.

## Candidate Guardrails

M2190 should fail if:

```text
candidate_count != 288
repair axis quotas are not exact
candidate IDs are duplicated
any candidate is profile-specific
any candidate changes actor input contract
any candidate marks ranking_admissible_by_default true
any paper or self-ID claim flag is true
```

## Future Readiness Gates

After materialization/reset/measured execution of a repaired panel, the branch
should re-run readiness checks:

```text
combined_success_count >= 240
combined_offtrack_rate <= 0.60
per_repeat_success_min >= 80
metadata_missing_count == 0
guardrail_violation_count == 0
seed_diversity_status != invalid
```

If support remains low, route to another task-quality repair or branch
synthesis. If support passes but seed-diversity remains suspicious, route to a
repeat seed-diversity audit/repair. Only after both support and seed-diversity
are acceptable may the project design a controller-family comparison.

## Claim Boundary

Allowed claim after M2189:

```text
The next branch step is a no-rollout task-quality/offtrack support repair
candidate generator, not a controller-family comparison.
```

Still blocked:

```text
new rollout;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2190 may implement and run the deterministic no-rollout candidate generator.
It must write the candidate artifact and a summary, but it must not reset,
roll out, train, rank, or compare profiles.
