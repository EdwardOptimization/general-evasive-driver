# M551 Route-Health Screen Redesign

## Purpose

M551 redesigns the pre-public route-health screen after M550 showed that the
old M545 screen was too weak.

M550 result:

```text
M549 selected L3 passed 5-episode route health.
M549 selected L3 still failed public frozen-source diagnostics versus L0/L2.
```

This milestone is design-only. It does not train, evaluate public rows, or
promote a checkpoint.

## What Failed

The old M545 route-health screen was:

```text
episodes = 5
return_mean > 25.0
termination_rate < 1.0
```

This admitted:

```text
runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt
return_mean = 27.858686
termination_rate = 0.8
min_clearance_margin_mean = 0.594595
```

M550 then showed that this checkpoint is still public-surface negative:

```text
M549 L3 - L0 success delta = -0.076203
M549 L3 - L0 margin delta  = -0.235235

M549 L3 - L2 success delta = -0.141711
M549 L3 - L2 margin delta  = -0.629009
```

Therefore route pass alone is not enough. The pre-public screen must compare a
candidate against the same route distribution as L0/L2, with more episodes and
metrics aligned to obstacle success, collision, and clearance margin.

## Route-Screen V2

M552 should implement and run a retrospective route-screen v2 before any new
training branch.

Route-screen v2 should evaluate:

```text
l0_s3540
l2_s3540
l3_m542_s3540
l3_m549_fast2816
```

on a public-neutral route distribution:

```text
env config = configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json
episodes = 64 minimum
seed = fixed before launch
device = cpu
```

The screen should use `autodrift.evaluate`, not `train_ppo.evaluate_actor`,
because `autodrift.evaluate` reports obstacle success, collision, and clearance
margin.

## Selection Rule V2

For interval-checkpoint selection in future repair pilots, do not rank by route
`return_mean` alone.

Use lexicographic screening:

1. Reject any checkpoint with `success_rate < l0_success_rate`.
2. Reject any checkpoint with `min_clearance_margin_mean < l0_margin_mean`.
3. Reject any checkpoint whose collision rate exceeds L0 by more than `0.02`.
4. Among remaining checkpoints, rank by:
   - higher success rate;
   - higher mean clearance margin;
   - lower collision rate;
   - higher return.

If no checkpoint clears L0 on route-screen v2, public frozen-source eval is
blocked.

## L2 Boundary

L2 remains the strong finite-window baseline. Passing L0 is only the minimum
screen for public diagnostics.

For a checkpoint to justify matched repeat after public diagnostics, it must
also be competitive with L2:

```text
route_screen_v2:
  candidate_success_delta_vs_l2 >= -0.02
  candidate_margin_delta_vs_l2 >= -0.05

public_diagnostic:
  candidate_success_delta_vs_l2 >= 0 or clear mechanism reason to continue
  candidate_margin_delta_vs_l2 >= 0 or clear mechanism reason to continue
```

If a candidate passes L0 but remains far below L2, the correct interpretation is
still:

```text
finite-window history remains stronger under the current training recipe.
```

## Public Diagnostics Boundary

Public frozen-source rows remain public diagnostics. They can identify failures
and guide the harness, but they cannot become checkpoint-selection data for a
private claim.

If M550 public rows are used to redesign route-screen v2, then any later paper
or promotion claim must still require a fresh holdout after the recipe and
selection rule are frozen.

## M552 Admission

M551 admits a retrospective route-screen v2 check:

```text
m552-route-screen-v2-retrospective
```

M552 should answer:

```text
Would route-screen v2 have rejected the M549 selected checkpoint before M550?
```

If yes, the workflow fix is validated and can be used before another training
branch. If no, the project needs a stronger public-neutral scenario screen
before more L3 repair training.

## Decision

```text
route_health_screen_redesign_admit_m552_retrospective
```
