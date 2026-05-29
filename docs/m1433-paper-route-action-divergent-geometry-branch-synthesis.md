# M1433 Paper-Route Action-Divergent Geometry Branch Synthesis

## Summary

M1433 synthesizes the M1423-M1432 action-divergent outcome-pressure and
geometry-selector branch.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
action_divergent_geometry_synthesis_promote_to_preflight_validation
```

M1433 does not run source preflight, replay, outcome interventions, training,
PPO, promotion, private holdout, corpus export, or actor-input changes.

## Evidence Summary

M1423-M1424 built the proxy source constructor for matched-current,
action-divergent, terminal-margin-sensitive cases. M1425 showed the constructor
can find source-diverse action-divergent rows:

```text
candidate_rows: 256
outcome_pressure_rows: 846
candidate_unique_source_seeds: 12
candidate_unique_capability_pairs: 16
candidate_unique_reveal_buckets: 52
outcome_pressure_unique_source_seeds: 7
outcome_pressure_unique_capability_pairs: 16
outcome_pressure_unique_reveal_buckets: 31
history_positive_rows: 0
```

M1426 audited the result as proxy-limited: shared-margin pressure preserves the
normal-vs-variant margin gap, so it cannot validate actual terminal sensitivity.

M1427-M1428 designed and implemented bounded relocation replay. M1429 ran the
first replay smoke:

```text
selected_candidate_rows: 128
actual_replay_rows: 384
history_positive_rows: 0
control_positive_rows: 0
normal_failed_rows: 177
selected_unique_source_seeds: 3
selected_unique_variants: 1
selected_max_single_seed_share: 0.75
source_body_x_median: -1.678050
relocated_body_x_clipped_groups: 126 / 128
```

M1430 audited M1429 as selector failure, not self-ID evidence. M1431 designed a
geometry-aware selector. M1432 implemented optional geometry preflight and
focused tests:

```text
focused_test_result: 8 passed
geometry-aware selector default enabled: false
replay_started: false
training_started: false
actor_input_contract_changed: false
```

## Supported Claims

The branch supports these bounded claims:

```text
1. matched-current action-divergent public rows exist in the M1419/M1421 source family;
2. proxy pressure alone is insufficient for history-positive terminal evidence;
3. bounded relocation replay tooling can execute actual rollout rows;
4. M1429's negative is dominated by source geometry and selector concentration;
5. geometry-aware preflight infrastructure now exists behind an explicit option;
6. no actor input, actor parameter, checkpoint, training, PPO, private holdout, or corpus-export shortcut was used.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. shared-margin proxy pressure is enough to establish history-positive rows;
2. M1429 zero history-positive rows prove history is unnecessary;
3. the M1429 selector is valid for forward-obstacle replay evidence;
4. a full replay run should proceed without first validating source geometry;
5. these artifacts justify training, corpus export, promotion, or paper-level self-ID claims.
```

## Failure Taxonomy Summary

Observed failure modes:

```text
scenario_sampling_failure:
  M1425/M1429 did not produce source-diverse history-positive terminal evidence.

proxy_limitation:
  M1425 shared-margin pressure cannot change normal-vs-variant margin gaps.

geometry_selector_failure:
  M1429 selected mostly behind-vehicle/clipped obstacle rows and one history variant.

public_row_overuse_risk:
  M1425/M1429 public rows have now been used for multiple repairs and diagnostics.
```

The dominant current blocker is not PPO or actor architecture. It is source
validity: before actual replay can be interpreted, the project must prove that
the selected rows are forward, unclipped, source-diverse, and variant-diverse.

## Public-Gate Overfit Risk

Risk level:

```text
medium_to_high
```

Reasons:

```text
M1425 rows are public and repeatedly inspected;
M1429 selected rows were seed-concentrated;
M1429 selected only warmup_removed;
geometry-aware selector thresholds were designed after seeing M1429 clipping;
no private holdout or paper-level evaluation is involved.
```

Mitigation:

```text
run only public diagnostic preflight next;
do not train or export corpus from preflight rows;
do not claim self-ID from preflight-only output;
if preflight fails, pivot to source mining instead of threshold lowering.
```

## Next Branch Decision

Promote from:

```text
paper_route_action_divergent_outcome_pressure_design
```

to:

```text
paper_route_geometry_aware_preflight_validation
```

The next branch should first expose and test a preflight-only command. It should
not run full bounded replay yet, because M1432's current CLI executes replay
after selection.

Admit:

```text
m1434-paper-route-geometry-preflight-only-command-implementation
```

M1434 should implement a no-replay preflight command or mode that writes
geometry preflight rows, selected rows, rejected rows, diversity summaries, and
summary JSON. M1435 can then run a public preflight smoke if M1434 passes.

## Guardrails

M1433 guardrail status:

```text
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
