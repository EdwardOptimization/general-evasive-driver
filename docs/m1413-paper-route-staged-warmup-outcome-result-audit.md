# M1413 Paper-Route Staged Warmup Outcome Result Audit

## Summary

M1413 audits the sparse M1412 staged warmup outcome result before any new run.

Decision:

```text
staged_warmup_outcome_audit_route_to_clear_near_boundary_retarget_design
```

M1413 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## What Improved

M1412 is the first warmup/reveal branch result after M1405 to produce any
warmup-history-positive outcome rows:

```text
M1405 warmup_history_positive_rows: 0
M1412 warmup_history_positive_rows: 14
```

The positives are not purely collision-heavy:

```text
clear stratum warmup-history positives: 10
collision stratum warmup-history positives: 4
clear_low_margin warmup-history positives: 0
```

This means staged warmup is a useful task-design direction; it should not be
discarded as only an invasive obstacle artifact.

## What Is Still Not Enough

M1412 does not pass the public-positive history-necessity bar:

```text
required:
  warmup_history_positive_rows >= 48
  accepted_history_seeds >= 12
  accepted_history_capability_pairs >= 6
  accepted_history_reveal_buckets >= 4

observed:
  warmup_history_positive_rows: 14
  accepted_history_seeds: 3
  accepted_history_capability_pairs: 7
  accepted_history_reveal_buckets: 3
```

The accepted rows are seed-thin:

```text
max_single_seed_share: 0.714286
```

Near-boundary evidence is weaker:

```text
accepted_warmup_history_preferred_near_boundary_rows: 2
preferred near-boundary accepted-history seeds: 1
accepted_warmup_history_broad_near_boundary_rows: 4
broad near-boundary accepted-history seeds: 2
```

Wrong-warmup variants remain negative:

```text
wrong_warmup_history_same_reveal positives: 0
same_recent_wrong_warmup_history positives: 0
```

So the result says:

```text
removing or shortening warmup sometimes matters;
injecting the wrong warmup history has not yet produced robust errors.
```

That is below the standard for self-identification.

## Failure Classification

M1413 classifies M1412 as:

```text
scenario_sampling_failure
```

The mechanism signal exists, but the scenario distribution is not yet targeted
enough: too many rows are high-margin or collision-heavy, and too few are
source-diverse near-boundary cases where history should change the outcome.

This is not:

```text
contract_violation
training_instability
private_holdout_contamination
promotion_gate_failure
```

No actor input contract changed.

## Route Decision

M1413 does not admit training or corpus export.

The next route should design a retargeted public source/outcome loop that
preserves the useful clear-stratum signal while increasing near-boundary and
seed diversity.

Next milestone:

```text
m1414-paper-route-clear-near-boundary-warmup-retarget-design
```

The retarget design should consider:

```text
1. reducing warmup gate invasiveness enough to lower collision-source rows;
2. keeping enough warmup command-response evidence to avoid returning to M1405;
3. targeting normal margins in preferred/broad near-boundary bands;
4. keeping clear and collision strata separate in every artifact;
5. making wrong-warmup variants first-class pass/fail diagnostics;
6. blocking training/export until source-diverse outcome positives exist.
```

## Guardrails

The next branch step must not:

```text
train
run PPO
promote
use private holdout
export a corpus
change actor inputs
claim level3 self-identification
optimize only the current 3 accepted-history seeds
```

If the retargeted repeat still produces seed-thin or wrong-warmup-negative
results, the branch should synthesize and pivot rather than keep locally tuning
the same staged gate.
