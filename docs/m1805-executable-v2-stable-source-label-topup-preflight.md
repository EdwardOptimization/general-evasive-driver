# M1805 Executable V2 Stable Source-Label Top-Up Preflight

- status: completed
- decision: `stable_source_label_topup_preflight_pass_route_to_result_audit`
- artifact: `runs/m1805_executable_v2_stable_source_label_topup_preflight/summary.json`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_stable_source_label_topup_preflight \
  --replacement-needs runs/m1800_executable_v2_label_source_compatibility_preflight/replacement_need_rows.csv \
  --source-label-support runs/m1800_executable_v2_label_source_compatibility_preflight/source_label_support.csv \
  --bounded-panel-specs runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json \
  --output-dir runs/m1805_executable_v2_stable_source_label_topup_preflight \
  --target-topup-count 3 \
  --next-blocker m1806-executable-v2-stable-source-label-topup-result-audit
```

## Result

M1805 matched the pre-registered M1804 counts:

| field | value |
| --- | ---: |
| `stable_topup_target_count` | 3 |
| `target_missing_profile_count_total` | 36 |
| `stable_candidate_source_count` | 6 |
| `candidate_row_count` | 5 |
| `direct_replacement_count` | 0 |
| `new_materialization_need_count` | 3 |
| `labels_enter_actor_input_count` | 0 |
| `guardrail_violation_count` | 0 |

Candidate class counts:

| candidate class | rows |
| --- | ---: |
| `metadata_only_untrusted` | 2 |
| `near_existing_candidate` | 3 |
| `exact_existing_candidate` | 0 |

Claim flags:

```text
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Top-Up Targets

| target | label | hidden | road | timing | lateral | missing profiles | candidate rows | result |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `m1771-bp1-00` | `aes_feasible` | `nominal` | `nominal` | `medium` | `center` | 12 | 3 | no direct replacement |
| `m1771-bp1-02` | `aes_feasible` | `friction_step` | `nominal` | `late` | `center` | 12 | 2 | no direct replacement |
| `m1771-bp1-05` | `aeb_feasible` | `brake_variation` | `moderate` | `late` | `wide_offset` | 12 | 0 | no candidate in current source pool |

## Candidate Evidence

The candidate rows confirm that metadata alone is not trusted:

- `m1771-bp1-00/aes_feasible` has one exact metadata match, but M1800 observed
  it as `unsupported_systematic`; it remains `metadata_only_untrusted`.
- `m1771-bp1-02/aes_feasible` has the same exact metadata-only failure mode.
- `m1771-bp1-00/aes_feasible` also has two `near_existing_candidate` rows
  sharing the hidden bucket but not the road/timing/lateral buckets.
- `m1771-bp1-02/aes_feasible` has one `near_existing_candidate` with matching
  hidden bucket but shifted geometry.
- `m1771-bp1-05/aeb_feasible/brake_variation` has no candidate in the current
  M1771 stable source pool.

No candidate is admissible as a direct replacement, and all three targets remain
in `stable_new_materialization_need_rows.csv`.

## Artifact Set

M1805 wrote:

```text
summary.json
stable_topup_targets.csv
stable_candidate_source_pool.csv
stable_topup_candidate_rows.csv
stable_new_materialization_need_rows.csv
stable_topup_claim_boundary.csv
```

## Interpretation

M1805 passes as a planning preflight, but it does not repair executable v2 reset
feasibility. The current stable source pool cannot replace the systematic
stable source-label gaps without either:

- materializing new stable sources with observed label support; or
- running targeted reset probes over candidate sources and proving support.

Because `direct_replacement_count=0`, the branch should not proceed directly to
measured execution or controller-family ranking.

## Route Decision

Route to:

```text
m1806-executable-v2-stable-source-label-topup-result-audit
```

M1806 should audit whether the next step is stable source materialization
design, targeted reset-probe design, helper repair, or a broader branch
synthesis.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-reset stable source-label top-up preflight result;
- current stable source pool has no trusted direct replacement for the three
  stable systematic gaps;
- stable new-materialization or targeted reset-probe route remains necessary.

Unsupported:

- repaired reset feasibility pass;
- stable source materialization result;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
