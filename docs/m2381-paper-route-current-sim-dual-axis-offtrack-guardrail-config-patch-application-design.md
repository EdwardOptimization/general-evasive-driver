# M2381 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Config Patch Application Design

- status: completed
- decision: `config_patch_application_design_admit_artifact_only_application_plan_materializer`
- manifest: `experiments/manifests/m2381-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-design.json`
- parent synthesis: `docs/m2380-paper-route-current-sim-dual-axis-repair-plan-materialization-branch-synthesis.md`
- source summary: `runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/summary.json`
- reset/rollout/measured execution in M2381: `false`
- policy action executed in M2381: `false`
- active config overwritten in M2381: `false`
- config patch application in M2381: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2381 designs an artifact-only application-plan materializer for M2378 overlay
config-patch artifacts. It does not apply patches to active configs and does
not write candidate config copies. The next implementation should write
candidate application-plan artifacts under a run directory only.

Source artifacts:

```text
config_patch_manifest.json
reward_config_patch_rows.csv
curriculum_config_patch_rows.csv
guardrail_config_patch_rows.csv
config_patch_preview.json
claim_boundary.csv
summary.json
```

## Candidate Application Semantics

The materializer should group patch rows by `source_repair_spec_id`:

```text
candidate_application_spec:
  candidate_id: deterministic id from source_repair_spec_id
  source_repair_spec_id: original repair spec id
  repair_family: copied from reward/curriculum patch source
  source_slice_axis/value: copied from source patch rows
  reward_patch_refs: three reward patch ids for the repair spec
  curriculum_patch_ref: one curriculum patch id for the repair spec
  guardrail_patch_scope: all M2378 guardrail patches
  mixed_collision_guardrail_required: true for guarded mixed candidates
  active_config_overwritten: false
  config_patch_applied: false
```

Expected candidate count:

```text
54 source repair specs with reward/curriculum rows -> 54 candidate application specs
```

Expected patch references:

```text
reward patch references: 162
curriculum patch references: 54
guardrail patch references: 284
mixed guarded candidate requirements: 18
```

## Application-Plan Artifact Schema

M2382 should write these files:

```text
application_plan_manifest.json:
  source artifacts, output files, application semantics, guardrail counts,
  blocked routes, and claim boundary.

candidate_application_specs.csv:
  one row per candidate repair spec, with deterministic candidate id and
  source repair metadata.

reward_patch_application_refs.csv:
  links candidate ids to reward overlay patch ids.

curriculum_patch_application_refs.csv:
  links candidate ids to curriculum overlay patch ids.

guardrail_patch_application_refs.csv:
  lists all guardrail patch ids in the global candidate guardrail scope.

mixed_guarded_candidate_requirements.csv:
  one row per mixed guarded candidate, requiring collision guardrail coverage.

config_copy_preview.json:
  deterministic count preview only, not a config file.

claim_boundary.csv:
  same blocked claim boundary extended with config application and active-config
  overwrite blocks.

summary.json:
  result class, count checks, guardrail flags, artifact paths, and next
  blocker.
```

## Pass Gates For M2382

M2382 should pass only if:

```text
source_reward_config_patch_row_count == 162
source_curriculum_config_patch_row_count == 54
source_guardrail_config_patch_row_count == 284
candidate_application_spec_count == 54
reward_patch_reference_count == 162
curriculum_patch_reference_count == 54
guardrail_patch_reference_count == 284
mixed_guarded_candidate_requirement_count == 18
candidate_without_reward_patch_count == 0
candidate_without_curriculum_patch_count == 0
candidate_without_guardrail_scope_count == 0
active_config_overwritten == false
config_patch_applied == false
candidate_config_file_written_count == 0
actor_input_change_count == 0
hidden_oracle_feature_injection_count == 0
profile_specific_tuning_count == 0
repair_execution_started == false
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
training_started == false
replay_started == false
ppo_used == false
ranking_admissible_count == 0
winner_selected_count == 0
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
current_sim_verdict_claim_made == false
guardrail_violation_count == 0
```

## Guardrail Policy

The materializer must fail closed if any of these happen:

```text
active scenario config is overwritten;
candidate config files are written before application-plan audit;
patches are applied rather than referenced;
actor input contract is modified;
hidden/oracle features are introduced;
profile-specific tuning appears;
mixed guarded collision constraints are dropped;
R4 semantics become ordinary avoidance repair;
diagnostic rows become ranking-admissible;
any execution/training/replay/PPO flag is true.
```

## Decision

M2381 routes to:

```text
m2382-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization
```

M2382 should implement the artifact-only application-plan materializer. It
should not apply patches, overwrite active configs, write candidate config
files, run reset/rollout, execute repair, train, replay, use PPO, rank profiles
or packs, select a winner, claim current-sim verdict, or make paper/self-ID
claims.

## Claim Boundary

M2381 may claim only:

```text
A bounded artifact-only config-patch application-plan design has been defined
from audited overlay patch artifacts.
```

Still blocked:

```text
active config overwrite
config patch application
candidate config file generation
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
m2382-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization
```
