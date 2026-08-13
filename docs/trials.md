# Long-task trial record

Use one copy per governed trial and one comparable run without the plugin. Do not record chat transcripts, secrets, or source-file contents.

## Setup

- Date:
- Project and feature:
- Participant/agent configuration:
- Plugin version:
- Spec Kit / Superpowers / bridge versions:
- Governed or baseline run:

## Outcomes

- Recovery time after compaction, crash, or new session:
- Actor state leaks observed:
- Authority changes missed before continuation:
- Work units resumed successfully:
- Manual reconciliation events:

## Evidence and conclusion

- Relevant state paths, commands, and test results:
- Failures or ambiguity:
- Did governance materially improve recovery time or reduce leaks/drift?
- Recommended product change:

Calculate each paired run with the same declared threshold:

```bash
python3 skills/context-governance/scripts/trial_summary.py \
  --baseline 116.522 --baseline 115.979 --baseline 144.616 \
  --governed 66.787 --governed 57.059 --governed 88.413 \
  --threshold-percent 50 \
  --json
```

Keep raw durations and the JSON result with the trial evidence. A `directional_benefit` verdict is not equivalent to meeting the effect threshold.

Recorded trials:

- [2026-08-13 EA Issue #61 / PR #62 paired recovery](trial-records/2026-08-13-ea-pr62-paired.md) — accuracy and isolation passed; recovery-time effect was not demonstrated.
