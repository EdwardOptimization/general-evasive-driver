# M142 Critical-Key Guarded Repair

Date: 2026-05-22

## Question

M139 showed that fixed snippet losses and action anchoring can improve while a
near-threshold rollout proof key disappears. M141 then built a cheap replay
guard for the lost key `9944|perturbed|28|28`.

M142 asks whether that guard can be used as a pre-screen for a minimal repair:
admit a tiny fixed-loss improvement only if it preserves the critical key before
running expensive strict miners.

## Method

Interpolate from the M132 s60 repair checkpoint toward the M139 s20/snippet1000
checkpoint:

```text
base:   runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt
target: runs/m139_m136_s20_env20_snip1000_seed7141/optimized_checkpoint.pt
alphas: 0.1, 0.2, 0.3, 0.4, 0.5
```

Artifacts:

```text
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_1.pt
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_2.pt
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_3.pt
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt
runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_5.pt
runs/m142_interpolation_guard_seed9944/summary.json
runs/m142_interpolation_guard_seed9944/policy_summary.csv
runs/m142_interpolation_guard_seed9944/guard_results.csv
runs/m142_m136_interpolation_eval_seed0/policy_summary.csv
runs/m142_m128_interpolation_eval_seed0/policy_summary.csv
runs/m142_behavior_gate_seed9503/policy_summary.csv
runs/m142_interp_a400_strict_60ep_seed9900/summary.json
runs/m142_interp_a400_strict_60ep_seed9920/summary.json
```

## Critical-Key Guard

The protected key is the M140 lost row:

```text
9944|perturbed|28|28
```

Guard outcome:

```text
policy                  accepted / cases   pass
m132_s60                1 / 1              yes
m142_interp_a100        1 / 1              yes
m142_interp_a200        1 / 1              yes
m142_interp_a300        1 / 1              yes
m142_interp_a400        1 / 1              yes
m142_interp_a500        0 / 1              no
m139_s20_snip1000       0 / 1              no
```

The guard therefore identifies `alpha_0_4` as the largest interpolation that
still preserves the near-threshold proof key.

The margin gap on the protected key shrinks monotonically:

```text
m132_s60           0.005196
alpha_0_1          0.005171
alpha_0_2          0.005124
alpha_0_3          0.005069
alpha_0_4          0.005014
alpha_0_5          0.004959  fail
m139_s20_snip1000  0.004675  fail
```

This is exactly the failure mode M141 was meant to catch.

## Fixed-Loss Check

M136 retention-corpus loss:

```text
m132_s60           0.106838
alpha_0_1          0.106824
alpha_0_2          0.106810
alpha_0_3          0.106796
alpha_0_4          0.106782
alpha_0_5          0.106768
m139_s20_snip1000  0.106696
```

M128 combined-corpus loss:

```text
m132_s60           0.252310
alpha_0_1          0.252275
alpha_0_2          0.252240
alpha_0_3          0.252205
alpha_0_4          0.252169
alpha_0_5          0.252134
m139_s20_snip1000  0.251958
```

The fixed-loss gain is tiny. It is useful only as a sanity signal that the
candidate is not a pure revert to M132.

## Behavior Gate

The max guard-pass candidate `alpha_0_4` preserves the M133 behavior surface on
seed `9503`.

```text
policy             normal   reset    zero-response   no-action   clearance mean
m132_s60           0.8625   0.8500   0.8000          0.8625      1.841558
alpha_0_4          0.8625   0.8500   0.8000          0.8625      1.841495
```

The zero-response degradation remains present, while no-action history remains
neutral. This does not strengthen the self-identification claim; it only says
the minimal repair did not visibly break the existing behavior gate.

## Strict Proof Surface

Because `alpha_0_4` passed the cheap guard and behavior retention, it was allowed
to run the strict miners.

Result:

```text
miner seed   selected pairs   selected seeds   snippets
9900         10               8                17
9920         9                8                14
```

This matches the M133 formal repeat thresholds:

```text
M133 seed9900: 10 pairs / 8 seeds
M133 seed9920: 9 pairs / 8 seeds
```

## Decision

M142 is a positive harness result.

`alpha_0_4` is admitted as a guarded repair candidate because it:

- is the largest interpolation that passes the M141 critical-key guard;
- gives a tiny but measurable fixed-loss improvement on M136 and M128;
- preserves M133 behavior success and zero-response degradation on seed `9503`;
- restores the strict M133 proof-surface thresholds on seeds `9900` and `9920`.

It is not a new driver success. The evidence remains limited by the old
perturbed-only proof surface and no-action-neutral behavior. The useful result
is the process: cheap critical-key replay can block near-threshold rollout
regressions before strict miners or PPO continuation.

## Next

Keep `runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt` as the
current guarded repair candidate.

The next research task should not tune PPO freely. Based on the latest input
discussion, the priority is an input-profile audit with a frozen recipe:
driver-like minimal, driver-like minimal without steering torque, raw wheel
speed, and optional `v_parallel_i` as a diagnostic comparison.
