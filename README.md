<div align="center">

[🇬🇧 English](README.md) · [🇪🇸 Español](README.es.md)

</div>

<div align="center">

# 🕯️ death-noticer

**Your containers die at 3 AM. Someone should notice.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-0-00A884?style=flat-square)
![Docker](https://img.shields.io/badge/lives%20in-docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

**Zero dependencies · One file · AI First, human-approved**

</div>

---

You have logs, you have dashboards, you have alerts. And yet, when a container dies at 3 AM, what you actually get is a gray exit code in a terminal nobody is watching.

**death-noticer** is a tiny always-on sidecar that watches the Docker event stream. The instant any container dies, it writes its **obituary**: who it was (name, image), how long it lived, the cause of death (deterministic rules: exit codes, OOM, restart storms), its final words (the last log lines) — and, if you want, an **AI epilogue** from your local agent.

Deploy it once with `docker compose up -d` and every death in your host gets noticed, documented and (optionally) announced.

## ⚡ Quickstart

```bash
git clone https://github.com/fernedy/death-noticer.git
cd death-noticer
docker compose up -d --build
# ...later, a container dies...
ls reports/
# my-api-20260914-030130.md
```

An obituary looks like this:

```markdown
## 🕯️ Obituary — `my-api`

*my-api, beloved service behind `api:1.2`, left us at 2026-09-14 03:01:30
after 0:03:30 of uptime, surviving 3 restart(s).*

**Cause of death:** 🗡️ SIGKILL — kernel OOM killer or docker stop -f timeout
**Final words:** 🧠 memory pressure in logs

```
ERROR: Cannot allocate memory
```

*In lieu of flowers, raise the memory limit.* 🪦
```

Or autopsy a single container on demand:

```bash
python death_noticer.py my-dead-container
```

## 🔔 Announce the deaths

Point it at any webhook and every obituary is posted the moment it is written:

```yaml
command: ["--reports-dir", "/reports",
          "--webhook", "https://discord.com/api/webhooks/XXX/YYY"]
```

Works with Discord (`content`), Slack-compatible (`text`) and generic webhooks — both keys are sent.

## 🤖 AI First, human-approved

- **Deterministic first**: the cause of death comes from a rule engine (9 exit-code meanings, 8 log-pattern clues) — same evidence, same verdict, every time.
- **AI second, opt-in and local**: with `--ai`, your local agent CLI ([opencode](https://opencode.ai)) appends a 3-line epilogue: likely root cause, one command to confirm it, one command to fix it. No API keys, no cloud, nothing leaves your machine.
- **Human in the loop**: death-noticer never restarts, never heals, never touches your containers. It only reads (`inspect`, `logs`, `events`) and writes markdown. You decide what to do.

## 🧰 All the knobs

```bash
python death_noticer.py                      # watch forever, write obituaries to ./reports
python death_noticer.py --reports-dir /r     # custom folder
python death_noticer.py --webhook URL        # post each obituary to Slack/Discord
python death_noticer.py --tail 40            # collect more final words
python death_noticer.py --ai                 # local AI epilogue on every death
python death_noticer.py <container>          # one-off obituary for a container
```

## 🐳 Why it lives in Docker

The noticer itself is a container (`python:3.12-alpine` + Docker CLI) with your docker socket mounted. It sees every death on the host, survives reboots (`restart: unless-stopped`), and it cannot die of the same causes it documents — it runs no workload, holds no state, sends no traffic unless a webhook is configured.

## 🤝 Works great with [container-autopsy](https://github.com/fernedy/container-autopsy)

death-noticer notices the death and writes the short obituary. When you need the full forensic workup — evidence table, contributing findings, shareable badge — run container-autopsy on the same container.

## ✅ Tested

```bash
python -m unittest discover -v
```

The suite mocks Docker entirely — CI runs on Python 3.8, 3.10 and 3.12 with no daemon. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## 🤝 Contributing

Ideas: Kubernetes events flavor, HTML obituary wall, RSS feed of deaths, Grafana annotation on every death. See [CONTRIBUTING.md](CONTRIBUTING.md). Dogfooding rule: **PRs must not lower this repo's [Glow Score](https://github.com/fernedy/repo-glow).**

## 📜 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built AI-first by [Fernedy Arias](https://github.com/fernedy) · Tech Explorer

*If death-noticer caught a 3 AM death for you, drop a ⭐.*

</div>
