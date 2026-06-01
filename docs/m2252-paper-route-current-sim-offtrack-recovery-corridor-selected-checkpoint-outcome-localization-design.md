# M2252 Paper-Route Current-Sim Offtrack/Recovery/Corridor Selected-Checkpoint Outcome Localization Design

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization_design_admit_execution`
- manifest: `experiments/manifests/m2252-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-design.json`
- parent audit: `docs/m2251-paper-route-current-sim-offtrack-recovery-corridor-training-execution-result-audit.md`
- selected checkpoint source: `runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv`

## Design Rationale

M2251 establishes that M2250 is a clean repaired training execution with useful
return movement, but it does not establish outcome repair:

```text
completed_run_count: 15
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 15/15
selected_checkpoint_profile_floor_pass_count: 0
local selected readiness rows: 4/15
```

The next evidence gap is not another aggregate training run. The next evidence
gap is episode-level outcome mode:

```text
Did the offtrack/recovery/corridor reward extension reduce offtrack?
Did it trade offtrack into collision?
Did it leave the selected panel broadly unsupported?
```

## Execution Scope

M2253 should evaluate exactly the `15` M2250 selected checkpoint rows:

```text
selected rows:
  runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/configs

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

Use the same public episode-seed policy as M2244:

```text
episode_seed = seed_id + 10000 + episode_index
```

This keeps the M2253 panel comparable to M2244 as repair-route evidence, not as
a controller-family ranking.

## Execution Command

M2253 should run:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_selected_checkpoint_outcome_localization \
  --selected-rows runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2250_paper_route_current_sim_offtrack_recovery_corridor_training_execution/configs \
  --output-dir runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization \
  --next-blocker m2254-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-result-audit \
  --device cpu
```

The existing runner already accepts the selected rows, config root, output dir,
episode count, device, and next blocker. If M2253 needs a task-id metadata
repair, it must be default-preserving and must not change episode semantics.

## Required Outputs

M2253 should write:

```text
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/summary.json
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/profile_seed_aggregate.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/profile_aggregate.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/outcome_aggregate.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/termination_aggregate.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/repair_route_candidates.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/run_state.json
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

## Baseline For Audit

M2254 should compare M2253 against M2244 only as repair-route evidence.

M2244 baseline selected panel:

| outcome | count | rate |
| --- | ---: | ---: |
| success | `277/480` | `0.57708` |
| offtrack | `110/480` | `0.22917` |
| collision | `93/480` | `0.19375` |
| max-step noncompletion | `0/480` | `0.0` |

M2253 improves the repair route only if offtrack falls without materially
raising collision or introducing max-step noncompletion. Return improvement
alone is not sufficient.

## Guardrails

M2252 and M2253 must not:

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

M2254 should route by M2253 outcome mode:

```text
if offtrack rate falls and collision does not rise materially:
  route to readiness-floor/repaired-panel audit

if offtrack remains dominant:
  route to stronger offtrack/recovery/corridor repair or branch synthesis

if collision becomes dominant:
  route to collision/clearance guardrail repair

if mixed or low support:
  route to task-curriculum stratification or branch synthesis
```

## Next

Pre-register:

```text
m2253-paper-route-current-sim-offtrack-recovery-corridor-selected-checkpoint-outcome-localization-implementation
```
