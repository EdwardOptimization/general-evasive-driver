# M273 M272 Boundary Trust-Region Audit

M273 audits the limiting M183/M170 boundary row discovered by M272.

No PPO, actor update, promotion, or actor-input change was performed.

## Question

M272 promoted `m272b_a0_01025`, but the safe alpha boundary was extremely
narrow. M273 asks what kind of failure appears at the boundary:

- terminal-margin cliff;
- action drift;
- loss of wrong-history sensitivity;
- hidden-state or input-contract artifact.

## Limiting Row

```text
row_id = 16
target = future_braking_deceleration
physical_pair_key = 9530:6:9550:6
source surface = M183/M170
```

Artifact:

```text
runs/m273_m272_boundary_trust_region_audit/row16_alpha_audit.csv
```

## Alpha Boundary

| Policy | Alpha | Normal success | Success drop | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| `m170_split` | source | true | true | 0.004913638 | -0.000097 | 0.005011 |
| `m264_a001` | 0.00000 | true | true | 0.000029941 | -0.005919 | 0.005949 |
| `m272_a010` | 0.01000 | true | true | 0.000001340 | -0.005949 | 0.005950 |
| `m272b_a0_01025` | 0.01025 | true | true | 0.000000636 | -0.005949 | 0.005950 |
| `m272b_a0_0105` | 0.01050 | false | false | -0.000000087 | -0.005950 | 0.005950 |
| `m272_a020` | 0.02000 | false | false | -0.000027190 | -0.005978 | 0.005951 |
| `m272_a500` | 0.50000 | false | false | -0.001398138 | -0.007386 | 0.005987 |
| `m271_10074` | 1.00000 | false | false | -0.002824977 | -0.008850 | 0.006025 |

The estimated zero-margin alpha from the local selected-to-failed segment is:

```text
0.010469864
```

## Action Drift

The flip from pass to fail is not caused by a large first-action change.

| Comparison | First-action L2 |
| --- | ---: |
| `m264_a001` -> `m272b_a0_01025` | 0.000075126 |
| `m272b_a0_01025` -> `m272b_a0_0105` | 0.000001841 |

The row is already almost out of terminal-margin budget at `m264_a001`. M272's
selected alpha keeps it barely alive, while an almost microscopic action change
pushes it into collision.

## Classification

Failure type:

```text
terminal_margin_cliff
```

This is not wrong-history sensitivity loss:

- wrong-history margin remains strongly negative across the boundary;
- margin gap remains positive;
- the failure is normal-history terminal margin crossing zero.

It is also not an actor-input contract issue because no input or observation
profile changed in M272 or M273.

## Design Implication

Another snippet-only actor update is not justified. The M270/M271 direction is
steerable, but the closed-loop trust region is too narrow when old proof rows
have near-zero terminal margin.

The next repair should add a terminal-margin retention layer that directly
penalizes movement of fragile closed-loop rows, especially M183/M170 row16. A
reasonable M274 design is:

```text
source-balanced snippet objective
+ trajectory/action anchor
+ terminal-margin retention for fragile rows
+ lexicographic proof gate before any PPO
```

The retention should not merely anchor first actions. It should explicitly guard
terminal clearance margin for rows with very small positive normal margins.

## Decision

M273 is complete as an audit.

Decision:

```text
design_terminal_margin_retention_before_more_updates
```

Next step:

```text
m274-terminal-margin-retention-design
```

M274 should design and, if scoped tightly, implement the terminal-margin
retention harness before any actor update or PPO continuation.
