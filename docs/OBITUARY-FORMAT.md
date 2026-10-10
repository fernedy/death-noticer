# The Obituary Format

Every death gets a markdown file: `<container>-<YYYYmmdd-HHMMSS>.md`, UTC timestamp of when the noticer saw the `die` event.

## Structure

| Section | Content | Source |
|---|---|---|
| Title | 🕯️ Obituary — container name | `docker events` |
| Epitaph | Name, image, time of death, uptime, restart count | `docker inspect` |
| Cause of death | Deterministic verdict | Exit-code table + OOMKilled |
| Final words | The strongest log clue (memory pressure, refused connections, tracebacks, Go panics, health-check failures…) | regex over `docker logs` |
| Log excerpt | Up to 8 last log lines | `docker logs --tail` |
| Attribution | Link back to death-noticer | — |
| 🤖 AI epilogue (optional) | Root cause + confirm + fix commands | local agent CLI, only with `--ai` |

## Cause-of-death table

| Exit code | Verdict |
|---|---|
| 0 | finished its job on purpose |
| 1 | application error |
| 2 | shell/CLI misuse |
| 125 | Docker daemon error |
| 126 | command not executable |
| 127 | command not found |
| 137 | SIGKILL (OOM killer / stop timeout) |
| 139 | segfault |
| 143 | SIGTERM (orchestrated stop) |

`OOMKilled` always takes precedence over the exit code: a container killed by the kernel reports 137, but the flag is unambiguous.

## Webhook payload

Both keys are sent so Discord, Slack-compatible receivers and generic webhooks all work:

```json
{"content": "<first 1900 chars of the obituary>", "text": "<same>"}
```

## Design constraints

- Read-only against the Docker socket: `events`, `inspect`, `logs`. Never start/stop/rm.
- A failing webhook or a missing agent CLI must never crash the noticer — a dead notifier joining the deceased would be embarrassing.
- One file, stdlib only. The obituary must be writable by a host with nothing installed but Docker.
