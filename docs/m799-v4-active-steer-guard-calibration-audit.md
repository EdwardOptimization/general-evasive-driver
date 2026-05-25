# M799 V4 Active Steer Guard Calibration Audit

## Purpose

M799 audits the M798 low-margin guard-corpus blocker before any further
residual calibration objective, replay run, PPO, or checkpoint promotion.

The question is:

```text
Did M798 block for a valid source-diversity reason, and what should the next
blocker be?
```

This milestone is audit-only:

```text
no training
no replay rerun
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Cleanliness Check

M798 preserved the registered no-training invariants after the guard-corpus
gate failed:

```text
actor_backbone_changed: false
base_residual_head_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
```

The created calibrator artifact is only an initialized reproducibility artifact:

```text
calibrator_parameter_count: 2146
optimizer_updates_only_calibrator: true
```

No optimizer step occurred, so M798 did not mutate the actor, M761 residual
head, or calibrator weights through training.

## Blocker Evidence

M798 selected low-margin guard rows from the M795 parent replay using:

```text
branch == normal
alpha == 0.2
and (
  min_clearance_margin <= 0.00005
  or known active boundary source
)
```

The resulting corpus failed every source-diversity requirement:

```text
low_margin_guard_row_count: 12
low_margin_unique_seed_count: 1
low_margin_unique_source_index_count: 1
low_margin_unique_fault_pair_count: 1
low_margin_max_seed_dominance: 1.0

required unique seeds: 8
required unique source_index values: 8
required unique fault-family pairs: 4
required max seed dominance: 0.25
```

All accepted rows are variants of the same public active source:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
normal margin: +0.000003618
```

The 12 rows differ only by contrast/intervention grouping around this same
normal boundary source. They do not form a source-diverse low-margin guard
surface.

## Interpretation

M798 is a valid process-positive blocker. The guard prevented the branch from
training a new active-steer residual calibrator on a single public active source
that has already dominated multiple recent diagnostics.

This is not evidence that active-steer guarding is impossible. It is evidence
that the current parent replay/corpus stack does not contain enough
source-diverse low-margin normal rows to fairly test the M797 objective.

The blocker should be classified as:

```text
scenario_sampling_failure
objective_overfit risk if bypassed
private_holdout_contamination risk if tuned against the single public source
```

## Supported Claims

M799 supports:

```text
1. M798 stopped for the intended source-diversity reason, not because of a
   training instability or checksum mutation.

2. The active-source row at seed 77025/source_index 12 should remain a
   diagnostic boundary row, but it must not be the sole veto or sole training
   target for the next calibrator.

3. Further residual calibration is under-supported until a source-diverse
   low-margin normal guard corpus is mined.

4. PPO and checkpoint promotion remain blocked.
```

## Falsified Claims

M799 falsifies:

```text
1. Current M795/M773 artifacts already contain enough source-diverse
   low-margin normal rows for active-steer guard training.

2. M798 should continue by weakening the low-margin diversity thresholds.

3. The next highest-leverage step is another residual-gate coefficient tweak.

4. A single public active source can support a credible self-identification
   guard claim.
```

## Decision

M799 accepts the M798 blocker as valid:

```text
v4_active_steer_guard_low_margin_corpus_blocked
```

The branch should pivot from calibrator-objective tuning to corpus coverage:

```text
next: m800-v4-low-margin-source-diverse-corpus-refresh-design
```

M800 should design a no-training source-diverse low-margin normal-boundary
corpus refresh. It should explicitly target a broader set of seeds, source
indices, and fault-family pairs around near-boundary normal margins before any
new active-steer guard training is attempted.

## M800 Design Requirements

M800 should remain design-only and should require the implementation milestone
to produce:

```text
low_margin_guard_candidates.csv
accepted_low_margin_guard_rows.csv
summary.json
```

Minimum acceptance targets should include:

```text
accepted low-margin normal guard rows >= 80
unique seeds >= 8
unique source_index values >= 8
unique fault-family pairs >= 4
max single seed dominance <= 0.25
active seed/source included but capped
```

If the refreshed corpus is still sparse, the next step should broaden or
retarget scenario sampling. It should not weaken the diversity thresholds or
tune the calibrator only on seed `77025` / source index `12`.

## Final State

M799 does not change any driver checkpoint or model parameters. It only records
that M798's corpus blocker is real and routes the next milestone toward
source-diverse low-margin corpus refresh.

PPO, promotion, and further residual calibration remain blocked until the corpus
coverage issue is resolved.
