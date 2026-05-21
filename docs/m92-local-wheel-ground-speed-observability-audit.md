# M92 Local Wheel Ground-Speed Observability Audit

This placeholder keeps the M92 research task concrete and traceable. The design
details are in `docs/m92-local-wheel-ground-speed-input-plan.md`.

## Planned Work

Implement and evaluate observation profiles that expose:

```text
Romega_i
v_parallel_i
optional v_perp_i
optional fixed-scale Romega_i - v_parallel_i
```

without exposing:

```text
slip_ratio
slip_angle
ABS/TCS/ESC flags
tire saturation labels
mu
true tire force
oracle feasibility
```

## Status

Planned. No experiment has been run yet.

M91-I remains the current decision for PPO-facing input: use the clean no-wheel
human-view response stream until M92 proves a cleaner wheel/local-ground-speed
profile adds stable self-identification evidence.
