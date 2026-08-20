# Pinned handoff compatibility smoke

## Result

The exact baseline passed end to end on 2026-08-20:

- Spec Kit `0.11.1`
- Superpowers `6.0.0`
- speckit-superpowers-bridge `1.1.0`
- Agent Project Governance `0.4.0+codex.20260820091043`

The executable compatibility verifier returned `passed: true` for pinned dependencies, native Bridge readiness, completed handoff, and the complete governance lifecycle. The disposable feature completed all eight authoritative tasks, passed eight tests on Python 3.9.6, cleared final review, closed its actor-owned work unit, and left all 21 Bridge files byte-identical.

No repository was pushed and no production data or external service was modified.

## Defects exposed

1. The verifier accepted only synthetic top-level readiness keys, while Bridge v1.1.0 emits `overall_status` plus component states. The project now consumes the native shape and accepts a pre-feature Bridge warning only when tools, namespace, package files, and agent metadata are independently ready.
2. Bridge v1.1.0 bash lifecycle scripts call GNU `realpath -m`. macOS BSD `realpath` rejected the call. The ready transition was verified in Linux; the host implementation used an audited compatibility command without changing any pinned Bridge file.
3. Superpowers 6.0.0 `task-brief` expects `Task N` headings, while Spec Kit uses `TNNN` checklist rows. The execution used a narrowly scoped derived brief while keeping `tasks.md` authoritative. This limits claims about seamless subagent-driven execution even though the standard Bridge lifecycle passed.
4. Codex CLI `plugin add` garbage-collected older Agent Project Governance cache directories. Both historical cache paths were reconstructed from repository history and their Hook adapter was verified. Local updates must wait for active tasks to end; cachebuster versioning alone does not retain paths.

## Release decision

The fixed-version handoff gate is complete. The later EA forward test met the predeclared original-baseline recovery threshold and passed the drift matrix, making v0.4 eligible for a limited human-reviewed advisory pilot. This handoff trial itself did not measure that SLO.

Machine-readable evidence: [2026-08-20-pinned-handoff-smoke.json](2026-08-20-pinned-handoff-smoke.json).
