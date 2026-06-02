# M2385 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Candidate Config Generation Materialization

- status: completed
- result class: `current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass`
- manifest: `experiments/manifests/m2385-paper-route-current-sim-dual-axis-offtrack-guardrail-candidate-config-generation-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation.py`
- focused tests: `2 passed`
- summary: `runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json`
- run-dir candidate config generation: `true`
- active config overwrite: `false`
- candidate config files outside run dir: `0`
- environment load/reset/rollout: `false/false/false`
- repair execution/training/replay/PPO: `false/false/false/false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`
- next: `m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis`

## Result

M2385 implemented and ran the run-dir-only candidate config generation
materializer from M2382 application-plan artifacts. It wrote candidate JSON
artifacts only under:

```text
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_configs
```

Counts:

```text
source_candidate_application_spec_count: 54
candidate_config_file_written_count: 54
candidate_config_files_outside_run_dir_count: 0
source_reward_patch_reference_count: 162
source_curriculum_patch_reference_count: 54
source_guardrail_patch_reference_count: 284
mixed_guarded_candidate_requirement_count: 18
candidate_without_reward_overlay_count: 0
candidate_without_curriculum_overlay_count: 0
candidate_without_guardrail_overlay_count: 0
active_config_overwrite_count: 0
active_config_patch_application_count: 0
loaded_into_environment_count: 0
environment_reset_count: 0
guardrail_violation_count: 0
```

Candidate repair-family counts:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
```

Generated artifacts:

```text
candidate_config_generation_manifest.json
candidate_config_rows.csv
candidate_patch_reference_matrix.csv
candidate_guardrail_scope_rows.csv
candidate_configs/*.json
active_config_safety_report.json
claim_boundary.csv
summary.json
```

## Claim Boundary

Allowed claim:

```text
Run-dir-only candidate config artifacts were generated from audited
application-plan artifacts without active config overwrite or execution.
```

Still blocked:

```text
active config overwrite
candidate config loading into an environment
environment reset or rollout
measured execution
repair execution
training/replay/PPO
support-policy or controller-family ranking
winner selection
scenario redesign executed claim
training repair success claim
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Interpretation

M2385 is infrastructure progress only. It does not improve or evaluate a
driver, and it does not validate whether the generated candidate configs can be
sampled, reset, rolled out, repaired, or ranked.

Because the post-M2380 branch has reached the local-search non-evidence limit,
the next step must be a branch synthesis rather than another ordinary design or
audit milestone.
