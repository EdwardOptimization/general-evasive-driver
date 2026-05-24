# M585 BC5660 History Intervention Design

## Purpose

M585 designs the next proof layer after M582/M583/M584:

```text
M582/M583: zero-current-response degradation is strong.
M582/M583: reset-hidden degradation is weak.
M584: current-response dependence is supported, accumulated hidden-state
      self-ID is not yet proven.
```

This milestone is design-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Existing Tool Path

No new tool is required before the next run.

The existing staged path is:

1. `autodrift.matched_current_response_ambiguity`

   Mines pairs whose current observation or current response/context is close
   but whose future response targets differ. Output:

   ```text
   matched_pairs.csv
   candidate_pairs.csv
   target_summary.csv
   summary.json
   ```

2. `autodrift.matched_history_intervention_gate`

   Action-level screen on matched pairs. Existing variants include:

   ```text
   reset_hidden
   wrong_matched_history
   delayed_history
   zero_current_response
   zero_action_history
   ```

   This is useful for calibration, but action-distance alone is not enough for
   a self-ID claim.

3. `autodrift.persistent_wrong_history_intervention_gate`

   Outcome-level gate on matched pairs. Existing variants include:

   ```text
   normal
   wrong_once
   wrong_hold_4 / wrong_hold_8 / wrong_hold_16
   wrong_late_4_hold_4 / wrong_late_8_hold_4 / wrong_late_4_hold_8
   wrong_late_2_once / wrong_late_4_once / wrong_late_8_once / wrong_late_12_once
   wrong_reseed_4
   reset_hidden
   zero_current_response
   ```

   This is the right outcome gate because it measures terminal success,
   collision, obstacle completion, and clearance margin after hidden-state
   intervention.

## Design Principle

The next diagnostic must not ask only:

```text
Does removing current response hurt?
```

That has already been answered positively.

It must ask:

```text
Given a similar current scene/current response, does injecting delayed or wrong
history change closed-loop outcome?
```

The stronger evidence is outcome-related:

```text
normal-history margin > wrong-history margin
normal-history success > wrong-history success
wrong/delayed history creates collision/completion/margin degradation
```

Action distance is a screen, not the final evidence.

## M586 Pair Mining

M586 should mine BC5660 matched-current pairs on both same-distribution and
moderate-OOD route distributions.

Fresh route command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --probe-seeds 25560,25561,25562,25563 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m586_bc5660_matched_current_fresh_seed25560
```

Moderate-OOD command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/eval_m574_moderate_ood_l3.json \
  --probe-seeds 25660,25661,25662,25663 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m586_bc5660_matched_current_ood_seed25660
```

M586 pass criteria:

```text
At least one surface:
  accepted pairs >= 60
  accepted physical pairs >= 10
  accepted left steps >= 5
  accepted source obstacle buckets >= 4

Preferred:
  both fresh and OOD surfaces pass the same thresholds
```

If neither surface passes, M586 should not move to intervention. It should
classify the result as `source_narrow_or_no_matched_current_surface` and design
an expanded mining run with more probe seeds or a wider visible quantile.

## M587 Action Screen

If M586 finds at least one source-diverse pair surface, M587 should run
`matched_history_intervention_gate` as a cheap action-level screen.

Suggested command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config <same env config as pair surface> \
  --pairs-csv <matched_pairs.csv from M586> \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 120 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir <m587 run dir>
```

Action-screen diagnostic:

```text
wrong_matched_history and/or delayed_history should show non-trivial action
distance on accepted pairs, while zero_current_response remains a positive
control.
```

M587 should not claim self-ID from action distance alone. It should only decide
whether the surface is worth outcome rollout.

## M588 Outcome Gate

If M587 has enough signal, M588 should run
`persistent_wrong_history_intervention_gate`.

Suggested command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.persistent_wrong_history_intervention_gate \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config <same env config as pair surface> \
  --pairs-csv <matched_pairs.csv from M586> \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 160 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir <m588 run dir>
```

Outcome diagnostic pass:

```text
At least one wrong/delayed-history variant has:
  proof_candidate_count >= 16
  success_or_collision_or_completion_rows >= 4
  probe_seed_count >= 4
  obstacle_label_count >= 2
  target_count >= 2
  single_seed_share <= 0.50
  single_label_share <= 0.70
```

Interpretation:

- If `wrong_once` or late one-shot variants pass, hidden history matters at the
  critical instant in a less artificial way.
- If only clamped hold variants pass, wrong belief can be outcome-critical, but
  the natural recurrent policy may correct quickly.
- If only `zero_current_response` passes, BC5660 is likely current-response
  dependent but not history-intervention sensitive on this pair surface.
- If no variant passes, this branch should mine a sharper source surface before
  any PPO or promotion.

## Guardrails

M586-M588 must not:

```text
train or update checkpoint weights
promote a checkpoint
change actor inputs
use hidden vehicle parameters as deployable inputs
count action distance alone as outcome proof
count zero-current degradation as wrong-history proof
retune thresholds after seeing the run
```

## Decision

```text
bc5660_history_intervention_design_admit_pair_mining
```

M585 passes because it identifies the concrete existing tool path and
pre-registers outcome-based history-intervention gates before any run.

## Next

```text
M586: mine BC5660 matched-current pair surfaces on fresh route and moderate-OOD.
```
