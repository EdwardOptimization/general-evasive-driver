# M2384 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Candidate Config Generation Design

- status: completed
- decision: `candidate_config_generation_design_admit_run_dir_only_materializer`
- manifest: `experiments/manifests/m2384-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-design.json`
- parent audit: `docs/m2383-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization-result-audit.md`
- source summary: `runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/summary.json`
- reset/rollout/measured execution in M2384: `false`
- policy action executed in M2384: `false`
- active config overwritten in M2384: `false`
- candidate config file written in M2384: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2384 designs a run-dir-only candidate config generation materializer from
M2382 application-plan artifacts. It does not generate candidate config files
in M2384. The next implementation may write candidate config JSON files only
under its run directory.

Source artifacts:

```text
application_plan_manifest.json
candidate_application_specs.csv
reward_patch_application_refs.csv
curriculum_patch_application_refs.csv
guardrail_patch_application_refs.csv
mixed_guarded_candidate_requirements.csv
config_copy_preview.json
claim_boundary.csv
summary.json
```

## Candidate Config Semantics

M2385 should generate one candidate config file per candidate application spec:

```text
candidate_configs/<candidate_id>.json
```

Each generated file should contain:

```text
candidate_id
source_repair_spec_id
repair_family
source_slice_axis
source_slice_value
reward_overlay:
  three reward patch references and delta values
curriculum_overlay:
  one curriculum patch reference and multiplier
guardrail_overlay:
  global guardrail scope reference
mixed_guarded_requirements:
  collision guardrail required for guarded mixed candidates
claim_boundary:
  no active config overwrite, no reset/rollout, no repair execution, no ranking
```

The generated candidate config files are artifacts only. They are not loaded
into the environment in M2385 and they do not replace any active config.

## Expected Counts For M2385

```text
source_candidate_application_spec_count: 54
candidate_config_file_written_count: 54
candidate_config_files_outside_run_dir_count: 0
source_reward_patch_reference_count: 162
source_curriculum_patch_reference_count: 54
source_guardrail_patch_reference_count: 284
mixed_guarded_candidate_requirement_count: 18
active_config_overwritten: false
active_config_patch_application_count: 0
environment_reset_started: false
environment_rollout_started: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

## Output Artifact Schema

M2385 should write:

```text
candidate_config_generation_manifest.json:
  source artifacts, output directory, candidate config file list, blocked
  routes, and claim boundary.

candidate_config_rows.csv:
  one row per generated candidate config file.

candidate_patch_reference_matrix.csv:
  candidate-to-reward/curriculum patch reference matrix.

candidate_guardrail_scope_rows.csv:
  candidate-to-global guardrail scope links.

candidate_configs/*.json:
  generated candidate config artifacts under the M2385 run directory only.

active_config_safety_report.json:
  active config path, overwrite flag false, and outside-run-dir count.

claim_boundary.csv:
  blocked claims and admissible artifact-only generation claim.

summary.json:
  result class, count checks, guardrail flags, artifact paths, and next
  blocker.
```

## Guardrail Policy

The materializer must fail closed if any of these happen:

```text
active scenario config is overwritten;
candidate config files are written outside the M2385 run directory;
generated candidate configs drop reward, curriculum, or guardrail references;
mixed guarded collision requirements are dropped;
candidate configs are loaded or reset-tested;
actor input contract is modified;
hidden/oracle features are introduced;
profile-specific tuning appears;
ranking or winner fields become admissible;
any training/replay/PPO flag is true.
```

## Decision

M2384 routes to:

```text
m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization
```

M2385 should implement run-dir-only candidate config generation. It may write
candidate config files inside its run directory, but it must not overwrite
active configs, load configs into the environment, run reset/rollout, execute
repair, train, replay, use PPO, rank profiles or packs, select a winner, claim
current-sim verdict, or make paper/self-ID claims.

M2385 should route to branch synthesis afterward rather than another narrow
audit milestone, because the repair-plan materialization branch will reach the
local-search non-evidence limit.

## Claim Boundary

M2384 may claim only:

```text
A bounded run-dir-only candidate config generation design has been defined
from audited application-plan artifacts.
```

Still blocked:

```text
candidate config generation in M2384
active config overwrite
environment reset or rollout
measured validation
repair execution
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next

Pre-register:

```text
m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization
```
