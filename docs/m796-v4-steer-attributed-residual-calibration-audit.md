# M796 V4 Steer-Attributed Residual Calibration Audit

## Purpose

M796 audits M795 before any further residual objective, replay run, PPO, or
checkpoint promotion.

The question is:

```text
Is M795 an actionable steer-attributed candidate, or a clean negative that
requires a different calibration design?
```

This milestone is audit-only:

```text
no replay rerun
no optimizer run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Cleanliness Check

M795 is clean:

```text
positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
```

The M568 actor and M761 residual head were not mutated. Only the
2146-parameter steer/brake calibrator was trained.

## Result Classification

M795 result:

```text
v4_steer_attributed_calibration_component_collapse
```

Candidate counts:

```text
candidate_alpha_count: 0
strong_candidate_alpha_count: 0
limited_candidate_alpha_count: 0
steer_component_selectivity_alpha_count: 0
```

This is not a promotion result and not a PPO starting point.

## What Improved

M795 alpha `0.2` achieved two useful properties:

```text
strict normal retention: pass
normal success/collision: 1.000000 / 0.000000
gap mean: 0.044080
M780 alpha 0.125 gap reference: 0.044047
```

This is better than a simple failure. Compared with earlier alpha `0.2`
attempts, M795 removes the active-source collision while keeping enough
intervention action gap to pass the strong gap reference.

## What Failed

The active source still has too little margin:

```text
M795 alpha 0.2 active margin: +0.000003618
M786 alpha 0.15 active margin reference: +0.000028246
parent alpha 0.125 active margin reference: +0.000009273
```

The gate also failed the intended steer selectivity:

```text
active normal steer gate:       0.668225
active intervention steer gate: 0.665187
active steer contrast:         -0.003038
```

The desired relation was:

```text
active normal steer gate low
active intervention steer gate high
```

M795 learned:

```text
moderate steer gate almost everywhere
high brake gate almost everywhere
fixed-zero throttle
```

This is not the same collapse as M789's generic vector gate. It is more
specific:

```text
steer branch does not separate active normal from intervention.
```

## Interpretation

The important lesson is not "steer-attributed calibration is impossible."

M795 shows:

```text
1. fixed-zero throttle is tolerable on this diagnostic;
2. retaining brake is safe;
3. a moderate steer gate can remove collision;
4. the current objective under-protects active-source margin and under-enforces
   normal/intervention steer contrast.
```

The active boundary guard remained too weak relative to other losses and row
coverage. The active source contributes only a small part of the training set,
and the current design did not oversample source-diverse low-margin normal
rows.

## Supported Claims

M796 supports:

```text
1. M795 is a clean negative, not a tooling artifact.

2. Alpha 0.2 can be made collision-free while preserving strong intervention
   gap, so the branch is not exhausted yet.

3. The next design must be lexicographic or active-guarded: first enforce
   active/low-margin steering safety, then optimize gap.

4. Any next design must use source-diverse low-margin rows, not only the single
   public active source.
```

## Falsified Claims

M796 falsifies:

```text
1. M795 is a candidate checkpoint.

2. The first steer-attributed gate learned the intended active
   normal/intervention steering split.

3. Removing the alpha 0.2 collision is sufficient; active margin still matters.

4. PPO should resume from this branch now.
```

## Next Design Requirements

M797 should be design-only and should not simply tune a coefficient.

It should require:

```text
1. active-source steer gate as a hard or lexicographic constraint;
2. source-diverse low-margin normal rows, not only seed 77025/source_index 12;
3. intervention steer/brake retention after safety is satisfied;
4. exact closed-loop replay gates before any candidate claim;
5. no PPO and no checkpoint promotion.
```

Candidate design directions:

```text
active-source oversampling;
low-margin source-diverse replay weighting;
post-training exact active-steer projection;
trajectory-time steering residual supervision;
two-stage training: active steer safety first, intervention gap second.
```

## Decision

M796 admits one more design milestone:

```text
m797-v4-active-steer-guard-calibration-design
```

The branch continues because M795 produced a useful near miss: collision-free
alpha `0.2` with strong gap, but insufficient active margin and no steer
selectivity.

PPO and checkpoint promotion remain blocked.
