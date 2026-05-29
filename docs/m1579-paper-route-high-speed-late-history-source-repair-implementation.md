# M1579 Paper-Route High-Speed/Late History-Source Repair Implementation

## Summary

M1579 implemented and ran the bounded high-speed/late history-source repair
designed in M1578.

Decision:

```text
high_speed_late_history_source_repair_smoke_matched_pair_shortfall_route_to_audit
```

The implementation ran cleanly, but it did not reach the intervention stage:

```text
matched_current_hidden_divergent_pair_count: 0
null_result_classification: matched_pair_shortfall
```

This is a useful negative result. The high-speed/late pressure sources produced
many replay-ok anchors, but did not produce target-donor pairs that were both
current-response matched and hidden-history divergent under the pre-registered
screen.

## Commands

```bash
PYTHONPATH=src python -m pytest tests/test_high_speed_late_history_source_repair.py -q
```

Result:

```text
3 passed
```

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m autodrift.high_speed_late_history_source_repair \
  --output-dir runs/m1579_high_speed_late_history_source_repair_smoke \
  --seed 1877 \
  --seed-count 6 \
  --max-source-specs 360 \
  --max-anchor-candidates 384 \
  --max-anchors 192 \
  --continuation-steps 64
```

## Implementation

New code:

```text
src/autodrift/high_speed_late_history_source_repair.py
tests/test_high_speed_late_history_source_repair.py
```

The implementation adds:

```text
high-speed history-pressure modes;
late-reveal history-pressure modes;
repair windows including reveal_plus_2, reveal_plus_8, and decision_minus_32;
matched-current / hidden-divergent donor screen;
screen-rejected donor diagnostics;
M1576-compatible history-vs-control acceptance if pairs exist.
```

No actor input changed.

## Artifacts

```text
runs/m1579_high_speed_late_history_source_repair_smoke/source_spec_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/anchor_candidate_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/matched_donor_pair_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_intervention_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_anchor_rows.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_source_family_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/history_sensitive_window_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/control_substitution_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/guardrail_summary.csv
runs/m1579_high_speed_late_history_source_repair_smoke/summary.json
```

## Summary Metrics

```text
source_spec_count: 360
anchor_candidate_count: 384
replay_ok_anchor_count: 267
target_anchor_count: 192
donor_pair_count: 0
matched_current_hidden_divergent_pair_count: 0
strict_matched_pair_count: 0
fallback_matched_pair_count: 0
intervention_row_count: 0
high_speed_or_late_history_sensitive_anchor_count: 0
clean_high_speed_or_late_history_sensitive_anchor_count: 0
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
null_result_classification: matched_pair_shortfall
guardrail_violation_count: 0
```

Screen counts:

```text
screen_rejected: 24894
strict_matched_current_hidden_divergent: 0
fallback_matched_current_hidden_divergent: 0
```

## Screen Diagnostics

High-speed target rows:

```text
screen rows: 12012
response/action L2 min: 0.022386638660922765
response/action L2 mean: 1.0432750393278742
response/action L2 max: 2.4707454143905885
hidden L2 min: 0.06055958470854052
hidden L2 mean: 1.3871890049023916
hidden L2 max: 3.570538068071364
```

Late-reveal target rows:

```text
screen rows: 12882
response/action L2 min: 0.022386638660922765
response/action L2 mean: 0.9569601851123755
response/action L2 max: 2.4707454143905885
hidden L2 min: 0.06055958470854052
hidden L2 mean: 1.2332635820060684
hidden L2 max: 3.385703151579344
```

The screen failed because the candidate pool did not combine small enough
current response/action distance with large enough hidden distance. A relaxed
diagnostic screen would have found only a small number of possible pairs:

```text
response/action L2 <= 0.75 and hidden L2 >= 2.0: 15 pairs
```

This threshold was not pre-registered, so it is diagnostic only and must not be
used to claim a pass.

## Interpretation

Supported:

```text
the high-speed/late source repair implementation runs;
source generation produced many replay-ok anchors;
the pre-registered matched-current hidden-divergent screen is too strong for
the generated high-speed/late source pool;
M1579 did not produce history-intervention evidence because no accepted donor
pairs existed.
```

Unsupported:

```text
high-speed history sensitivity;
late-reveal history sensitivity;
source-diverse self-ID;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

This is a pairability/source-design failure. It is not an actor-input issue and
not a PPO/training issue.

## Route Decision

Do not route directly to:

```text
threshold relaxation;
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout.
```

Route to:

```text
m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair
```

M1580 must synthesize the branch and decide the next route before another
implementation milestone.

## Guardrails

```text
history_interventions_executed: true
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair
```
