# Demo Dev

Demo recording workspace for Zici.

## Layout

- `clipwise/` - reusable Clipwise scenario, narration, and instructions.
- `artifacts/` - generated videos, audio, capture metadata, and screenshots. Ignored by Git.
- `backend-artifacts/` - local backend auth/demo state. Ignored by Git.
- `playwright-mcp/` - local browser inspection logs. Ignored by Git.

## Clipwise

```bash
./dev.sh start
npx clipwise record demo-dev/clipwise/scenario.yaml -f mp4 -o ./demo-dev/artifacts
```

The generated recording will be written to `demo-dev/artifacts/`.
