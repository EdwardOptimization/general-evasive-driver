# M2264 Paper-Route Current-Sim Midcourse Corridor-Containment Selected-Checkpoint Outcome Localization Design

- status: completed
- decision: `current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization_design_admit_execution`
- manifest: `experiments/manifests/m2264-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-design.json`
- parent audit: `docs/m2263-paper-route-current-sim-midcourse-corridor-containment-training-execution-result-audit.md`
- selected checkpoint source: `runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv`

## Design Rationale

M2263 establishes that M2262 is a clean targeted containment training execution,
but it does not establish outcome repair:

```text
completed_run_count: 15
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 11/15
selected_checkpoint_profile_floor_pass_count: 0
local selected readiness rows: 4/15
```

The target failure from M2256/M2257 is not aggregate return. It is:

```text
midcourse mild boundary-containment regression
```

Therefore the next evidence gap is episode-level outcome mode:

```text
Did targeted containment reduce midcourse offtrack?
Did it reduce mild overshoot?
Did it trade offtrack into collision?
Did it introduce max-step noncompletion?
```

## Execution Scope

M2265 should evaluate exactly the `15` M2262 selected checkpoint rows:

```text
selected rows:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs

profiles:
  L0_current_masked
  L1_one_step
  L2_window_25
  L2_window_50
  L3_online_gru

seeds:
  222601
  222602
  222603

episodes per selected checkpoint:
  32

expected episode rows:
  480
```

Use the same public episode-seed policy as M2244/M2253:

```text
episode_seed = seed_id + 10000 + episode_index
```

This keeps M2265 comparable to M2244 and M2253 as repair-route evidence, not as
a controller-family ranking.

## Execution Command

M2265 should run:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_selected_checkpoint_outcome_localization \
  --selected-rows runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --output-dir runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization \
  --next-blocker m2266-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-result-audit \
  --device cpu
```

## Required Outputs

M2265 should write:

```text
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/summary.json
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/profile_seed_aggregate.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/profile_aggregate.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/outcome_aggregate.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/termination_aggregate.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/repair_route_candidates.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/run_state.json
```

Success criteria:

```text
result_class: current_sim_selected_checkpoint_outcome_localization_pass
selected_checkpoint_count: 15
episode_row_count: 480
profile_seed_groups_complete: true
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

## Audit Metrics

M2266 must compare M2265 against M2244 as the base panel and M2253 as the
generic-repair reference:

```text
M2244 base: success/offtrack/collision = 277/110/93
M2253 generic repair: success/offtrack/collision = 269/118/93
```

M2265 improves the targeted repair route only if it supports the M2258 slice
criteria:

```text
mid_offtrack_delta vs M2244 <= 0
mild_overshoot_delta vs M2244 <= 0
global_offtrack_count < 110
collision_count <= 107
max_step_noncompletion_count == 0
```

Return improvement alone is explicitly insufficient.

## Guardrails

M2264 and M2265 must not:

```text
train
alter checkpoints
alter actor inputs
drop selected checkpoints
drop seeds
use private holdout
promote any checkpoint
rank profiles
select a winner
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Route Logic

M2266 should route by M2265 outcome mode:

```text
if mid_offtrack and mild_overshoot improve while collision stays <= 107:
  route to repaired-panel support audit

if offtrack remains worse than M2244:
  route to branch synthesis or task/reward redesign, not another scalar tweak

if collision rises above guardrail:
  route to collision/clearance guardrail repair

if mixed or low support:
  route to branch synthesis before further local search
```

## Next

Pre-register:

```text
m2265-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-implementation
```
