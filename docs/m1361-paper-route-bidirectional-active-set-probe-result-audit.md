# M1361 Paper-Route Bidirectional Active-Set Probe Result Audit

## Summary

M1361 audits the M1360 bidirectional active-set probe result.

Decision:

```text
bidirectional_active_set_probe_audit_route_to_interpolation_preflight
```

M1360 is not promotable, but it is not the same failure as M1355. The
bidirectional anchor fixed the wrong-history success-drop collapse. The
remaining public proof failure is a narrower M267/M264 margin-gap regression.

## Positive Evidence

M1360 improved exact source-history metrics more than the M1355 normal-retention
probe:

```text
M1360 combined_loss_delta: -4.7206263688
M1355 combined_loss_delta: -4.6874377849

M1360 group_min_joint_margin_delta: +5.3494348235
M1355 group_min_joint_margin_delta: +5.2968078983

M1360 eval_fold_delta: +4.9267139186
M1355 eval_fold_delta: +4.8873970864
```

M1360 also preserved the two high-level M267/M264 behavior counts:

```text
normal_success_delta: 0.0
success_drop_count_delta: 0
wrong_history_success_delta: 0.0
wrong_safe_required_row_ids: []
```

This is the main improvement over M1355:

```text
M1355 success_drop_count_delta: -5
M1360 success_drop_count_delta: 0
```

The mutation scope is clean:

```text
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
changed only:
  actor_mean.*
  response_context_fusion.0.*
```

## Remaining Failure

M1360 fails M267/M264 only on margin-gap retention:

```text
margin_gap_mean_delta: -0.0012517729
allowed regression:    -0.001
excess regression:      0.0002517729
```

M183/M170 was not run because the pre-registered order stops after M267/M264
failure.

This means the current failure is not:

```text
normal-history collision
wrong-history rows becoming safe
actor input contract violation
forbidden mutation
exact objective regression
```

The remaining issue is that correct-vs-wrong margin separation shrank slightly
too much on the public current-family replay surface.

## Route Decision

The next control variable should be update amplitude before adding a new loss.

Reason:

```text
raw M1360 direction is exact-strong;
raw M1360 keeps normal success and wrong-history failure behavior;
raw M1360 misses the margin-gap threshold by only about 2.5e-4.
```

So M1362 should run an interpolation preflight from M1154 to raw M1360:

```text
base: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
raw:  runs/m1360_bidirectional_active_set_probe/checkpoints/raw_bidirectional_active_set_update.pt
```

The preflight should test exact metrics, M267/M264, and M183/M170 conditional on
M267/M264 pass. It must not promote a checkpoint. If no useful alpha passes, the
branch should route to a gap-aware active-set term rather than coefficient
tuning.

## Guardrails

M1361 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1362-paper-route-bidirectional-active-set-interpolation-preflight
```
