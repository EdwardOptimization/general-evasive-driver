# Reproduce

The pack materialization command is:

```text
PYTHONPATH=src python -m autodrift.engineering_controller_public_benchmark_pack --output-dir public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505 --milestone m2505-engineering-controller-public-benchmark-pack-materialization-preflight --next-blocker m2506-engineering-controller-public-benchmark-pack-result-audit
```

The pack references committed artifacts rather than rerunning policy actions.
