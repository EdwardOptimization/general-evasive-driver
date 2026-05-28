# M1364 Paper-Route Bidirectional Broader Public Replay Design

## Summary

M1364 designs the broader public replay escalation for the M1362 alpha `0.1`
candidate.

Decision:

```text
bidirectional_broader_public_replay_design_admit_implementation
```

The M1362 checkpoint has passed exact metrics plus two public replay preflight
surfaces. The next evidence level is broader public replay, not PPO, private
holdout, or promotion.

## Candidate

Base checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Candidate checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

## Tool

Use the existing public replay wrapper:

```text
autodrift.public_base_controlled_fusion_candidate_replay_gate
```

The module name is historical, but the wrapper already runs the gate stack this
branch needs:

```text
six public replay surfaces
source-diverse protected diagnostic
old-key neighborhood diagnostic
behavior seeds 9505 and 9506
```

The hardcoded labels inside that wrapper are not claim labels for this branch;
the manifest and run directory should record the actual base and candidate
checkpoint paths.

## Gate Order

Interpret results in this order:

```text
1. actor input contract unchanged
2. six public replay surfaces
3. source-diverse protected diagnostic
4. old-key neighborhood diagnostic
5. behavior seeds 9505 and 9506
```

The wrapper may compute diagnostics and behavior even if replay fails. The
research decision must still obey the order above: a replay failure blocks any
behavior or protected diagnostic from being used as promotion evidence.

## Replay Surfaces

M1365 should run these six public replay surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

The candidate must not regress:

```text
normal_success_delta >= 0.0
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
success_drop_count_delta >= 0
```

## Behavior

If replay gates pass, behavior seeds `9505` and `9506` should retain:

```text
candidate_success_rate >= base_success_rate
candidate_termination_rate <= base_termination_rate
candidate_success >= reset_success >= zero_all_success
```

Behavior is not a substitute for proof replay. It is a regression guard after
proof gates.

## Promotion Policy

M1365 must not promote. Even if it passes, the correct next step is a result
audit deciding whether to run a promotion-style public gate, source-diverse
protected refresh, or repeat.

## Guardrails

M1364 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1365-paper-route-bidirectional-broader-public-replay
```
