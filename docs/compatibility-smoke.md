# Compatibility smoke protocol

Run this protocol in a disposable repository. Installation is intentionally manual and opt-in.

## Verified baseline

1. Install Spec Kit `0.11.1`:

   ```bash
   uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.11.1
   ```

2. Install and enable Superpowers `6.0.0` using its supported Codex distribution.
3. Initialize a Codex Spec Kit project and install bridge `1.1.0` from its pinned release ZIP.
4. Run the bridge readiness command for actor `codex` and retain its JSON result.
5. Produce a minimal spec, plan, and `tasks.md`; perform one bridge handoff and verify the handoff reaches `complete`.
6. Run `project-bootstrap check` and confirm all three dependencies are `verified`.
7. Initialize, checkpoint, bind, resume, evaluate, and close one governance work unit around that handoff.

Save the bridge readiness and handoff results as JSON objects, then run the executable verifier. It requires exact pinned dependency versions and independently exercises checkpoint, bind, strict resume, authority drift, `RECONCILE`, actor isolation, and close:

```bash
python3 skills/project-bootstrap/scripts/compatibility_smoke.py \
  --project-root /path/to/disposable-project \
  --bridge-readiness /path/to/readiness.json \
  --handoff-result /path/to/handoff.json \
  --json
```

Exit `0` means the full evidence gate passed, `1` means a readiness condition is unmet, and `2` means the evidence or invocation is invalid. The verifier never installs dependencies.

## Newer upstream versions

Repeat the complete handoff with exact newer versions. Do not update `compatibility.json` from version detection or readiness alone. Promote a version to `verified` only after the handoff, authority-drift check, session resume, and actor-isolation checks all pass, with evidence recorded in a trial record.
