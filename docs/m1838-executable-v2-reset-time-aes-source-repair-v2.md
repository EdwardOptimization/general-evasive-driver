# M1838 Executable V2 Reset-Time AES Source Repair V2

- status: completed
- decision: `reset_time_aes_source_repair_v2_clean_fail_route_to_result_audit`
- branch: `paper_route_executable_v2_reset_time_aes_source_repair_v2`
- artifact: `runs/m1838_executable_v2_reset_time_aes_source_repair_v2/summary.json`
- result class: `reset_time_aes_source_repair_v2_fail`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1838 ran the exact command registered in M1837. The command applies the M1836
no-reset source repair v2 helper to the M1825 repaired payload and M1828 reset
rows. It scores source-level AES repair candidates using reset-time sampler
replay. It does not call environment reset or rollout.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_time_aes_source_repair_v2 \
  --repaired-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1838_executable_v2_reset_time_aes_source_repair_v2 \
  --target-source-count 2 \
  --target-profile-count 12 \
  --target-repaired-spec-count 36 \
  --main-attempt-budget 10000 \
  --next-blocker m1839-executable-v2-reset-time-aes-source-repair-v2-result-audit
```

## Output Artifacts

```text
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/summary.json
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_targets.csv
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_candidate_scores.csv
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_specs.json
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_specs.csv
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_claim_boundary.csv
```

## Summary

| field | value |
| --- | ---: |
| `result_class` | `reset_time_aes_source_repair_v2_fail` |
| `target_source_count` | 2 |
| `target_profile_count_total` | 24 |
| `selected_source_count` | 2 |
| `accepted_source_count` | 0 |
| `accepted_profile_count_total` | 0 |
| `repaired_spec_count` | 36 |
| `unchanged_non_target_count` | 12 |
| `reset_ready_spec_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

The selected-source summary has:

```text
attempt_count_total = 240000
attempt_count_by_label = {"aeb_feasible": 240000}
attempt_count_by_reject_reason = {"aeb_feasible_rejected": 240000}
summary_aggregation_version = "row_and_attempt_counts_v1"
```

The candidate score table is broader than the selected-source summary:

```text
candidate rows = 10
candidate attempt total = 1200000
candidate accepted profile counts = {0}
candidate names =
  original_reset_replay
  aes_reset_close_band
  aes_reset_close_medium_band
  aes_reset_threshold_band
  aes_reset_wide_search_band
```

All 10 candidate rows have `accepted_profile_count=0`. Every attempted candidate
was classified as `aeb_feasible` and rejected by `require_aeb_infeasible`.

## Interpretation

M1838 is a clean negative result. It proves that M1836's static source-level
candidate families still do not hit a reset-time AES-only band for the two
persistent AES sources.

This is not a reset failure, rollout failure, or policy failure. It is a task
support and sampler search failure:

- source-level candidate scoring ran;
- output artifacts are complete;
- guardrails are clean;
- all candidate families remain in the AEB-feasible region at reset time.

The next audit should decide whether to:

1. implement a reset-time feasibility scan that conditions candidate ranges on
   observed reset speed/mu distributions;
2. expand the candidate search toward closer and/or wider obstacles only if the
   classifier shows an AES-only feasible region exists;
3. synthesize and pivot if the current source metadata cannot support AES-only
   rows under the executable reset task.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- source repair v2 execution completed;
- M1836 static candidate families failed cleanly on project artifacts;
- detailed candidate score table shows 1.2M AEB-feasible rejections and zero
  accepted AES profiles;
- result audit is required before any further repair or reset preflight.

Unsupported:

- repaired reset feasibility;
- reset-time repair success;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Follow-Up

Route to:

```text
m1839-executable-v2-reset-time-aes-source-repair-v2-result-audit
```

M1839 should audit the clean fail and decide whether the next branch is a
reset-time feasibility scan / dynamic source repair v3 or a branch synthesis
and pivot.
